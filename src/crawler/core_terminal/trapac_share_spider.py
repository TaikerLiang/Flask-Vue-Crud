import dataclasses
from datetime import datetime, timedelta
import time
from typing import Dict, List
from urllib.parse import urlencode

import scrapy
from scrapy import Selector
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import ujson as json

from crawler.core.base_new import (
    DUMMY_URL_DICT,
    RESULT_STATUS_ERROR,
    SEARCH_TYPE_CONTAINER,
)
from crawler.core.exceptions_new import (
    GeneralFatalError,
    SuspiciousOperationError,
    TimeOutError,
)
from crawler.core.items_new import DataNotFoundItem, EndItem
from crawler.core.selenium import ChromeContentGetter
from crawler.core.table import BaseTable, TableExtractor
from crawler.core_terminal.base_spiders_new import BaseMultiTerminalSpider
from crawler.core_terminal.items_new import DebugItem, TerminalItem
from crawler.core_terminal.request_helpers_new import RequestOption
from crawler.core_terminal.rules import BaseRoutingRule, RuleManager
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor


@dataclasses.dataclass
class CompanyInfo:
    lower_short: str
    upper_short: str
    email: str
    password: str


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


@dataclasses.dataclass
class SaveItem:
    file_name: str
    text: str


class CookieHelper:
    @staticmethod
    def get_cookies(response):
        cookies = {}
        for cookie_byte in response.headers.getlist("Set-Cookie"):
            kv = cookie_byte.decode("utf-8").split(";")[0].split("=")
            cookies[kv[0]] = kv[1]

        return cookies

    @staticmethod
    def get_cookie_str(cookies: Dict):
        cookies_str = ""
        for item in cookies:
            cookies_str += f"{item['name']}={item['value']}; "

        return cookies_str


class TrapacShareSpider(BaseMultiTerminalSpider):
    name = ""
    company_info = CompanyInfo(
        lower_short="",
        upper_short="",
        email="",
        password="",
    )

    def __init__(self, *args, **kwargs):
        super(TrapacShareSpider, self).__init__(*args, **kwargs)

        rules = [MainRoutingRule(), ContentRoutingRule()]

        self._rule_manager = RuleManager(rules=rules)
        self._save = True if "save" in kwargs else False

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = MainRoutingRule.build_request_option(
            container_nos=unique_container_nos, cno_tid_map=self.cno_tid_map, company_info=self.company_info
        )
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem):
                c_no = result["container_no"]
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result["task_id"] = t_id
                    yield result
                    yield EndItem(task_id=t_id)
            elif isinstance(result, DataNotFoundItem):
                c_no = result["search_no"]
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result["task_id"] = t_id
                    yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            elif isinstance(result, SaveItem) and self._save:
                self._saver.save(to=result.file_name, text=result.text)

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )

        elif option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method="POST",
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
            )

        else:
            map_dict = {search_no: self.cno_tid_map[search_no] for search_no in option.meta["search_nos"]}
            raise SuspiciousOperationError(
                task_id=self.cno_tid_map[option.meta["search_nos"][0]][0],
                search_type=self.search_type,
                reason=f"Unexpected request method: `{option.method}`, on (search_no: [task_id...]): {map_dict}",
            )


class MainRoutingRule(BaseRoutingRule):
    name = "MAIN"

    @classmethod
    def build_request_option(cls, container_nos: List, cno_tid_map: Dict, company_info: CompanyInfo) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={
                "company_info": company_info,
                "search_nos": container_nos,
                "cno_tid_map": cno_tid_map,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        company_info = response.meta["company_info"]
        container_nos = response.meta["search_nos"]
        cno_tid_map = response.meta["cno_tid_map"]

        is_g_captcha, res, cookies = self._build_container_response(
            company_info=company_info,
            container_nos=container_nos,
            cno_tid_map=cno_tid_map,
        )
        if is_g_captcha:
            yield ContentRoutingRule.build_request_option(
                container_nos=container_nos,
                cno_tid_map=cno_tid_map,
                company_info=company_info,
                g_token=res,
                cookies=cookies,
            )
        else:
            for item in self.handle_response(response=res, container_nos=container_nos):
                yield item

    def handle_response(self, response, container_nos):
        container_response = scrapy.Selector(text=response)
        yield SaveItem(file_name="container.html", text=container_response.get())

        for container_info in self._extract_container_result_table(
            response=container_response, numbers=len(container_nos)
        ):
            container_no = container_info["container_no"]
            container_nos.remove(container_no)

            yield TerminalItem(  # html field
                container_no=container_no,  # number
                last_free_day=container_info["last_free_day"],  # demurrage-lfd
                customs_release=container_info.get("custom_release"),  # holds-customs
                demurrage=container_info["demurrage"],  # demurrage-amt
                container_spec=container_info["container_spec"],  # dimensions
                holds=container_info["holds"],  # demurrage-hold
                cy_location=container_info["cy_location"],  # yard status
                vessel=container_info["vessel"],  # vsl / voy
                voyage=container_info["voyage"],  # vsl / voy
            )

        for container_no in container_nos:
            yield DataNotFoundItem(
                search_no=container_no,
                search_type=SEARCH_TYPE_CONTAINER,
                detail="Data was not found",
                status=RESULT_STATUS_ERROR,
            )

    def _extract_container_result_table(self, response: scrapy.Selector, numbers: int):
        table = response.css('div[class="transaction-result availability"] table')

        table_locator = ContainerTableLocator()
        table_locator.parse(table=table, numbers=numbers)
        table_extractor = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_header():
            if not table_extractor.extract_cell(top="Number", left=left):
                continue

            vessel, voyage = table_extractor.extract_cell(
                top="Vsl / Voy", left=left, extractor=VesselVoyageTdExtractor()
            )
            yield {
                "container_no": table_extractor.extract_cell(top="Number", left=left),
                "carrier": table_extractor.extract_cell(top="Holds_Line", left=left),
                "custom_release": table_extractor.extract_cell(top="Holds_Customs", left=left),
                "cy_location": table_extractor.extract_cell(top="Yard Status", left=left),
                "last_free_day": table_extractor.extract_cell(top="Demurrage_LFD", left=left),
                "holds": table_extractor.extract_cell(top="Demurrage_Hold", left=left),
                "demurrage": table_extractor.extract_cell(top="Demurrage_Amt", left=left),
                "container_spec": table_extractor.extract_cell(top="Dimensions", left=left),
                "vessel": vessel,
                "voyage": voyage,
            }

    def _build_container_response(self, company_info: CompanyInfo, container_nos: List, cno_tid_map: Dict):
        content_getter = ContentGetter(proxy_manager=None, is_headless=True, company_info=company_info)
        try:
            is_g_captcha, res, cookies = content_getter.get_content(container_no_list=container_nos)
        except TimeOutError as e:
            map_dict = {search_no: cno_tid_map[search_no] for search_no in container_nos}
            raise TimeOutError(
                task_id=cno_tid_map[container_nos[0]][0],
                search_type=SEARCH_TYPE_CONTAINER,
                reason=f"{e.reason} on (search_no: [task_id...]): {map_dict}",
            )
        finally:
            content_getter.quit()

        return is_g_captcha, res, cookies

    def _is_search_no_invalid(self, response: scrapy.Selector) -> bool:
        return bool(response.css("tr.error-row"))


class ContentRoutingRule(BaseRoutingRule):
    name = "CONTENT"

    @classmethod
    def build_request_option(
        cls, container_nos: List, cno_tid_map: Dict, company_info: CompanyInfo, g_token: str, cookies: Dict
    ) -> RequestOption:
        form_data = {
            "action": "trapac_transaction",
            "recaptcha-token": g_token,
            "terminal": company_info.upper_short,
            "transaction": "availability",
            "containers": ",".join(container_nos),
            "booking": "",
            "email": "",
            "equipment_type": "CT",
            "history_type": "N",
            "services": "",
            "from_date": str(datetime.now().date()),
            "to_date": str((datetime.now() + timedelta(days=30)).date()),
        }

        headers = {
            "authority": f"{company_info.lower_short}.trapac.com",
            "sec-ch-ua": '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            "accept": "application/json, text/javascript, */*; q=0.01",
            "x-requested-with": "XMLHttpRequest",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": f"https://{company_info.lower_short}.trapac.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://{company_info.lower_short}.trapac.com/quick-check/?terminal={company_info.upper_short}&transaction=availability",
            "accept-language": "en-US,en;q=0.9",
            "cookie": CookieHelper.get_cookie_str(cookies),
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f"https://{company_info.lower_short}.trapac.com/wp-admin/admin-ajax.php",
            headers=headers,
            body=urlencode(query=form_data),
            meta={
                "search_nos": container_nos,
                "cno_tid_map": cno_tid_map,
            },
        )

    def handle(self, response):
        container_nos = response.meta["search_nos"]
        cno_tid_map = response.meta["cno_tid_map"]
        numbers = len(container_nos)

        resp = json.loads(response.text)

        if "Please complete the reCAPTCHA check and submit your request again" in resp["html"]:
            map_dict = {search_no: cno_tid_map[search_no] for search_no in container_nos}
            raise GeneralFatalError(
                task_id=cno_tid_map[container_nos[0]][0],
                search_type=SEARCH_TYPE_CONTAINER,
                reason=f"reCAPTCHA check encountered on (search_no: [task_id...]): {map_dict}",
            )

        resp_html = Selector(text=resp["html"])
        table = resp_html.css('div[class="transaction-result availability"] table')
        table_locator = ContainerTableLocator()
        table_locator.parse(table=table, numbers=numbers)
        table_extractor = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_header():
            vessel, voyage = table_extractor.extract_cell(
                top="Vsl / Voy", left=left, extractor=VesselVoyageTdExtractor()
            )
            yield TerminalItem(
                container_no=table_extractor.extract_cell(top="Number", left=left),
                customs_release=table_extractor.extract_cell(top="Holds_Customs", left=left),
                gate_out_date=table_extractor.extract_cell(top="Yard Status", left=left),
                last_free_day=table_extractor.extract_cell(top="Demurrage_LFD", left=left),
                holds=table_extractor.extract_cell(top="Demurrage_Hold", left=left),
                demurrage=table_extractor.extract_cell(top="Demurrage_Amt", left=left),
                container_spec=table_extractor.extract_cell(top="Dimensions", left=left),
                vessel=vessel,
                voyage=voyage,
            )


# ------------------------------------------------------------------------
class ContentGetter(ChromeContentGetter):
    def __init__(self, proxy_manager, is_headless, company_info: CompanyInfo):
        super().__init__(proxy_manager=proxy_manager, is_headless=is_headless)
        self._company = company_info

    def get_content(self, container_no_list):
        self._driver.get("https://www.trapac.com/")
        time.sleep(10)
        self._accept_cookie()

        link_pathes = {
            "LAX": "/html/body/div[1]/div/div/div[1]/ul/li[2]/a",
            "OAK": "/html/body/div[1]/div/div/div[1]/ul/li[2]/a",
            "OTHERS": "/html/body/div[1]/div/div/div[1]/ul/li[4]/a",
        }
        link_path = link_pathes.get(self._company.upper_short, link_pathes["OTHERS"])
        link = self._driver.find_element_by_xpath(link_path)
        ActionChains(self._driver).move_to_element(link).click().perform()
        time.sleep(10)

        menu_pathes = {
            "LAX": '//*[@id="menu-item-74"]/a',
            "OAK": '//*[@id="menu-item-245"]/a',
            "OTHERS": '//*[@id="menu-item-248"]/a',
        }
        menu_path = menu_pathes.get(self._company.upper_short, menu_pathes["OTHERS"])
        menu = self._driver.find_element_by_xpath(menu_path)
        ActionChains(self._driver).move_to_element(menu).click().perform()
        time.sleep(3)

        self._driver.get(
            f"https://{self._company.lower_short}.trapac.com/quick-check/?terminal={self._company.upper_short}&transaction=availability"
        )
        time.sleep(15)

        self._human_action()
        time.sleep(3)
        self._key_in_search_bar(search_no="\n".join(container_no_list))
        self._press_search_button()
        cookies = self.get_cookies()
        self._accept_cookie()

        return False, self._get_result_response_text(), cookies

    def _accept_cookie(self):
        try:
            cookie_btn = self._driver.find_element_by_xpath('//*[@id="cn-accept-cookie"]')
            cookie_btn.click()
            time.sleep(3)
        except Exception:
            pass

    def _key_in_search_bar(self, search_no: str):
        text_area = self._driver.find_element_by_xpath('//*[@id="edit-containers"]')
        text_area.send_keys(search_no)
        time.sleep(3)

    def _press_search_button(self):
        search_btn = self._driver.find_element_by_xpath('//*[@id="transaction-form"]/div[3]/button')
        search_btn.click()
        time.sleep(10)

    def _get_google_recaptcha(self):
        try:
            element = self._driver.find_element_by_xpath('//*[@id="recaptcha-backup"]')
            return element
        except NoSuchElementException:
            return None

    def get_proxy_username(self, option: ProxyOption) -> str:
        return f"groups-{option.group},session-{option.session}"

    def _get_result_response_text(self):
        result_table_css = "div#transaction-detail-result table"

        self._wait_for_appear(css=result_table_css, wait_sec=30)
        return self._driver.page_source

    def _wait_for_appear(self, css: str, wait_sec: int):
        locator = (By.CSS_SELECTOR, css)
        try:
            WebDriverWait(self._driver, wait_sec).until(EC.presence_of_element_located(locator))
        except TimeoutException:
            current_url = self.get_current_url()
            self._driver.quit()
            raise TimeOutError(reason=current_url)

    def _save_screenshot(self):
        self._driver.save_screenshot("screenshot.png")

    def _human_action(self):
        try:
            self._driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[2]/label').click()
            time.sleep(1)
            self._driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[1]/label').click()
            time.sleep(1)
            self._driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[3]/label').click()
            time.sleep(1)
        except:  # noqa: E722
            pass

        element_pathes = {
            "LAX": '//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[1]/label',
            "OAK": '//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[2]/label',
            "OTHERS": '//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[3]/label',
        }
        element_path = element_pathes.get(self._company.upper_short, element_pathes["OTHERS"])
        self._driver.find_element_by_xpath(element_path).click()
        time.sleep(1)


class VesselVoyageTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        vessel_voyage = cell.css("::text").get()
        vessel, voyage = "", ""
        if vessel_voyage:
            vessel, voyage = vessel_voyage.split("/")
        return vessel, voyage


class ContainerTableLocator(BaseTable):
    TR_MAIN_TITLE_CLASS = "th-main"
    TR_SECOND_TITLE_CLASS = "th-second"

    def parse(self, table: Selector, numbers: int = 1):
        main_title_tr = table.css(f"tr.{self.TR_MAIN_TITLE_CLASS}")
        second_title_tr = table.css(f"tr.{self.TR_SECOND_TITLE_CLASS}")
        data_trs = table.css("tbody tr.row-odd")

        main_title_ths = main_title_tr.css("th")
        second_title_ths = second_title_tr.css("th")
        title_list = self._combine_title_list(main_title_ths=main_title_ths, second_title_ths=second_title_ths)

        for index, data_tr in enumerate(data_trs):
            data_tds = data_tr.css("td")

            # not sure if this is needed
            if len(data_tds) < len(title_list):
                for title in title_list:
                    self._td_map.setdefault(title, [])
                    self._td_map[title].append(Selector(text="<p></p>"))
                continue

            self._left_header_set.add(index)
            for title, data_td in zip(title_list, data_tds):
                self._td_map.setdefault(title, [])
                self._td_map[title].append(data_td)

    def _combine_title_list(self, main_title_ths: List[scrapy.Selector], second_title_ths: List[scrapy.Selector]):
        main_title_list = []
        main_title_accumulated_col_span = []  # [(main_title, accumulated_col_span)]

        accumulated_col_span = 0
        for main_title_th in main_title_ths:
            main_title = "".join(main_title_th.css("::text").getall())
            col_span = main_title_th.css("::attr(colspan)").get()
            col_span = int(col_span) if col_span else 1

            accumulated_col_span += col_span
            main_title_list.append(main_title)
            main_title_accumulated_col_span.append((main_title, accumulated_col_span))

        title_list = []
        main_title_index = 0
        main_title, accumulated_col_span = main_title_accumulated_col_span[main_title_index]
        for second_title_index, second_title_th in enumerate(second_title_ths):
            second_title = second_title_th.css("::text").get()

            if second_title in ["Size"]:
                second_title = None
            elif second_title in ["Type", "Height"]:
                continue

            if second_title_index >= accumulated_col_span:
                main_title_index += 1
                main_title, accumulated_col_span = main_title_accumulated_col_span[main_title_index]

            if second_title:
                title_list.append(f"{main_title}_{second_title}")
            else:
                title_list.append(main_title)

        return title_list

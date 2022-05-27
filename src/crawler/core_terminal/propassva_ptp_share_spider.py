import dataclasses
import json
import time
from typing import List
from urllib.parse import unquote

import scrapy
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core.selenium import ChromeContentGetter
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, ExportErrorData, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import BaseRoutingRule, RuleManager
from crawler.services.captcha_service import GoogleRecaptchaV2Service

BASE_URL = "https://{}.emodal.com/"  # propassva or porttruckpass
MAX_PAGE_NUM = 20


@dataclasses.dataclass
class CompanyInfo:
    site_name: str
    username: str
    password: str


class PropassvaPtpShareSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = ""
    company_info = CompanyInfo(
        site_name="",
        username="",
        password="",
    )
    custom_settings = {
        **BaseMultiTerminalSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            AddContainerRoutingRule(),
            GetContainerNoRoutingRule(),
            RemoveContainerNoRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = LoginRoutingRule.build_request_option(
            container_no_list=unique_container_nos, company_info=self.company_info
        )
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, (TerminalItem, ExportErrorData)):
                c_no = result["container_no"]
                t_ids = self.cno_tid_map.get(c_no)
                if t_ids:
                    for t_id in t_ids:
                        result["task_id"] = t_id
                        yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                method=RequestOption.METHOD_GET,
                url=option.url,
                headers=option.headers,
                meta=meta,
                cookies=option.cookies,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method="POST",
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        elif option.method in ["DELETE", "PUT"]:
            return scrapy.Request(
                method=option.method,
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------
class LoginRoutingRule(BaseRoutingRule):
    name = "Login"

    @classmethod
    def build_request_option(cls, container_no_list: List[str], company_info: CompanyInfo) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={
                "container_no_list": container_no_list,
                "company_info": company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        browser = ContentGetter(proxy_manager=None, is_headless=True)
        browser.login(response.meta["company_info"])
        cookies = browser.get_cookies_dict()
        auth_dict = json.loads(unquote(cookies["AuthCookie"]))
        auth = f"Bearer {auth_dict['bearer']}"
        browser.close()

        yield AddContainerRoutingRule.build_request_option(container_no_list=container_no_list, auth=auth)


# -------------------------------------------------------------------------------
class AddContainerRoutingRule(BaseRoutingRule):
    name = "Add_Container"

    @classmethod
    def build_request_option(cls, container_no_list: List, auth: str) -> RequestOption:
        url = "https://datahub.visibility.emodal.com/datahub/container/AddContainers"
        form_data = {
            "containerNumbers": container_no_list[:MAX_PAGE_NUM],
            "tradeType": "I",
            "portCd": "",
            "IsselectedallTradetypes": False,
            "tags": None,
        }
        return RequestOption(
            rule_name=cls.name,
            method="PUT",
            url=url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/87.0.4280.141 Safari/537.36"
                ),
                "Accept-Language": "zh-TW,zh;q=0.9",
                "Authorization": auth,
                "Content-Type": "application/json",
            },
            body=json.dumps(form_data),
            meta={
                "container_no_list": container_no_list,
                "auth": auth,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        auth = response.meta["auth"]
        yield GetContainerNoRoutingRule.build_request_option(container_no_list=container_no_list, auth=auth)


# -------------------------------------------------------------------------------


class GetContainerNoRoutingRule(BaseRoutingRule):
    name = "Get_Container_No"

    @classmethod
    def build_request_option(cls, container_no_list: List, auth: str) -> RequestOption:
        url = "https://datahub.visibility.emodal.com/datahub/container/accesslist"
        form_data = {
            "queryContinuationToken": "",
            "pageSize": 30,
            "Page": 0,
            "conditions": [
                {
                    "mem": "unit_nbr",
                    "include": True,
                    "oper": 10,
                    "vLow": ",".join(container_no_list[:MAX_PAGE_NUM]),
                    "vHigh": "",
                },
                {
                    "mem": "viewtype_desc",
                    "include": True,
                    "oper": 10,
                    "required": True,
                    "vLow": "U",
                    "vHigh": [],
                    "seprator": "AND",
                },
            ],
            "ordering": [],
        }
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/87.0.4280.141 Safari/537.36"
                ),
                "Accept-Language": "zh-TW,zh;q=0.9",
                "Authorization": auth,
                "Content-Type": "application/json",
            },
            body=json.dumps(form_data),
            meta={
                "container_no_list": container_no_list,
                "auth": auth,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        auth = response.meta["auth"]

        search_container_nos = container_no_list[:MAX_PAGE_NUM]

        response_dict = json.loads(response.text)
        remove_containers = []
        remove_ids = []
        for container in response_dict["data"]:
            if (container["unit_nbr"] in search_container_nos) and (container["id"] is not None):
                vessel_info = self._extract_vessel_info(container)
                release_info = self._extract_release_info(container)
                yield TerminalItem(
                    container_no=container["unit_nbr"],
                    available=self._extract_available_time(container),
                    last_free_day=container["lastfree_dttm"],
                    gate_out_date=self._extract_gate_out_date(container),
                    demurrage=self._extract_demurrage_info(container),
                    customs_release=release_info["CUSTOMS"],
                    freight_release=release_info["FREIGHT"],
                    carrier=(container["unitinfo"] or dict()).get("ownerline_scac", ""),
                    container_spec=(container["unitinfo"] or dict()).get("unitsztype_cd", ""),
                    vessel=vessel_info["vessel"],
                    voyage=vessel_info["voyage"],
                )
                search_container_nos.remove(container["unit_nbr"])
            remove_containers.append(container["unit_nbr"])
            remove_ids.append(container["id"] or "")

        for container_no in search_container_nos:
            yield ExportErrorData(
                container_no=container_no,
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )

        yield RemoveContainerNoRoutingRule.build_request_option(container_no_list, remove_containers, remove_ids, auth)

    def _extract_release_info(self, container_dict):
        release_info = {
            "CUSTOMS": None,
            "FREIGHT": None,
        }
        for status in container_dict["shipmentstatus"]:
            for hold in status["holdsinfo"]:
                release_info[hold["type"]] = hold["status"]
        return release_info

    def _extract_gate_out_date(self, container_dict):
        activity_list = container_dict["drayunitactivity"]
        for activity in activity_list:
            if activity["event_desc"] == "Departed Terminal":
                return activity["event_dttm"]
        return None

    def _extract_demurrage_info(self, container_dict):
        demurrage_list = container_dict["confeeinfo"]
        for demurrage in demurrage_list:
            if demurrage["feestatus_dsc"] == "Paid":
                return demurrage["feepaid"]
        return None

    def _extract_vessel_info(self, container):
        locations = container["locations"]
        location_info = None
        if len(locations) > 0:
            location_info = locations[0]["locationinfo"]

        if location_info:
            arrive_info = location_info["arrivalinfo"]
            if arrive_info and arrive_info["vesselinfo"]:
                return {
                    "vessel": arrive_info["vesselinfo"].get("vessel_nm"),
                    "voyage": arrive_info["vesselinfo"].get("voyage_nbr"),
                }

        return {
            "vessel": None,
            "voyage": None,
        }

    def _extract_available_time(self, container_dict):
        activity_list = container_dict["drayunitactivity"]
        for activity in activity_list:
            if activity["event_desc"] == "Ready for pick up":
                return activity["event_dttm"]

        return None


# -------------------------------------------------------------------------------


class RemoveContainerNoRoutingRule(BaseRoutingRule):
    name = "Remove_Container_No"

    @classmethod
    def build_request_option(
        cls, container_no_list: List, remove_containers: List, remove_ids: List, auth: str
    ) -> RequestOption:
        url = "https://datahub.visibility.emodal.com/datahub/container/accesslist"
        form_data = {"containernbrs": ",".join(remove_containers), "drayunituids": ",".join(remove_ids)}
        return RequestOption(
            rule_name=cls.name,
            method="DELETE",
            url=url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/87.0.4280.141 Safari/537.36"
                ),
                "Accept-Language": "zh-TW,zh;q=0.9",
                "Authorization": auth,
                "Content-Type": "application/json",
            },
            body=json.dumps(form_data),
            meta={
                "container_no_list": container_no_list,
                "auth": auth,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        auth = response.meta["auth"]
        yield NextRoundRoutingRule.build_request_option(container_no_list, auth)


# --------------------------------------------------------------------


class NextRoundRoutingRule(BaseRoutingRule):
    @classmethod
    def build_request_option(cls, container_no_list: List, auth: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={"container_no_list": container_no_list, "auth": auth},
        )

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        auth = response.meta["auth"]

        if len(container_no_list) <= MAX_PAGE_NUM:
            return

        container_no_list = container_no_list[MAX_PAGE_NUM:]

        yield AddContainerRoutingRule.build_request_option(container_no_list=container_no_list, auth=auth)


# -------------------------------------------------------------------------------


class ContentGetter(ChromeContentGetter):
    def login(self, company_info: CompanyInfo):
        g_captcha_solver = GoogleRecaptchaV2Service()
        self._driver.get(BASE_URL.format(company_info.site_name))
        WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="Username"]')))
        site_key = "6LcYbVYUAAAAAOTBbXHZFvXBLYugYI5-sqQKlqsA"
        g_url = self.get_current_url()
        token = g_captcha_solver.solve(g_url, site_key)
        self._driver.find_element(By.XPATH, '//*[@id="Username"]').send_keys(company_info.username)
        time.sleep(1)
        self._driver.find_element(By.XPATH, '//*[@id="Password"]').send_keys(company_info.password)
        time.sleep(1)
        self.execute_recaptcha_callback_fun(token=token)
        self._driver.save_screenshot("before_login.png")
        login_btn = WebDriverWait(self._driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btnLogin"]')))
        login_btn.click()
        time.sleep(10)
        self._driver.save_screenshot("after_login.png")

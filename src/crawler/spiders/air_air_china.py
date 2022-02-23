from typing import List, Dict
import io

from scrapy import Request, FormRequest, Selector
from python_anticaptcha import AnticaptchaClient, ImageToTextTask, AnticaptchaException

from crawler.core.table import BaseTable, TableExtractor
from crawler.core_air.base_spiders import BaseMultiAirSpider
from crawler.core_air.items import DebugItem, BaseAirItem, AirItem, ExportErrorData, FlightItem, HistoryItem
from crawler.core_air.base import AIR_RESULT_STATUS_ERROR
from crawler.core_air.exceptions import AntiCaptchaError
from crawler.core_air.rules import RuleManager, BaseRoutingRule, RequestOption

BASE_URL = "https://www.airchinacargo.com"


class AirAirChinaSpider(BaseMultiAirSpider):
    mawb_prefix = "999"
    name = "air_air_china"

    def __init__(self, *args, **kwargs):
        super(AirAirChinaSpider, self).__init__(*args, **kwargs)

        rules = [
            HomePageRoutingRule(),
            CaptchaRoutingRule(),
            SearchRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        for m_no, t_id in zip(self.mawb_nos, self.task_ids):
            option = HomePageRoutingRule.build_request_option(mawb_no=m_no, task_id=t_id)
            yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        if routing_rule.name != CaptchaRoutingRule.name:
            save_name = routing_rule.get_save_name(response=response)
            self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseAirItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_AIR_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return FormRequest(
                url=option.url,
                formdata=option.form_data,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_BODY:
            return FormRequest(
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


# -------------------------------------------------------------------------------


class HomePageRoutingRule(BaseRoutingRule):
    name = "HOMEPAGE"

    @classmethod
    def build_request_option(cls, mawb_no: str, task_id: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f"{BASE_URL}/en/index.php?section=0-0149-0154",
            meta={
                "mawb_no": mawb_no,
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        mawb_no = response.meta["mawb_no"]
        task_id = response.meta["task_id"]

        yield CaptchaRoutingRule.build_request_option(mawb_no=mawb_no, task_id=task_id)


class CaptchaRoutingRule(BaseRoutingRule):
    name = "CAPTCHA"

    @classmethod
    def build_request_option(cls, mawb_no: str, task_id: str) -> RequestOption:
        headers = {
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/avif,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.9"
            ),
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Host": "www.airchinacargo.com",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=f"{BASE_URL}/en/yz.php",
            headers=headers,
            meta={
                "mawb_no": mawb_no,
                "headers": headers,
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        pass

    def handle(self, response):
        mawb_no = response.meta["mawb_no"]
        headers = response.meta["headers"]
        task_id = response.meta["task_id"]

        captcha = self._get_captcha(response.body)

        yield SearchRoutingRule.build_request_option(
            mawb_no=mawb_no,
            task_id=task_id,
            headers=headers,
            captcha=captcha,
        )

    @staticmethod
    def _get_captcha(captcha_code):
        try:
            api_key = "fbe73f747afc996b624e8d2a95fa0f84"
            captcha_fp = io.BytesIO(captcha_code)
            client = AnticaptchaClient(api_key)
            task = ImageToTextTask(captcha_fp)
            job = client.createTask(task)
            job.join()
            return job.get_captcha_text()
        except AnticaptchaException:
            raise AntiCaptchaError()


class SearchRoutingRule(BaseRoutingRule):
    name = "SEARCH"

    @classmethod
    def build_request_option(cls, mawb_no: str, task_id: str, headers, captcha) -> RequestOption:
        url = f"{BASE_URL}/en/search_order.php"
        form_data = {
            "orders0": mawb_no,
            "orders1": "Please enter the 8 digits",
            "orders2": "Please enter the 8 digits",
            "orders3": "Please enter the 8 digits",
            "orders4": "Please enter the 8 digits",
            "orders10": "999",
            "orders11": "999",
            "orders12": "999",
            "orders13": "999",
            "orders14": "999",
            "section": "0-0149-0154-0174",
            "x": "49",
            "y": "11",
            "usercheckcode": captcha,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            headers=headers,
            url=url,
            form_data=form_data,
            meta={
                "mawb_no": mawb_no,
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        mawb_no = response.meta["mawb_no"]
        task_id = response.meta["task_id"]

        if self._is_mawb_no_invalid(response):
            yield ExportErrorData(
                task_id=task_id,
                mawb_no=mawb_no,
                status=AIR_RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
            return

        air_info = self._extract_air_info(response)
        yield AirItem(task_id=task_id, mawb=mawb_no, **air_info)

        history_info_list = self._extract_history_info(response)
        for history_info in history_info_list:
            yield HistoryItem(task_id=task_id, **history_info)

        flight_info_list = self._build_flight_info_list(history_info_list, air_info)
        for flight_info in flight_info_list:
            yield FlightItem(task_id=task_id, **flight_info)

    @staticmethod
    def _is_mawb_no_invalid(response: Selector) -> bool:
        return len(response.css("#tbtrackingmaintitle td")) < 4

    @staticmethod
    def _extract_air_info(response: Selector) -> Dict:
        tds = [td.get().strip() for td in response.css("#tbtrackingmaintitle td ::text")]
        pieces = response.css("#tableCargo div.pcs ::text").get().strip()
        weight = response.css("#tableCargo div.weight ::text").get().strip()
        current_state = response.css("#tableCargo span ::text").get().strip()

        return {
            "origin": tds[3],
            "destination": tds[5],
            "pieces": pieces,
            "weight": weight,
            "current_state": current_state,
        }

    @staticmethod
    def _extract_history_info(response: Selector) -> List:
        table = response.css("table#tbcargostatus")[1]
        table_locator = CargoDetailsTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        history_info_list = []
        for left in table_locator.iter_left_header():
            history_info_list.append(
                {
                    "status": table_extractor.extract_cell(top="Status", left=left).strip(),
                    "flight_number": table_extractor.extract_cell(top="Flight Info", left=left).strip(),
                    "location": table_extractor.extract_cell(top="Operation Airport", left=left).strip(),
                    "pieces": table_extractor.extract_cell(top="Pieces", left=left).strip(),
                    "weight": table_extractor.extract_cell(top="Weight(kg)", left=left).strip(),
                    "time": table_extractor.extract_cell(top="Operational time", left=left).strip(),
                }
            )
        return history_info_list

    def _build_flight_info_list(self, history_info_list: List, air_info: Dict) -> List:
        origin = air_info["origin"]
        destination = air_info["destination"]

        is_dep_first, is_rcf_first = True, True

        flight_info_list = []
        for history_info in history_info_list:
            if (
                self._is_departure(status=history_info["status"], location=history_info["location"], origin=origin)
                and is_dep_first
            ):
                is_dep_first = False
                flight_info_list.append(
                    {
                        "flight_number": history_info["flight_number"],
                        "origin": origin,
                        "destination": destination,
                        "pieces": history_info["pieces"],
                        "weight": history_info["weight"],
                        "atd": history_info["time"],
                        "ata": None,
                    }
                )
                continue

            if (
                self._is_arrival(
                    status=history_info["status"], location=history_info["location"], destination=destination
                )
                and is_rcf_first
            ):
                is_rcf_first = False
                flight_info_list.append(
                    {
                        "flight_number": history_info["flight_number"],
                        "origin": origin,
                        "destination": destination,
                        "pieces": history_info["pieces"],
                        "weight": history_info["weight"],
                        "atd": None,
                        "ata": history_info["time"],
                    }
                )

        return flight_info_list

    @staticmethod
    def _is_departure(status, location, origin):
        return status.startswith("DEP") and location.startswith(origin)

    @staticmethod
    def _is_arrival(status, location, destination):
        return status.startswith("RCF") and location.startswith(destination)


class CargoDetailsTableLocator(BaseTable):
    def parse(self, table: Selector):
        header_ths = table.css("th")
        headers = [header_th.css("::text").get().strip() for header_th in header_ths]
        trs = table.css("tbody tr")

        for index, tr in enumerate(trs):
            tds = tr.css("td")
            self._left_header_set.add(index)
            for header, td in zip(headers, tds):
                self._td_map.setdefault(header, [])
                self._td_map[header].append(td)

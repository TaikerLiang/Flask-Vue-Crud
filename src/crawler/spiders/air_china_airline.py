from typing import List, Dict

from scrapy import Request, FormRequest, Selector

from crawler.core.table import BaseTable, TableExtractor
from crawler.core_air.base_spiders import BaseMultiAirSpider
from crawler.core_air.items import DebugItem, BaseAirItem, AirItem, ExportErrorData, FlightItem
from crawler.core_air.base import AIR_RESULT_STATUS_ERROR
from crawler.core_air.rules import RuleManager, BaseRoutingRule, RequestOption


class AirChinaAirlineSpider(BaseMultiAirSpider):
    awb_prefix = "297"
    name = "air_china_airline"

    def __init__(self, *args, **kwargs):
        super(AirChinaAirlineSpider, self).__init__(*args, **kwargs)

        rules = [
            HomePageRoutingRule(),
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
            url="https://cargo.china-airlines.com/ccnetv2/content/manage/ShipmentTracking.aspx",
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

        hidden_form = self._extract_hidden_form(response)

        yield SearchRoutingRule.build_request_option(mawb_no=mawb_no, task_id=task_id, hidden_form=hidden_form)

    @staticmethod
    def _extract_hidden_form(response: Selector) -> Dict:
        view_state = response.css("input#__VIEWSTATE::attr(value)").get()
        view_state_generator = response.css("input#__VIEWSTATEGENERATOR::attr(value)").get()

        return {
            "view_state": view_state,
            "view_state_generator": view_state_generator,
        }


class SearchRoutingRule(BaseRoutingRule):
    name = "SEARCH"

    @classmethod
    def build_request_option(cls, mawb_no: str, task_id: str, hidden_form: Dict) -> RequestOption:
        url = "https://cargo.china-airlines.com/ccnetv2/content/manage/ShipmentTracking.aspx"
        form_data = {
            "__EVENTARGUMENT": "",
            "__EVENTTARGET": "",
            "__VIEWSTATE": hidden_form["view_state"],
            "__VIEWSTATEGENERATOR": hidden_form["view_state_generator"],
            "__SCROLLPOSITIONX": "0",
            "__SCROLLPOSITIONY": "307",
            "sWord": "",
            "ctl00$txtCompanyId": "",
            "ctl00$txtUserId": "",
            "ctl00$txtPassword": "",
            "ctl00$ContentPlaceHolder1$txtAwbPfx": AirChinaAirlineSpider.awb_prefix,
            "ctl00$ContentPlaceHolder1$txtAwbNum": mawb_no,
            "ctl00$ContentPlaceHolder1$btnSearch": "查詢",
            "ctl00$hdnLogPath": "/ccnetv2/content/home/addLog.ashx",
            "ctl00$hdnProgName": "/ccnetv2/content/manage/shipmenttracking.aspx",
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
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
        flight_info_list = self._extract_flight_info(response)

        yield AirItem(task_id=task_id, mawb=mawb_no, **air_info)

        for flight_info in flight_info_list:
            yield FlightItem(task_id=task_id, **flight_info)

    @staticmethod
    def _is_mawb_no_invalid(response: Selector) -> bool:
        return not bool(response.css("div#ContentPlaceHolder1_div_FI"))

    @staticmethod
    def _extract_air_info(response: Selector) -> Dict:
        origin = response.css("#ContentPlaceHolder1_lblOrg ::text").get().strip()
        destination = response.css("#ContentPlaceHolder1_lblDes ::text").get().strip()
        pieces = response.css("#ContentPlaceHolder1_lblPcs ::text").get().strip()
        weight = response.css("#ContentPlaceHolder1_lblWgt ::text").get().strip()
        current_state = response.css("#ContentPlaceHolder1_lblLatestFreightStatus ::text").get().strip()

        return {
            "origin": origin,
            "destination": destination,
            "pieces": pieces,
            "weight": weight,
            "current_state": current_state,
        }

    @staticmethod
    def _extract_flight_info(response: Selector) -> List:
        table = response.css("div#ContentPlaceHolder1_div_FI table")
        table_locator = FlightInfoTableLocator()
        table_locator.parse(table=table)

        table_extractor = TableExtractor(table_locator=table_locator)
        flight_info_list = []
        for left in table_locator.iter_left_header():
            origin, atd = table_extractor.extract_cell(top="Departure", left=left).strip().split(maxsplit=1)
            destination, ata = table_extractor.extract_cell(top="Arrival", left=left).strip().split(maxsplit=1)

            flight_info_list.append(
                {
                    "flight_number": table_extractor.extract_cell(top="Flight", left=left).strip(),
                    "origin": origin,
                    "destination": destination,
                    "pieces": table_extractor.extract_cell(top="Pieces", left=left).strip(),
                    "weight": table_extractor.extract_cell(top="Weight", left=left).strip(),
                    "atd": atd.split("(")[0],
                    "ata": ata.split("(")[0],
                }
            )
        return flight_info_list


class FlightInfoTableLocator(BaseTable):
    def parse(self, table: Selector):
        header_tds = table.css("tr")[0].css("td")
        headers = [header_td.css("::text").get().strip() for header_td in header_tds]
        trs = table.css("tr")[1:]

        for index, tr in enumerate(trs):
            tds = tr.css("td")
            self._left_header_set.add(index)
            for header, td in zip(headers, tds):
                self._td_map.setdefault(header, [])
                self._td_map[header].append(td)

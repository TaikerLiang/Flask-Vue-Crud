from urllib.parse import urlencode
from typing import Dict, List

import scrapy
from scrapy import Request, FormRequest

from crawler.core_air.base_spiders import BaseAirSpider
from crawler.core_air.items import DebugItem, BaseAirItem
from crawler.core_air.rules import RuleManager, BaseRoutingRule, RequestOption
from scrapy.selector.unified import Selector


class AirChinaAirlineSpider(BaseAirSpider):
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
        option = HomePageRoutingRule.build_request_option(mawb_no=self.mawb_no)
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
    def build_request_option(cls, mawb_no) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://cargo.china-airlines.com/ccnetv2/content/home/index.aspx",
            meta={
                "mawb_no": mawb_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        mawb_no = response.meta["mawb_no"]

        hidden_form = self._extract_hidden_form(response)

        yield SearchRoutingRule.build_request_option(mawb_no=mawb_no, hidden_form=hidden_form)

    @staticmethod
    def _extract_hidden_form(response: scrapy.Selector) -> Dict:
        view_state = response.css("input#__VIEWSTATE::attr(value)").get()
        view_state_generator = response.css("input#__VIEWSTATEGENERATOR::attr(value)").get()

        return {
            "view_state": view_state,
            "view_state_generator": view_state_generator,
        }


class SearchRoutingRule(BaseRoutingRule):
    name = "SEARCH"

    @classmethod
    def build_request_option(cls, mawb_no: str, hidden_form: Dict) -> RequestOption:
        url = "https://cargo.china-airlines.com/ccnetv2/content/manage/ShipmentTracking.aspx"
        form_data = {
            "__EVENTARGUMENT": "",
            "__EVENTTARGET": "",
            "__VIEWSTATE": hidden_form["view_state"],
            "__VIEWSTATEGENERATOR": hidden_form["view_state_generator"],
            "ctl00$ContentPlaceHolder1$txtAwbPfx": AirChinaAirlineSpider.awb_prefix,
            "ctl00$ContentPlaceHolder1$txtAwbNum": mawb_no,
            "ctl00$ContentPlaceHolder1$btnSearch": "查詢",
            "ctl00$hdnLogPath": "/ccnetv2/content/home/addLog.ashx",
            "ctl00$hdnProgName": "/ccnetv2/content/manage/shipmenttracking.aspx",
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            url=url,
            body=urlencode(form_data),
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        self._extract_airline_info(response=response)
        yield BaseAirItem()

        # for airline_info in airline_info_list:
        # if ... :
        #   yield ExportErrorData()
        # else:
        #   ...
        #   yield AirItem()

    def _extract_airline_info(response: Selector):
        if not response.css("div#ContentPlaceHolder1_div_FI"):
            return None

        table = response.css("div#ContentPlaceHolder1_div_FI table")
        print(table)

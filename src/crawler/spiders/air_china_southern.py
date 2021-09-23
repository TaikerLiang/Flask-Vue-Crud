import requests
from typing import Dict
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from crawler.core_air.base_spiders import BaseAirSpider
from crawler.core_air.exceptions import (
    AirInvalidMawbNoError,
    LoadWebsiteTimeOutFatal,
)
from crawler.core_air.items import (
    BaseAirItem,
    AirItem,
    DebugItem,
)
from crawler.core_air.request_helpers import RequestOption
from crawler.core_air.rules import RuleManager, BaseRoutingRule

PREFIX = "784"
URL = "https://tang.csair.com/EN/WebFace/Tang.WebFace.Cargo/AgentAwbBrower.aspx"
LANG = "en-us"


class AirChinaSouthernSpider(BaseAirSpider):
    name = "air_china_southern"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            AirInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = AirInfoRoutingRule.build_request_option(mawb_no=self.mawb_no)
        yield self._build_request_by(option=request_option)

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

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method="POST",
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


class AirInfoRoutingRule(BaseRoutingRule):
    name = "AIR_INFO"

    @classmethod
    def build_request_option(cls, mawb_no: str) -> RequestOption:
        response = requests.post(url=URL)
        if response.status_code == 200:
            response_text = response.text
        else:
            raise LoadWebsiteTimeOutFatal()

        prompt = 'value="'
        start_pos = response_text.find(prompt, response_text.find("__VIEWSTATE")) + len(prompt)
        end_pos = response_text.find('"', start_pos)
        view_state = response_text[start_pos:end_pos]

        param_dict = {"awbprefix": PREFIX, "awbno": mawb_no, "lan": LANG}
        form_data = {
            "__VIEWSTATE": view_state,
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$ContentPlaceHolder1$txtPrefix": PREFIX,
            "ctl00$ContentPlaceHolder1$txtNo": mawb_no,
            "ctl00$ContentPlaceHolder1$btnBrow": "Search",
            "ctl00$ContentPlaceHolder1$cbIsInter": "on",
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f"{URL}?{urlencode(query=param_dict)}",
            body=urlencode(form_data),
            headers={
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/93.0.4577.82 "
                "Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "*/*",
                "Referer": "https://tang.csair.com/EN/WebFace/Tang.WebFace.Cargo/AgentAwbBrower.aspx",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6",
            },
            meta={
                "mawb_no": mawb_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response: Response):
        selector = response.css("span[id='ctl00_ContentPlaceHolder1_awbLbl'] tr td")
        basic_info = []
        for info in selector:
            basic_info.append(info.xpath("normalize-space(text())").get())

        if basic_info[0] is None:
            raise AirInvalidMawbNoError()

        routing_city = basic_info[2].split("--")
        basic_info[1] = routing_city[0].split("(")[0]
        basic_info[2] = routing_city[-1].split("(")[0]

        status_selector = response.css("table[id='ctl00_ContentPlaceHolder1_gvCargoState'] tr")
        for tr_selector in status_selector[1:]:
            city = tr_selector.xpath("normalize-space(td[2]/text())").get()
            status = tr_selector.xpath("normalize-space(td[4]/text())").get()
            if city != basic_info[1]:
                basic_info.append("")
                break
            if status == "Flight has taken off.":
                basic_info.append(tr_selector.xpath("normalize-space(td[1]/text())").get())
                break

        for tr_selector in reversed(status_selector):
            city = tr_selector.xpath("normalize-space(td[2]/text())").get()
            status = tr_selector.xpath("normalize-space(td[4]/text())").get()
            if city != basic_info[2]:
                basic_info.append("")
                break
            if status == "Cargo has been received.":
                basic_info.append(tr_selector.xpath("normalize-space(td[1]/text())").get())
                break

        air_info = self._extract_air_info(basic_info)
        yield AirItem(**air_info)

    @staticmethod
    def _extract_air_info(basic_info: list) -> Dict:
        return {
            "mawb": basic_info[0].split("-")[1],
            "origin": basic_info[1],
            "destination": basic_info[2],
            "pieces": basic_info[4],
            "weight": basic_info[5],
            "atd": basic_info[6],
            "ata": basic_info[7],
        }

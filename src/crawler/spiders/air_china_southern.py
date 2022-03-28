from typing import Union
from urllib.parse import urlencode

import requests
import scrapy
from scrapy.http import Response

from crawler.core.base import RESULT_STATUS_ERROR, SEARCH_TYPE_AWB
from crawler.core.exceptions import SuspiciousOperationError, TimeOutError
from crawler.core.items import DataNotFoundItem
from crawler.core_air.base_spiders import BaseAirSpider
from crawler.core_air.items import AirItem, BaseAirItem, DebugItem, HistoryItem
from crawler.core_air.request_helpers import RequestOption
from crawler.core_air.rules import BaseRoutingRule, RuleManager

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
        request_option = AirInfoRoutingRule.build_request_option(task_id=self.task_id, mawb_no=self.mawb_no)
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})
        routing_rule = self._rule_manager.get_rule_by_response(response=response)
        save_name = routing_rule.get_save_name()
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, (BaseAirItem, DataNotFoundItem)):
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
            raise SuspiciousOperationError(
                task_id=self.task_id,
                search_no=self.mawb_no,
                search_type=self.search_type,
                reason=f"Unexpected request method: `{option.method}`",
            )


class AirInfoRoutingRule(BaseRoutingRule):
    name = "AIR_INFO"

    @classmethod
    def build_request_option(cls, task_id: str, mawb_no: str) -> RequestOption:
        response = requests.post(url=URL, timeout=20)
        if response.status_code == 200:
            response_text = response.text
        else:
            raise TimeOutError(
                task_id=task_id,
                search_no=mawb_no,
                search_type=SEARCH_TYPE_AWB,
                reason=f"unexpected HTTP status: {str(response.status_code)}",
            )

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
                "task_id": task_id,
                "search_no": mawb_no,
            },
        )

    def get_save_name(self) -> str:
        return f"{self.name}.json"

    def handle(self, response: Response):
        if self._is_mawb_not_exist(response):
            yield DataNotFoundItem(
                task_id=response.meta["task_id"],
                search_no=response.meta["search_no"],
                search_type=SEARCH_TYPE_AWB,
                status=RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
        else:
            yield self._construct_air_item(response)

            for history_item in self._construct_history_item_list(response):
                yield history_item

    def _construct_air_item(self, response) -> Union[AirItem, DataNotFoundItem]:
        selector = response.css("span[id='ctl00_ContentPlaceHolder1_awbLbl'] tr td")
        basic_info = []
        for info in selector:
            basic_info.append(info.xpath("normalize-space(text())").get())

        if not basic_info or basic_info[0] is None:
            return DataNotFoundItem(
                task_id=response.meta["task_id"],
                search_no=response.meta["search_no"],
                search_type=SEARCH_TYPE_AWB,
                status=RESULT_STATUS_ERROR,
                detail="Data was not found",
            )

        basic_info[0] = basic_info[0].split("-")[1]
        if basic_info[0] != response.meta["search_no"]:
            return DataNotFoundItem(
                task_id=response.meta["task_id"],
                search_no=response.meta["search_no"],
                search_type=SEARCH_TYPE_AWB,
                status=RESULT_STATUS_ERROR,
                detail="Data was not found",
            )

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

        return AirItem(
            {
                "task_id": response.meta["task_id"],
                "mawb": response.meta["search_no"],
                "origin": basic_info[1],
                "destination": basic_info[2],
                "pieces": basic_info[4],
                "weight": basic_info[5],
                "atd": basic_info[6],
                "ata": basic_info[7],
            }
        )

    def _construct_history_item_list(self, response):
        info_list = []
        status_selector = response.css("table[id='ctl00_ContentPlaceHolder1_gvCargoState'] tr")
        for tr_selector in status_selector[1:]:
            info_list.append(
                HistoryItem(
                    {
                        "task_id": response.meta["task_id"],
                        "status": tr_selector.xpath("normalize-space(td[4]/text())").get(),
                        "pieces": tr_selector.xpath("normalize-space(td[5]/text())").get(),
                        "weight": tr_selector.xpath("normalize-space(td[6]/text())").get(),
                        "time": tr_selector.xpath("normalize-space(td[1]/text())").get(),
                        "location": tr_selector.xpath("normalize-space(td[2]/text())").get(),
                        "flight_number": tr_selector.xpath("normalize-space(td[3]/text())").get(),
                    }
                )
            )

        return info_list

    def _is_mawb_not_exist(self, response) -> bool:
        error_info = response.css("span[id='ctl00_ContentPlaceHolder1_lblErrorInfo'] font::text").get()
        if error_info == "Mawb information does not exist":
            return True
        else:
            return False

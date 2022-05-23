from datetime import datetime, timezone
import json
import re
from typing import List

from scrapy import Request

from crawler.core.base_new import DUMMY_URL_DICT
from crawler.core_air.base_spiders import BaseMultiAirSpider
from crawler.core_air.items import AirItem, BaseAirItem, DebugItem, HistoryItem
from crawler.core_air.rules import BaseRoutingRule, RequestOption, RuleManager

MAWB_PREFIX = "160"
URL = "https://www.cathaypacificcargo.com/ManageYourShipment/TrackYourShipment/tabid/108/SingleAWBNo/{MAWB_PREFIX}-{mawb_no}-/language/en-US/Default.aspx"


class AirCathaySpider(BaseMultiAirSpider):
    name = "air_cathay"

    def __init__(self, *args, **kwargs):
        super(AirCathaySpider, self).__init__(*args, **kwargs)

        rules = [
            TrackingResultRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = TrackingResultRoutingRule.build_request_option(mawb_nos=self.mawb_nos, task_ids=self.task_ids)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        if save_name != "ROUTING":
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
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


class TrackingResultRoutingRule(BaseRoutingRule):
    name = "TrackingResult"

    @classmethod
    def build_request_option(cls, mawb_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=URL.format(MAWB_PREFIX=MAWB_PREFIX, mawb_no=mawb_nos[0]),
            meta={
                "mawb_nos": mawb_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        mawb_no = response.meta["mawb_nos"][0]
        task_id = response.meta["task_ids"][0]
        pattern = re.compile(r"strJSON_FreightStatus = (.+)")
        res = pattern.findall(response.text)
        freight_status = json.loads(res[0].strip("'\r"))

        yield AirItem(
            mawb=mawb_no,
            task_id=task_id,
            origin=freight_status["Origin"],
            destination=freight_status["Destination"],
            weight=freight_status["QDWeight"],
            pieces=freight_status["QDPieces"],
        )

        for details in freight_status["FreightStatusDetails"]:
            if details["MDDate"]:
                time = datetime.fromtimestamp(details["MDDate"]["Seconds"]).astimezone(timezone.utc)
                yield HistoryItem(
                    task_id=task_id,
                    status=details["StatusCode"],
                    time=time.strftime(r"%Y-%m-%d %H:%M:%S %Z"),
                    location=details["MDPort1"],
                    flight_number=f'{details["MDCarrierCode"]}{details["MDFlightNum"]}',
                    pieces=details["QDPieces"],
                    weight=details["QDWeight"],
                )

        yield NextRoundRoutingRule.build_request_option(
            mawb_nos=response.meta["mawb_nos"], task_ids=response.meta["task_ids"]
        )


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    @classmethod
    def build_request_option(cls, mawb_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={
                "mawb_nos": mawb_nos,
                "task_ids": task_ids,
            },
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        mawb_nos = response.meta["mawb_nos"]

        if len(mawb_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        mawb_nos = mawb_nos[1:]

        yield TrackingResultRoutingRule.build_request_option(mawb_nos=mawb_nos, task_ids=task_ids)

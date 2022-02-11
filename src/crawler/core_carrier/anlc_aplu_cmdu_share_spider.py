import re
import json
import time
from typing import Dict, List
from random import randint

import scrapy
from scrapy import Selector

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    SuspiciousOperationError,
    DataNotFoundError,
)

from crawler.core_carrier.items import (
    BaseCarrierItem,
    MblItem,
    LocationItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    ExportErrorData,
)
from crawler.extractors.selector_finder import find_selector_from, BaseMatchRule
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core.proxy import HydraproxyProxyManager
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR

STATUS_ONE_CONTAINER = "STATUS_ONE_CONTAINER"
STATUS_MULTI_CONTAINER = "STATUS_MULTI_CONTAINER"
STATUS_MBL_NOT_EXIST = "STATUS_MBL_NOT_EXIST"
STATUS_WEBSITE_SUSPEND = "STATUS_WEBSITE_SUSPEND"

SHIPMENT_TYPE_CONTAINER = "CONTAINER"


class ForceRestart:
    pass


class AnlcApluCmduShareSpider(BaseMultiCarrierSpider):
    name = ""
    base_url = ""

    def __init__(self, *args, **kwargs):
        super(AnlcApluCmduShareSpider, self).__init__(*args, **kwargs)

        self.custom_settings.update({"CONCURRENT_REQUESTS": "1"})

        bill_rules = [
            RecaptchaRule(),
            SearchRoutingRule(),
            ContainerStatusRoutingRule(),
            NextRoundRoutingRule(),
        ]

        booking_rules = [
            RecaptchaRule(),
            SearchRoutingRule(),
            ContainerStatusRoutingRule(),
            NextRoundRoutingRule(),
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

        self._proxy_manager = HydraproxyProxyManager(session="share", logger=self.logger)

    def start(self):
        option = self._prepare_start(search_nos=self.search_nos, task_ids=self.task_ids)
        yield self._build_request_by(option=option)

    def _prepare_start(self, search_nos: List, task_ids: List):
        self._proxy_manager.renew_proxy()
        option = RecaptchaRule.build_request_option(
            base_url=self.base_url, search_nos=search_nos, task_ids=task_ids, search_type=self.search_type
        )

        proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        return proxy_option

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)
        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(result)
                yield self._build_request_by(option=proxy_option)
            elif isinstance(result, ForceRestart):
                search_nos = response.meta["search_nos"]
                task_ids = response.meta["task_ids"]
                proxy_option = self._prepare_start(search_nos=search_nos, task_ids=task_ids)
                yield self._build_request_by(option=proxy_option)
            else:
                # raise RuntimeError()
                pass

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                headers=option.headers,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


class RecaptchaRule(BaseRoutingRule):
    name = "RECAPTCHA"

    @classmethod
    def build_request_option(cls, base_url: str, search_nos: List, task_ids: List, search_type: str):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.recaptcha.net/recaptcha/enterprise/anchor?ar=1&k=6Lf1iyUaAAAAAJ2mA_9rBiiGtkxBCfO0ItCm7t-x&co=aHR0cHM6Ly93d3cuY21hLWNnbS5jb206NDQz&hl=zh-TW&size=invisible",
            meta={
                "base_url": base_url,
                "search_nos": search_nos,
                "task_ids": task_ids,
                "search_type": search_type,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        base_url = response.meta["base_url"]
        search_nos = response.meta["search_nos"]
        task_ids = response.meta["task_ids"]
        search_type = response.meta["search_type"]

        g_recaptcha_res = response.css("#recaptcha-token ::attr(value)").get()
        yield SearchRoutingRule.build_request_option(
            base_url=base_url,
            search_nos=search_nos,
            search_type=search_type,
            task_ids=task_ids,
            g_recaptcha_res=g_recaptcha_res,
        )


class SearchRoutingRule(BaseRoutingRule):
    name = "SEARCH"

    @classmethod
    def build_request_option(
        cls, base_url: str, search_nos: List, search_type: str, task_ids: List, g_recaptcha_res: str
    ) -> RequestOption:
        current_search_no = search_nos[0]

        search_by = "Booking" if not search_type == SHIPMENT_TYPE_CONTAINER else "Container"

        form_data = {
            "g-recaptcha-response": g_recaptcha_res,
            "SearchViewModel.SearchBy": search_by,
            "SearchViewModel.Reference": current_search_no,
            "SearchViewModel.FromHome": "true",
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f"{base_url}/ebusiness/tracking/search",
            form_data=form_data,
            headers={
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36",
                "referer": "https://www.cma-cgm.com/ebusiness/tracking",
            },
            meta={
                "base_url": base_url,
                "search_nos": search_nos,
                "search_type": search_type,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        base_url = response.meta["base_url"]
        search_nos = response.meta["search_nos"]
        task_ids = response.meta["task_ids"]
        search_type = response.meta["search_type"]

        current_search_no = search_nos[0]
        current_task_id = task_ids[0]

        if search_type != SHIPMENT_TYPE_CONTAINER:
            mbl_status = self._extract_mbl_status(response=response)

            if search_type == SHIPMENT_TYPE_MBL:
                basic_mbl_item = MblItem(task_id=current_task_id, mbl_no=current_search_no)
            elif search_type == SHIPMENT_TYPE_BOOKING:
                basic_mbl_item = MblItem(task_id=current_task_id, booking_no=current_search_no)

            if mbl_status == STATUS_ONE_CONTAINER:
                yield basic_mbl_item
                routing_rule = ContainerStatusRoutingRule()
                for item in routing_rule.handle(response=response):
                    yield item

            elif mbl_status == STATUS_MULTI_CONTAINER:
                yield basic_mbl_item
                container_list = self._extract_container_list(response=response)

                for container_no in container_list:
                    yield RecaptchaRule.build_request_option(
                        base_url=base_url,
                        search_nos=[container_no],
                        task_ids=task_ids,
                        search_type=SHIPMENT_TYPE_CONTAINER,
                    )

            elif mbl_status == STATUS_WEBSITE_SUSPEND:
                raise DataNotFoundError()

            else:  # STATUS_MBL_NOT_EXIST
                if search_type == SHIPMENT_TYPE_MBL:
                    yield ExportErrorData(
                        task_id=current_task_id,
                        mbl_no=current_search_no,
                        status=CARRIER_RESULT_STATUS_ERROR,
                        detail="Data was not found",
                    )
                elif search_type == SHIPMENT_TYPE_BOOKING:
                    yield ExportErrorData(
                        task_id=current_task_id,
                        booking_no=current_search_no,
                        status=CARRIER_RESULT_STATUS_ERROR,
                        detail="Data was not found",
                    )

            yield NextRoundRoutingRule.build_request_option(
                base_url=base_url,
                search_nos=search_nos,
                task_ids=task_ids,
                search_type=search_type,
            )

        else:
            routing_rule = ContainerStatusRoutingRule()
            for item in routing_rule.handle(response=response):
                yield item

    @staticmethod
    def _extract_mbl_status(response: Selector):
        invalid = bool(response.css("div.no-result"))
        single = bool(response.css("#trackingsearchsection"))
        multi = bool(response.css("#multiresultssection"))

        if invalid:
            return STATUS_MBL_NOT_EXIST
        if single:
            return STATUS_ONE_CONTAINER
        if multi:
            return STATUS_MULTI_CONTAINER
        return STATUS_WEBSITE_SUSPEND

    @staticmethod
    def _extract_container_list(response: Selector):
        container_list = response.css("dl.container-ref a::text").getall()
        return container_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"

    @classmethod
    def build_request_option(cls, container_no: str, search_no: str, task_id: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://api.myip.com/",
            meta={
                "search_no": search_no,
                "container_no": container_no,
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta["container_no"]
        return f"container_status_{container_no}.json"

    def handle(self, response):
        task_id = response.meta.get("task_id")
        if not task_id:
            task_id = response.meta["task_ids"][0]

        container_no = self._extract_container_no(response=response)
        main_info = self._extract_tracking_no_map(response=response)

        yield MblItem(
            task_id=task_id,
            por=LocationItem(name=main_info["por"]),
            pol=LocationItem(name=main_info["pol"]),
            pod=LocationItem(name=main_info["pod"]),
            final_dest=LocationItem(name=main_info["dest"]),
            eta=main_info["pod_eta"],
            ata=main_info["pod_ata"],
        )

        yield ContainerItem(
            task_id=task_id,
            container_key=container_no,
            container_no=container_no,
        )

        response_dict = self._get_response_dict(response=response)
        container_status_list = self._extract_container_status(response_dict=response_dict)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_no,
                local_date_time=container_status["local_date_time"].replace(",", ""),
                description=container_status["description"],
                location=LocationItem(name=container_status["location"]),
                est_or_actual=container_status["est_or_actual"],
                facility=container_status["facility"],
            )

    @staticmethod
    def _extract_container_no(response: Selector):
        return response.css("ul.resume-filter strong::text").get()

    @staticmethod
    def _extract_tracking_no_map(response: Selector):
        status = response.css("div.status span::text").get()
        pod_time = " ".join(response.css("div.status span strong::text").getall())

        pod_eta, pod_ata = None, None

        if status.strip() == "ETA Berth at POD":
            pod_eta = pod_time.strip()
        elif status.strip() == "Arrived at POD":
            pod_eta = None
            pod_ata = pod_time.strip()
        elif status.strip() == "Remaining":
            pod_eta = None
        else:
            raise CarrierResponseFormatError(reason=f"Unknown status {status!r}")

        pod, dest = None, None

        timeline_divs = response.css("div.timeline--item-description")
        pod_rule = SpecificSpanTextExistMatchRule("POD")
        pod_div = find_selector_from(selectors=timeline_divs, rule=pod_rule)
        if pod_div:
            pod = pod_div.css("strong::text").get()

        dest_rule = SpecificSpanTextExistMatchRule("FPD")
        dest_div = find_selector_from(selectors=timeline_divs, rule=dest_rule)
        if dest_div:
            dest = dest_div.css("strong::text").get()

        return {
            "por": response.css("li#prepol strong::text").get(),
            "pol": response.css("li#pol strong::text").get(),
            "pod": pod,
            "dest": dest,
            "pod_eta": pod_eta,
            "pod_ata": pod_ata,
        }

    @staticmethod
    def _get_response_dict(response) -> Dict:
        response_text = response.text
        match = re.search(r"options\.responseData = \'(?P<response_data>.*)\'", response_text)
        response_data = match.group("response_data")
        return json.loads(response_data)

    def _extract_container_status(self, response_dict: Dict) -> Dict:
        moves = (
            response_dict.get("PastMoves", [])
            + response_dict.get("CurrentMoves", [])
            + response_dict.get("ProvisionalMoves", [])
        )

        for move in moves:
            local_date_time = f"{move['DateString']} {move['TimeString']}"
            est_or_actual = "E" if move["State"] == "NONE" else "A"

            yield {
                "local_date_time": local_date_time,
                "description": move["StatusDescription"],
                "location": move["Location"],
                "vessel": move["Vessel"],
                "voyage": move["Voyage"],
                "est_or_actual": est_or_actual,
                "facility": move["LocationTerminal"],
            }


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, base_url: str, search_nos: List, task_ids: List, search_type: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://api.myip.com/",
            meta={
                "base_url": base_url,
                "search_nos": search_nos,
                "task_ids": task_ids,
                "search_type": search_type,
            },
        )

    def handle(self, response):
        base_url = response.meta["base_url"]
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]
        search_type = response.meta["search_type"]

        if len(search_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        search_nos = search_nos[1:]
        time.sleep(randint(1, 3))
        yield RecaptchaRule.build_request_option(
            base_url=base_url, search_nos=search_nos, task_ids=task_ids, search_type=search_type
        )


class SpecificSpanTextExistMatchRule(BaseMatchRule):
    def __init__(self, text):
        self._text = text

    def check(self, selector: Selector) -> bool:
        raw_span_text = selector.css("span::text").get()
        span_text = raw_span_text.strip() if isinstance(raw_span_text, str) else raw_span_text
        return self._text == span_text

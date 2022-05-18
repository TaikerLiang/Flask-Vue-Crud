import json
import re
from typing import Dict, List

import scrapy
from scrapy import Selector

from crawler.core.base_new import (
    DUMMY_URL_DICT,
    RESULT_STATUS_ERROR,
    SEARCH_TYPE_BOOKING,
    SEARCH_TYPE_CONTAINER,
    SEARCH_TYPE_MBL,
)
from crawler.core.description import DATA_NOT_FOUND_DESC, SUSPICIOUS_OPERATION_DESC
from crawler.core.exceptions_new import FormatError, SuspiciousOperationError
from crawler.core.items_new import DataNotFoundItem, EndItem
from crawler.core.proxy_new import HydraproxyProxyManager
from crawler.core_carrier.base_spiders_new import BaseMultiCarrierSpider
from crawler.core_carrier.items_new import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    LocationItem,
    MblItem,
)
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from

STATUS_ONE_CONTAINER = "STATUS_ONE_CONTAINER"
STATUS_MULTI_CONTAINER = "STATUS_MULTI_CONTAINER"
STATUS_MBL_NOT_EXIST = "STATUS_MBL_NOT_EXIST"
STATUS_WEBSITE_SUSPEND = "STATUS_WEBSITE_SUSPEND"

MAX_PAGE_NUM = 1


class ForceRestart:
    pass


class AnlcApluCmduShareSpider(BaseMultiCarrierSpider):
    name = ""
    base_url = ""
    custom_settings = {
        **BaseMultiCarrierSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(AnlcApluCmduShareSpider, self).__init__(*args, **kwargs)

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

        if self.search_type == SEARCH_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SEARCH_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

        self._proxy_manager = HydraproxyProxyManager(session="share", logger=self.logger)

        self._enditem_remaining_num_dict = {}

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
            if isinstance(result, (BaseCarrierItem, DataNotFoundItem)):
                yield result
            elif isinstance(result, EndItem):
                if result.get("remaining_num"):
                    self._enditem_remaining_num_dict.setdefault(result["task_id"], result["remaining_num"])
                else:
                    if not self._enditem_remaining_num_dict.get(result["task_id"]):
                        yield result
                    else:
                        self._enditem_remaining_num_dict[result["task_id"]] -= 1
                        if self._enditem_remaining_num_dict[result["task_id"]] == 0:
                            yield result
            elif isinstance(result, RequestOption):
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(result)
                yield self._build_request_by(option=proxy_option)
            elif isinstance(result, ForceRestart):
                search_nos = response.meta["search_nos"]
                task_ids = response.meta["task_ids"]

                for task_id in task_ids[:MAX_PAGE_NUM]:
                    self._enditem_remaining_num_dict.pop(task_id, None)

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
            if meta.get("task_ids"):
                zip_list = list(zip(meta["task_ids"], meta["search_nos"]))
                raise SuspiciousOperationError(
                    task_id=meta["task_ids"][0],
                    search_type=self.search_type,
                    reason=SUSPICIOUS_OPERATION_DESC.format(method=option.method)
                    + f", on (task_id, search_no): {zip_list}",
                )
            else:
                raise SuspiciousOperationError(
                    task_id=meta["task_id"],
                    search_no=meta["search_no"],
                    search_type=self.search_type,
                    reason=SUSPICIOUS_OPERATION_DESC.format(method=option.method),
                )


class RecaptchaRule(BaseRoutingRule):
    name = "RECAPTCHA"

    @classmethod
    def build_request_option(
        cls, base_url: str, search_nos: List, task_ids: List, search_type: str, research_times: int = 0
    ):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.recaptcha.net/recaptcha/enterprise/anchor?ar=1&k=6Lf1iyUaAAAAAJ2mA_9rBiiGtkxBCfO0ItCm7t-x&co=aHR0cHM6Ly93d3cuY21hLWNnbS5jb206NDQz&hl=zh-TW&size=invisible",
            meta={
                "base_url": base_url,
                "search_nos": search_nos,
                "task_ids": task_ids,
                "search_type": search_type,
                "research_times": research_times,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        base_url = response.meta["base_url"]
        search_nos = response.meta["search_nos"]
        task_ids = response.meta["task_ids"]
        search_type = response.meta["search_type"]
        research_times = response.meta["research_times"]

        g_recaptcha_res = response.css("#recaptcha-token ::attr(value)").get()
        yield SearchRoutingRule.build_request_option(
            base_url=base_url,
            search_nos=search_nos,
            search_type=search_type,
            task_ids=task_ids,
            g_recaptcha_res=g_recaptcha_res,
            research_times=research_times,
        )


class SearchRoutingRule(BaseRoutingRule):
    name = "SEARCH"

    @classmethod
    def build_request_option(
        cls,
        base_url: str,
        search_nos: List,
        search_type: str,
        task_ids: List,
        g_recaptcha_res: str,
        research_times: int,
    ) -> RequestOption:
        current_search_no = search_nos[0]

        search_by = "Booking" if not search_type == SEARCH_TYPE_CONTAINER else "Container"

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
                "research_times": research_times,
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

        info_pack = {
            "task_id": current_task_id,
            "search_no": current_search_no,
            "search_type": search_type,
        }

        if search_type != SEARCH_TYPE_CONTAINER:
            mbl_status = self._extract_mbl_status(response=response)

            if search_type == SEARCH_TYPE_MBL:
                basic_mbl_item = MblItem(task_id=current_task_id, mbl_no=current_search_no)
            else:
                basic_mbl_item = MblItem(task_id=current_task_id, booking_no=current_search_no)

            if mbl_status == STATUS_ONE_CONTAINER:
                yield basic_mbl_item
                routing_rule = ContainerStatusRoutingRule()
                for item in routing_rule.handle(response=response):
                    yield item

                yield EndItem(task_id=task_ids[0])

            elif mbl_status == STATUS_MULTI_CONTAINER:
                yield basic_mbl_item
                container_list = self._extract_container_list(response=response)

                for container_no in container_list:
                    yield EndItem(task_id=task_ids[0], remaining_num=1)
                    yield RecaptchaRule.build_request_option(
                        base_url=base_url,
                        search_nos=[container_no],
                        task_ids=task_ids,
                        search_type=SEARCH_TYPE_CONTAINER,
                    )

                if not container_list:
                    yield EndItem(task_id=task_ids[0])

            elif mbl_status == STATUS_WEBSITE_SUSPEND:
                research_times = response.meta["research_times"]
                if research_times < 3:
                    yield DebugItem(info=f"Website suspend {research_times} times, researching ...")
                    yield RecaptchaRule.build_request_option(
                        base_url=base_url,
                        search_nos=search_nos,
                        search_type=search_type,
                        task_ids=task_ids,
                        research_times=research_times + 1,
                    )
                else:
                    yield DebugItem(info=f"Website suspend {research_times} times, give up ...")
                    yield DebugItem(info=f"response:\n{response.text}")
                    raise FormatError(**info_pack, reason="Website suspend")

                return

            else:  # STATUS_MBL_NOT_EXIST
                yield DataNotFoundItem(
                    **info_pack,
                    status=RESULT_STATUS_ERROR,
                    detail=DATA_NOT_FOUND_DESC,
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

            yield EndItem(task_id=task_ids[0])

    def _extract_mbl_status(self, response: Selector):
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

    def _extract_container_list(self, response: Selector):
        container_list = response.css("dl.container-ref a::text").getall()
        return container_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"

    @classmethod
    def build_request_option(cls, container_no: str, search_no: str, task_id: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
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
        search_no = response.meta.get("search_no")

        if not task_id:
            task_id = response.meta["task_ids"][0]

        if not search_no:
            search_no = response.meta["search_nos"][0]

        info_pack = {
            "task_id": task_id,
            "search_no": search_no,
            "search_type": SEARCH_TYPE_CONTAINER,
        }

        container_no = self._extract_container_no(response=response)
        main_info = self._extract_tracking_no_map(response=response, info_pack=info_pack)

        yield MblItem(
            task_id=task_id,
            por=LocationItem(name=main_info["por"]),
            pol=LocationItem(name=main_info["pol"]),
            pod=LocationItem(name=main_info["pod"]),
            place_of_deliv=LocationItem(name=main_info["place_of_deliv"]),
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

    def _extract_container_no(self, response: Selector):
        return response.css("ul.resume-filter strong::text").get()

    def _extract_tracking_no_map(self, response: Selector, info_pack: Dict):
        status = response.css("div.status span::text").get()
        pod_time = " ".join(response.css("div.status span strong::text").getall())

        pod_eta, pod_ata = None, None
        if status:
            if status.strip() == "ETA Berth at POD":
                pod_eta = pod_time.strip()
            elif status.strip() == "Arrived at POD":
                pod_eta = None
                pod_ata = pod_time.strip()
            elif status.strip() == "Remaining":
                pod_eta = None
            else:
                raise FormatError(**info_pack, reason=f"Unknown status {repr(status)}")

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
            "place_of_deliv": response.xpath("//span[text() = 'FPD']/..//strong/text()").get(),
            "dest": dest,
            "pod_eta": pod_eta,
            "pod_ata": pod_ata,
        }

    def _get_response_dict(self, response) -> Dict:
        response_text = response.text
        match = re.search(r"options\.responseData = \'(?P<response_data>.*)\'", response_text)
        response_data = match.group("response_data")
        return json.loads(response_data)

    def _extract_container_status(self, response_dict: Dict):
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
            url=DUMMY_URL_DICT["eval_edi"],
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

        if len(search_nos) <= MAX_PAGE_NUM and len(task_ids) <= MAX_PAGE_NUM:
            return

        task_ids = task_ids[MAX_PAGE_NUM:]
        search_nos = search_nos[MAX_PAGE_NUM:]
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

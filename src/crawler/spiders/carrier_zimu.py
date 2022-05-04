import asyncio
import dataclasses
from typing import Dict, List, Tuple, Union

from pyppeteer.errors import TimeoutError
import scrapy

from crawler.core.base_new import DUMMY_URL_DICT, RESULT_STATUS_ERROR, SEARCH_TYPE_MBL
from crawler.core.exceptions_new import (
    FormatError,
    GeneralError,
    SuspiciousOperationError,
    TimeOutError,
)
from crawler.core.items_new import DataNotFoundItem, EndItem
from crawler.core.proxy_new import ProxyManager
from crawler.core.pyppeteer import PyppeteerContentGetter
from crawler.core.table import BaseTable, TableExtractor
from crawler.core_carrier.base_spiders_new import BaseCarrierSpider
from crawler.core_carrier.items_new import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    LocationItem,
    MblItem,
    VesselItem,
)
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.table_cell_extractors import (
    BaseTableCellExtractor,
    FirstTextTdExtractor,
)


class CarrierZimuSpider(BaseCarrierSpider):
    name = "carrier_zimu"

    def __init__(self, *args, **kwargs):
        super(CarrierZimuSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = MainInfoRoutingRule.build_request_option(task_id=self.task_id, mbl_no=self.mbl_no)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, (BaseCarrierItem, DataNotFoundItem, EndItem)):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

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
                callback=self.parse,
            )
        else:
            raise SuspiciousOperationError(
                task_id=self.task_id,
                search_no=self.mbl_no,
                search_type=self.search_type,
                reason=f"Unexpected request method: `{option.method}`",
            )


# ---------------------------------------------------------------------------------


class ContentGetter(PyppeteerContentGetter):
    def __init__(self, proxy_manager: ProxyManager = None):
        super().__init__(proxy_manager, is_headless=False)
        # pyppeteer_logger = logging.getLogger("pyppeteer")
        # pyppeteer_logger.setLevel(logging.WARNING)

    async def search(self, info_pack: Dict):
        await self.page.goto("https://www.zim.com/tools/track-a-shipment")

        accept_btn = "button#onetrust-accept-btn-handler"
        try:
            await self.page.waitForSelector(accept_btn, timeout=10000)
            await asyncio.sleep(1)
        except TimeoutError:
            raise TimeOutError(
                **info_pack,
                reason=f"Timeout during waiting for selector '{accept_btn}'",
            )

        await self.page.click(accept_btn)

        await asyncio.sleep(1)
        await self.page.type("input[name='consnumber']", text=info_pack["search_no"])
        await self.page.click("input[value='Track Shipment']")

        bottom_row_div = "div[class='bottom row']"
        try:
            await self.page.waitForSelector(bottom_row_div, timeout=20000)
        except TimeoutError:
            raise TimeOutError(
                **info_pack,
                reason=f"Timeout during waiting for selector '{bottom_row_div}'",
            )

        page_source = await self.page.content()

        return page_source


@dataclasses.dataclass
class VesselInfo:
    vessel: Union[str, None]
    voyage: Union[str, None]


@dataclasses.dataclass
class ScheduleInfo:
    port_type: str
    port_name: str
    eta: str
    etd: str


class MainInfoRoutingRule(BaseRoutingRule):
    name = "MAIN_INFO"

    @classmethod
    def build_request_option(cls, task_id: str, mbl_no: str) -> RequestOption:
        url = DUMMY_URL_DICT["eval_edi"]

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            meta={
                "task_id": task_id,
                "search_no": mbl_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        task_id = response.meta["task_id"]
        mbl_no = response.meta["search_no"]
        info_pack = {
            "task_id": task_id,
            "search_no": mbl_no,
            "search_type": SEARCH_TYPE_MBL,
        }

        if self._is_not_found(response=response):
            yield DataNotFoundItem(
                **info_pack,
                status=RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
            return

        if self._is_mbl_no_format_error(response=response):
            raise GeneralError(
                **info_pack,
                reason="There is format error on mbl_no",
            )

        content_getter = ContentGetter()
        response_text = asyncio.get_event_loop().run_until_complete(content_getter.search(info_pack=info_pack))
        response_selector = scrapy.Selector(text=response_text)

        for item in self._handle_item(response=response_selector, info_pack=info_pack):
            yield item

        yield EndItem(task_id=task_id)

    def _is_not_found(self, response):
        return bool(response.css("section#noResult p"))

    def _is_mbl_no_format_error(self, response):
        return bool(response.css("span.field-validation-error"))

    def _handle_item(self, response, info_pack: Dict):
        main_info = self._extract_main_info(response=response)

        raw_vessel_list = self._extract_vessel_list(response=response)
        raw_schedule_list = self._extract_schedule_list(response=response)

        vessel_list = self._arrange_vessel_list(raw_vessel_list)

        schedule_list = self._arrange_schedule_list(
            schedule_list=raw_schedule_list, main_info=main_info, info_pack=info_pack
        )

        task_id = info_pack["task_id"]

        if len(vessel_list) >= len(schedule_list):
            raise FormatError(**info_pack, reason=f"vessel_list: `{vessel_list}`, schedule_list: `{schedule_list}`")

        for vessel_index, vessel in enumerate(vessel_list):
            departure_info = schedule_list[vessel_index]
            arrival_info = schedule_list[vessel_index + 1]

            yield VesselItem(
                task_id=task_id,
                vessel_key=vessel_index,
                vessel=vessel.vessel,
                voyage=vessel.voyage,
                pol=LocationItem(name=departure_info.port_name),
                pod=LocationItem(name=arrival_info.port_name),
                etd=departure_info.etd or None,
                eta=arrival_info.eta or None,
            )

        to_pod_vessel = self._find_to_pod_vessel(vessel_list, schedule_list)

        place_of_deliv = main_info["place_of_deliv"]
        if not place_of_deliv:
            place_of_deliv_un_lo_code = None
            place_of_deliv_name = None
        elif len(place_of_deliv) == 5:
            place_of_deliv_un_lo_code = place_of_deliv
            place_of_deliv_name = None
        else:
            place_of_deliv_un_lo_code = None
            place_of_deliv_name = place_of_deliv

        yield MblItem(
            task_id=task_id,
            mbl_no=main_info["mbl_no"],
            vessel=to_pod_vessel.vessel,
            voyage=to_pod_vessel.voyage,
            por=LocationItem(name=main_info["por"]),
            pol=LocationItem(name=main_info["pol"]),
            pod=LocationItem(name=main_info["pod"]),
            place_of_deliv=LocationItem(un_lo_code=place_of_deliv_un_lo_code, name=place_of_deliv_name),
            etd=main_info["etd"] or None,
            eta=main_info["eta"] or None,
            deliv_eta=main_info["deliv_eta"] or None,
            deliv_ata=main_info["deliv_ata"] or None,
        )

        container_no_list = self._extract_container_no_list(response=response)
        for container_no in container_no_list:
            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
                terminal_pod=LocationItem(name=main_info["terminal_pod"] or None),
            )

            container_status_list = self._extract_container_status_list(response=response, container_no=container_no)
            for container_status in container_status_list:
                yield ContainerStatusItem(
                    task_id=task_id,
                    container_key=container_no,
                    description=container_status["description"],
                    local_date_time=container_status["local_time"],
                    location=LocationItem(name=container_status["location"]),
                )

    def _extract_main_info(self, response: scrapy.Selector):
        mbl_no = response.css("dl.dl-inline dd::text").get()

        if not mbl_no:
            return {}

        pod_dl = response.xpath("//dl[@class='dlist']/*[text()='POD']/..")
        if pod_dl:
            pod_info = dict(self._extract_dl(dl=pod_dl))
        else:
            pod_info = {
                "Arrival Date": "",
            }

        routing_schedule_dl_list = response.css("dl.dl-list")
        routing_schedule_list = []
        for routing_schedule_dl in routing_schedule_dl_list:
            routing_schedule_info = self._extract_dl(dl=routing_schedule_dl)
            routing_schedule_list.extend(routing_schedule_info)
        routing_schedule = dict(routing_schedule_list)

        if "Final Destination:" in routing_schedule:
            place_of_deliv = routing_schedule["Final Destination:"].strip()
            deliv_eta = response.css("dt#etaDate::text").get() or ""
            deliv_ata = deliv_eta
            eta = pod_info.get("Arrival Date", "")
        else:
            place_of_deliv = ""
            deliv_eta = ""
            deliv_ata = deliv_eta
            eta = response.css("dt#etaDate::text").get() or ""

        terminal_pod = routing_schedule.get("Terminal Name") or ""

        return {
            "mbl_no": mbl_no.strip(),
            "por": routing_schedule.get("Place of Receipt (POR)") or None,
            "pol": routing_schedule["Port of Loading (POL)"].strip(),
            "pod": routing_schedule["Port of Discharge (POD)"].strip(),
            "place_of_deliv": place_of_deliv,
            "terminal_pod": terminal_pod.strip(),
            "deliv_eta": deliv_eta.strip(),
            "deliv_ata": deliv_ata.strip(),
            "etd": routing_schedule["Sailing Date"].strip(),
            "eta": eta.strip(),
        }

    def _extract_vessel_list(self, response) -> List[Dict]:
        vessel_list = []

        vessel_td_list = response.css("table.progress-info tr.bottom-row td")
        for vessel_td in vessel_td_list:
            if vessel_td.css("::attr(class)") == "hidden":
                continue

            vessel_dl = vessel_td.css("dl")
            if not vessel_dl:
                vessel = {}
            else:
                vessel = dict(self._extract_dl(dl=vessel_dl))
            vessel_list.append(vessel)

        return vessel_list

    def _extract_schedule_list(self, response) -> List[Dict]:
        schedule_list = []

        schedule_td_list = response.css("table.progress-info tr.top-row td")
        for schedule_td in schedule_td_list:
            schedule_dl = schedule_td.css("dl")
            if not schedule_dl:
                schedule = {}
            else:
                may_empty_schedule = dict(self._extract_dl(dl=schedule_dl))
                schedule = {} if "" in may_empty_schedule else may_empty_schedule
            schedule_list.append(schedule)

        return schedule_list

    def _arrange_vessel_list(self, raw_vessel_list) -> List[VesselInfo]:
        vessel_list = []
        for raw_vessel in raw_vessel_list:
            if not raw_vessel:
                continue

            vessel_name, voyage = raw_vessel["Vessel / Voyage"].split("/", 1)
            vessel_list.append(VesselInfo(vessel=vessel_name, voyage=voyage))

        return vessel_list

    def _arrange_schedule_list(self, schedule_list: List[Dict], main_info: Dict, info_pack: Dict) -> List[ScheduleInfo]:
        result = [
            ScheduleInfo(port_type="POL", port_name=main_info["pol"], eta="", etd=main_info["etd"]),  # POL
        ]
        for schedule in schedule_list:
            if not schedule:
                continue

            elif "Transshipment" in schedule:
                result.append(
                    ScheduleInfo(
                        port_type="Transshipment",
                        port_name=schedule["Transshipment"],
                        eta=schedule.get("Arrival Date", ""),
                        etd=schedule.get("Sailing Date", ""),
                    )
                )

            elif "POD" in schedule:
                result.append(
                    ScheduleInfo(
                        port_type="POD",
                        port_name=schedule["POD"],
                        eta=schedule.get("Arrival Date", ""),
                        etd="",
                    )
                )

            elif "POL" in schedule:
                pass

            else:
                raise FormatError(**info_pack, reason=f"Unknown port type of schedule: `{schedule}`")

        # add POD ?
        last_schedule = result[-1]
        if last_schedule.port_type != "POD":
            result.append(
                ScheduleInfo(
                    port_type="POD",
                    port_name=main_info["pod"],
                    eta=main_info["eta"],
                    etd="",
                )
            )

        return result

    def _find_to_pod_vessel(self, vessel_list, schedule_list) -> VesselInfo:
        last_schedule_info = schedule_list[-1]
        assert last_schedule_info.port_type == "POD"

        is_last_vessel_to_pod = len(schedule_list) == (len(vessel_list) + 1)

        if is_last_vessel_to_pod:
            return vessel_list[-1]
        else:
            return VesselInfo(vessel=None, voyage=None)

    def _extract_container_no_list(self, response) -> List[str]:
        container_no_not_strip_list = response.css("div.opener h3::text").getall()
        container_no_list = []

        for container_no_not_strip in container_no_not_strip_list:
            container_no_list.append(container_no_not_strip.strip())
        return container_no_list

    def _extract_container_status_list(self, response, container_no) -> List[Dict]:
        table_css_query = f"div[data-cont-id='{container_no} '] + div.slide table"
        table_selector = response.css(table_css_query)

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table_extractor = TableExtractor(table_locator=table_locator)
        first_text_td_extractor = FirstTextTdExtractor()

        container_status_list = []
        for left in table_locator.iter_left_header():
            container_status_list.append(
                {
                    "description": table_extractor.extract_cell(
                        top="Activity", left=left, extractor=first_text_td_extractor
                    ),
                    "location": table_extractor.extract_cell(
                        top="Location", left=left, extractor=first_text_td_extractor
                    ),
                    "local_time": table_extractor.extract_cell(
                        top="Local Date & Time", left=left, extractor=first_text_td_extractor
                    ),
                }
            )

        return container_status_list

    def _extract_dl(self, dl: scrapy.Selector, dt_extractor=None, dd_extractor=None) -> List[Tuple[str, str]]:
        """
        <dl>
            <dt></dt> --+-- pair
            <dd></dd> --+
            <dt></dt>
            <dd></dd>
            ...
        </dl>
        """
        if dt_extractor is None:
            dt_extractor = FirstTextTdExtractor()
        if dd_extractor is None:
            dd_extractor = AllTextCellExtractor()

        dt_list = dl.css("dt")
        dl_info_list = []

        for dt_index, dt in enumerate(dt_list):
            dd = dt.xpath("following-sibling::dd[1]")

            dt_text = dt_extractor.extract(dt)
            dd_text = dd_extractor.extract(dd)
            dl_info_list.append((dt_text, dd_text))

        return dl_info_list


# ------------------------------------------------------------------------


class ContainerStatusTableLocator(BaseTable):
    def parse(self, table: scrapy.Selector):
        top_header_list = []

        for th in table.css("thead th"):
            raw_top_header = th.css("::text").get()
            top_header = raw_top_header.strip() if isinstance(raw_top_header, str) else ""
            top_header_list.append(top_header)
            self._td_map[top_header] = []

        data_tr_list = table.css("tbody tr")
        for index, tr in enumerate(data_tr_list):
            self._left_header_set.add(index)
            for top, td in zip(top_header_list, tr.css("td")):
                self._td_map[top].append(td)


class AllTextCellExtractor(BaseTableCellExtractor):
    def __init__(self, css_query: str = "::text"):
        self.css_query = css_query

    def extract(self, cell: scrapy.Selector):
        text_not_strip_list = cell.css(self.css_query).getall()
        text_list = [text.strip() for text in text_not_strip_list if isinstance(text, str)]
        return " ".join(text_list)

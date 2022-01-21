import dataclasses
import re
import asyncio
import time
from typing import Tuple, List, Optional

from scrapy import Selector, FormRequest, Request
from pyppeteer.errors import TimeoutError, PageError

from crawler.core.table import BaseTable, TableExtractor
from crawler.core.defines import BaseContentGetter
from crawler.core.proxy import HydraproxyProxyManager, ProxyManager
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core.pyppeteer import PyppeteerContentGetter
from crawler.core.base import RESULT_STATUS_FATAL

from crawler.core_carrier.items import (
    BaseCarrierItem,
    MblItem,
    LocationItem,
    VesselItem,
    ContainerItem,
    ExportErrorData,
    ContainerStatusItem,
    DebugItem,
)
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    SuspiciousOperationError,
    ProxyMaxRetryError,
)
from crawler.extractors.selector_finder import CssQueryTextStartswithMatchRule, find_selector_from
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor


BASE_URL = "https://www.hamburgsud-line.com/linerportal/pages/hsdg/tnt.xhtml"

MAX_RETRY_COUNT = 3


@dataclasses.dataclass
class Restart:
    search_nos: list
    task_ids: list
    reason: str = ""


@dataclasses.dataclass
class VoyageSpec:
    direction: str
    container_key: str
    voyage_key: str
    location: str  # for debug purpose
    container_no: str  # for debug purpose


class CarrierSuduSpider(BaseMultiCarrierSpider):
    name = "carrier_sudu_multi"

    def __init__(self, *args, **kwargs):
        super(CarrierSuduSpider, self).__init__(*args, **kwargs)
        self._driver = ContentGetter(
            proxy_manager=HydraproxyProxyManager(session="sudu", logger=self.logger), is_headless=True
        )

        rules = [
            MblRoutingRule(content_getter=self._driver, logger=self.logger),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self.retry_count = 1

    def start(self):
        option = MblRoutingRule.build_request_option(mbl_nos=self.search_nos, task_ids=self.task_ids)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(result)
            elif isinstance(result, Restart):
                search_nos = result.search_nos
                task_ids = result.task_ids
                self.logger.warning(f"----- {result.reason}, try new proxy and restart")

                try:
                    self._driver.proxy_manager.renew_proxy()
                except ProxyMaxRetryError:
                    for search_no, task_id in zip(search_nos, task_ids):
                        yield ExportErrorData(
                            mbl_no=search_no,
                            task_id=task_id,
                            status=CARRIER_RESULT_STATUS_ERROR,
                            detail="proxy max retry error",
                        )
                    return

                option = MblRoutingRule.build_request_option(mbl_nos=search_nos, task_ids=task_ids)
                yield self._build_request_by(option)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return Request(
                url=option.url,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


# -------------------------------------------------------------------------------


class MblRoutingRule(BaseRoutingRule):
    name = "MBL_RULE"
    retry_count = 1

    def __init__(self, content_getter: BaseContentGetter, logger):
        self.driver = content_getter
        self.logger = logger

    @classmethod
    def build_request_option(cls, mbl_nos, task_ids):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f"https://api.myip.com/",
            meta={"mbl_nos": mbl_nos, "task_ids": task_ids},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        mbl_nos = response.meta["mbl_nos"]
        task_ids = response.meta["task_ids"]

        try:
            page_source = asyncio.get_event_loop().run_until_complete(self.driver.search(search_no=mbl_nos[0]))
            response_selector = Selector(text=page_source)
            if self._is_mbl_no_invalid(response_selector):
                yield ExportErrorData(
                    mbl_no=mbl_nos[0],
                    task_id=task_ids[0],
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )
            elif self.is_multi_containers(response_selector):
                ct_links = asyncio.get_event_loop().run_until_complete(self.driver.get_container_links())
                for idx in range(len(ct_links)):
                    # avoid Node is detached from document
                    ct_links = asyncio.get_event_loop().run_until_complete(self.driver.get_container_links())
                    content = asyncio.get_event_loop().run_until_complete(
                        self.driver.go_to_next_container_page(ct_links, idx)
                    )

                    if not content:
                        yield Restart(search_nos=mbl_nos, task_ids=task_ids, reason="Content not extracted correctly")
                        return

                    ct_detail_selector = Selector(text=content)

                    voyage_contents = asyncio.get_event_loop().run_until_complete(self.driver.get_voyage_contents())
                    for result in self.handle_detail_page(
                        response=ct_detail_selector, task_id=task_ids[0], voyage_contents=voyage_contents
                    ):
                        if isinstance(result, BaseCarrierItem):
                            yield result
                        else:
                            raise RuntimeError()
                    if not voyage_contents:
                        asyncio.get_event_loop().run_until_complete(self.driver.find_and_scroll())  # search again
                        continue
                    asyncio.get_event_loop().run_until_complete(self.driver.go_back_from_container_detail_page())
            else:
                voyage_contents = asyncio.get_event_loop().run_until_complete(self.driver.get_voyage_contents())
                for result in self.handle_detail_page(
                    response=response_selector, task_id=task_ids[0], voyage_contents=voyage_contents
                ):
                    if isinstance(result, BaseCarrierItem):
                        yield result
                    else:
                        raise RuntimeError()
            asyncio.get_event_loop().run_until_complete(self.driver.reset_mbl_search_textarea())

        except (TimeoutError, PageError, IndexError):
            # need close first
            if self.retry_count >= MAX_RETRY_COUNT:
                yield ExportErrorData(status=RESULT_STATUS_FATAL, detail="<max-retry-error>")
                return

            self.retry_count += 1
            self.driver.quit()
            self.driver = ContentGetter(
                proxy_manager=HydraproxyProxyManager(session="sudu", logger=self.logger), is_headless=True
            )
            yield MblRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)
            return

        yield NextRoundRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)

    @staticmethod
    def _is_mbl_no_invalid(response):
        error_message = response.css("span.ui-messages-info-summary::text").get()
        if not error_message:
            return

        error_message.strip()
        return error_message.startswith("No results found.")

    @staticmethod
    def is_multi_containers(response):
        """
        Are there multiple containers in this mbl?
        """
        # detail_div contains detail_table which is in detail page
        detail_div = response.css("div.ui-grid-responsive")

        if detail_div:
            return False
        return True

    @staticmethod
    def _extract_container_link_element_map(response):
        container_link_elements = response.css('a[class="ui-commandlink ui-widget"]::attr(id)').getall()
        container_nos = response.css('a[class="ui-commandlink ui-widget"]::text').getall()

        container_link_element_map = {container_nos[i]: container_link_elements[i] for i in range(len(container_nos))}
        return container_link_element_map

    def handle_detail_page(self, response: Selector, voyage_contents: List, task_id: str):
        voyage_content_selectors = [Selector(text=voyage_content) for voyage_content in voyage_contents]

        # parse
        main_info = self._extract_main_info(response=response)
        container_statuses = self.extract_container_statuses(
            response=response, voyage_contents=voyage_content_selectors
        )
        container_no = main_info["container_no"]
        por = main_info["por"].strip()
        final_dest = main_info["final_dest"].strip()

        yield MblItem(
            task_id=task_id,
            por=LocationItem(name=por),
            final_dest=LocationItem(name=final_dest),
            carrier_release_date=main_info["carrier_release_date"] or None,
            customs_release_date=main_info["customs_release_date"] or None,
        )

        yield ContainerItem(
            task_id=task_id,
            container_key=container_no,
            container_no=container_no,
        )

        for container_status in container_statuses:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_no,
                description=container_status["description"],
                local_date_time=container_status["timestamp"],
                location=LocationItem(name=container_status["location"] or None),
                vessel=container_status["vessel"] or None,
                voyage=container_status["voyage"] or None,
            )

        if voyage_contents:
            departure_voyage_spec, arrival_voyage_spec = self._get_container_voyage_link_element_specs(
                por=por,
                final_dest=final_dest,
                container_statuses=container_statuses,
                container_key=container_no,
                container_no=container_no,
            )

            for voyage_spec in [departure_voyage_spec, arrival_voyage_spec]:
                if not voyage_spec:
                    continue

                voyage_routing = self._extract_voyage_routing(
                    voyage_routing_responses=voyage_content_selectors,
                    location=voyage_spec.location.strip(),
                    direction=voyage_spec.direction.strip(),
                )

                yield VesselItem(
                    task_id=task_id,
                    vessel_key=f"{voyage_spec.location} {voyage_spec.direction}",
                    vessel=voyage_routing["vessel"],
                    voyage=voyage_routing["voyage"],
                    pol=LocationItem(name=voyage_routing["pol"]),
                    pod=LocationItem(name=voyage_routing["pod"]),
                    etd=voyage_routing["etd"],
                    eta=voyage_routing["eta"],
                )

    @staticmethod
    def _get_container_voyage_link_element_specs(
        por, final_dest, container_statuses, container_key, container_no
    ) -> Tuple:
        # voyage part
        departure_voyages = []
        arrival_voyages = []
        for container_status in container_statuses:
            vessel = container_status["vessel"]
            location = container_status["location"]

            for container_status in container_statuses:
                vessel = container_status["vessel"]
                location = container_status["location"]
                location = location.replace("Place ", "").strip()

                if vessel and location == por:
                    voyage_spec = VoyageSpec(
                        direction="Departure",
                        container_key=container_key,
                        voyage_key=container_status["voyage_css_id"],
                        location=por,
                        container_no=container_no,
                    )
                    departure_voyages.append(voyage_spec)

                elif vessel and location == final_dest:
                    voyage_spec = VoyageSpec(
                        direction="Arrival",
                        container_key=container_key,
                        voyage_key=container_status["voyage_css_id"],
                        location=final_dest,
                        container_no=container_no,
                    )
                    arrival_voyages.append(voyage_spec)

        first_departure_voyage = None
        if departure_voyages:
            first_departure_voyage = departure_voyages[0]

        last_arrival_voyage = None
        if arrival_voyages:
            last_arrival_voyage = arrival_voyages[-1]

        return first_departure_voyage, last_arrival_voyage

    @staticmethod
    def _extract_main_info(response):
        titles = response.css("h3")
        rule = CssQueryTextStartswithMatchRule(css_query="::text", startswith="Details")
        details_title = find_selector_from(selectors=titles, rule=rule)
        detail_div = details_title.xpath("./following-sibling::div")

        div_locator = MainDivTableLocator()
        div_locator.parse(table=detail_div)
        table = TableExtractor(table_locator=div_locator)

        carrier_release_date = ""
        if table.has_header(top="Carrier release"):
            carrier_release_date = table.extract_cell(top="Carrier release")

        customs_release_date = ""
        if table.has_header(top="Customs release"):
            customs_release_date = table.extract_cell(top="Customs release")

        return {
            "container_no": table.extract_cell(top="Container"),
            "por": table.extract_cell(top="Origin"),
            "final_dest": table.extract_cell(top="Destination"),
            "carrier_release_date": carrier_release_date,
            "customs_release_date": customs_release_date,
        }

    def extract_container_statuses(self, response, voyage_contents):
        titles = response.css("h3")
        rule = CssQueryTextStartswithMatchRule(css_query="::text", startswith="Main information")
        main_info_title = find_selector_from(selectors=titles, rule=rule)
        main_info_div = main_info_title.xpath("./following-sibling::div")[0]

        table_selector = main_info_div.css("table")
        container_status_locator = ContainerStatusTableLocator()
        container_status_locator.parse(table=table_selector)
        ct_page_td_extrcator = ContainerDetailPageTdExtractor()
        table = TableExtractor(table_locator=container_status_locator)
        vessel_voyage_extractor = VesselVoyageTdExtractor()

        container_statuses = []
        for left in container_status_locator.iter_left_header():
            vessel_voyage_info = table.extract_cell(top="Mode/Vendor", left=left, extractor=vessel_voyage_extractor)
            container_statuses.append(
                {
                    "timestamp": table.extract_cell(top="Date", left=left, extractor=ct_page_td_extrcator),
                    "location": table.extract_cell(top="Place", left=left, extractor=ct_page_td_extrcator),
                    "description": table.extract_cell(top="Movement", left=left, extractor=ct_page_td_extrcator),
                    "vessel": vessel_voyage_info["vessel"],
                    "voyage": vessel_voyage_info["voyage"],
                    "voyage_css_id": vessel_voyage_info["voyage_css_id"],
                }
            )

        container_statuses.reverse()
        return container_statuses

    def _extract_voyage_routing(self, voyage_routing_responses: List[Selector], location, direction):
        if direction == "Arrival":
            response = voyage_routing_responses[0]
        else:
            response = voyage_routing_responses[-1]
        raw_vessel_voyage = response.css("h3::text").get()
        vessel, voyage = self._parse_vessel_voyage(raw_vessel_voyage)

        table_selector = response.css('table[role="grid"]')
        if not table_selector:
            raise CarrierResponseFormatError(reason="Can not find voyage routing table !!!")

        voyage_routing_locator = VoyageRoutingTableLocator()
        voyage_extractor = VoyageDetailPageTdExtractor()
        voyage_routing_locator.parse(table=table_selector)

        table = TableExtractor(table_locator=voyage_routing_locator)

        eta, etd, pol, pod = None, None, None, None
        if direction == "Arrival":
            eta = table.extract_cell(top="Estimated Arrival", left=location, extractor=voyage_extractor)
            pod = location

        elif direction == "Departure":
            etd = table.extract_cell(top="Estimated Departure", left=location, extractor=voyage_extractor)
            pol = location

        else:
            raise CarrierResponseFormatError(reason=f"Unknown arr_or_dep: `{direction}`")

        return {
            "vessel": vessel,
            "voyage": voyage,
            "eta": eta,
            "etd": etd,
            "pol": pol,
            "pod": pod,
        }

    @staticmethod
    def _parse_vessel_voyage(vessel_voyage):
        pattern = re.compile(r"^Voyage details -\s+(?P<vessel>[\w+ ]+\w+) -\s+(?P<voyage>\w+)\s+$")
        match = pattern.match(vessel_voyage)
        if not match:
            raise CarrierResponseFormatError(reason=f"Unknown vessel_voyage title: `{vessel_voyage}`")

        return match.group("vessel"), match.group("voyage")


# -------------------------------------------------------------------------------


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    @classmethod
    def build_request_option(cls, mbl_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://api.myip.com/",
            meta={"mbl_nos": mbl_nos, "task_ids": task_ids},
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        mbl_nos = response.meta["mbl_nos"]

        if len(mbl_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        mbl_nos = mbl_nos[1:]

        yield MblRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)


# -------------------------------------------------------------------------------


class ContentGetter(PyppeteerContentGetter):
    def __init__(self, proxy_manager: Optional[ProxyManager] = None, is_headless: Optional[bool] = True):
        super().__init__(proxy_manager, is_headless=is_headless)

    async def search(self, search_no: str):
        await self.page.goto(BASE_URL, options={"waitUntil": "networkidle0", "timeout": 30000})
        await asyncio.sleep(5)
        await self.page.type("textarea[id$=inputReferences]", search_no)
        await asyncio.sleep(2)
        await self.find_and_scroll()

        return await self.page.content()

    async def find_and_scroll(self):
        await self.page.click("button[id$=search-submit]")
        await asyncio.sleep(5)
        await self.scroll_down()

    async def get_voyage_contents(self):
        # the voyage pages in different container status are the same
        contents = []
        links = await self._get_distinct_voyage_links()

        for link in links:
            await self.page.evaluate("""elem => elem.click()""", link)
            time.sleep(5)
            await self.scroll_down()
            time.sleep(5)
            content = await self.page.content()
            try:
                await self.page.click("button[id$=voyageBackButton]")
            except PageError:
                # special case, if the voyage_contents page is emtpy, the website will reset the result
                return []
            time.sleep(5)
            await self.scroll_down()
            time.sleep(2)
            contents.append(content)

        return contents

    async def _get_distinct_voyage_links(self):
        links = await self.page.querySelectorAll("a[id*='voyageDetailsLink']")
        voyage_num_link_map = {await self._get_voyage_link_text(link): link for link in links}
        return list(voyage_num_link_map.values())

    async def _get_voyage_link_text(self, link_elem_handle):
        return await self.page.evaluate("""e => e.textContent""", link_elem_handle)

    async def get_container_links(self, idx: Optional[int] = -1):
        if idx >= 0:
            links = await self.page.querySelectorAll("a[id*='contDetailsLink']")
            return links[idx]
        return await self.page.querySelectorAll("a[id*='contDetailsLink']")

    async def go_to_next_container_page(self, links: List, idx: int):
        await links[idx].click()
        await asyncio.sleep(5)
        await self.page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
        await asyncio.sleep(3)
        return await self.page.content()

    async def go_back_from_container_detail_page(self):
        await self.page.click("button[id$=contDetailsBackButton]")
        time.sleep(5)
        await self.scroll_down()
        time.sleep(2)

    async def reset_mbl_search_textarea(self):
        await self.page.click("button[id$=search-reset]")
        time.sleep(3)


class ContainerDetailPageTdExtractor(BaseTableCellExtractor):
    def __init__(self, css_query: str = "::text"):
        self.css_query = css_query

    def extract(self, cell: Selector) -> str:
        td_text_list = cell.css(self.css_query).getall()
        if len(td_text_list) == 1:
            return None
        return td_text_list[-1]


class VoyageDetailPageTdExtractor(BaseTableCellExtractor):
    def __init__(self, css_query: str = "::text"):
        self.css_query = css_query

    def extract(self, cell: Selector) -> str:
        td_text_list = cell.css(self.css_query).getall()
        if len(td_text_list) == 1:
            return None
        return td_text_list[-1]


class VesselVoyageTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        a_list = cell.css("a")

        if len(a_list) == 0:
            return {
                "vessel": "",
                "voyage": "",
                "voyage_css_id": "",
            }

        vessel_cell = a_list[0]
        voyage_cell = a_list[1]

        return {
            "vessel": vessel_cell.css("::text").get().strip(),
            "voyage": voyage_cell.css("::text").get().strip(),
            "voyage_css_id": voyage_cell.css("::attr(id)").get(),
        }


class ContainerStatusTableLocator(BaseTable):
    def parse(self, table: Selector):
        title_text_list = table.css("thead th ::text").getall()
        data_tr_list = table.css("tbody tr")

        for index, tr in enumerate(data_tr_list):
            tds = tr.css("td")
            self.add_left_header_set(index)
            for title, td in zip(title_text_list, tds):
                self._td_map.setdefault(title, [])
                self._td_map[title].append(td)


class VoyageRoutingTableLocator(BaseTable):
    def parse(self, table: Selector):
        title_text_list = table.css("thead th ::text").getall()
        data_tr_list = table.css("tbody tr")

        for tr in data_tr_list:
            tds = tr.css("td")
            left_header = tds[0].css("::text").get()
            self.add_left_header_set(left_header)

            for title, td in zip(title_text_list, tds[1:]):
                self._td_map.setdefault(title, {})
                self._td_map[title][left_header] = td


class MainDivTableLocator(BaseTable):
    def parse(self, table: Selector):
        div_section_list = table.css("div.ui-g")

        for div_section in div_section_list:

            cell_list = div_section.xpath("./div")
            for cell in cell_list:
                title, data = cell.css("::text").getall()
                td = Selector(text=f"<td>{data.strip()}</td>")

                self._td_map.setdefault(title, [])
                self._td_map[title].append(td)

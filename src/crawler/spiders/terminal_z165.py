import scrapy

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, ExportErrorData
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.core.table import BaseTable, TableExtractor


BASE_URL = "https://www.imperialcfs.com"


class TerminalImperialCfsSpider(BaseMultiTerminalSpider):
    firms_code = "Z165"
    name = "terminal_imperial_cfs"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        for container_no in unique_container_nos:
            option = ContainerRoutingRule.build_request_option(container_no=container_no)
            yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, ExportErrorData):
                c_no = result["container_no"]
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result["task_id"] = t_id
                    yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )

        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = "CONTAINER"

    @classmethod
    def build_request_option(cls, container_no: str) -> RequestOption:
        url = f"{BASE_URL}/Availability/Index/Cntr/{container_no}"

        return RequestOption(
            rule_name=cls.name, method=RequestOption.METHOD_GET, url=url, meta={"container_no": container_no}
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}_{response.meta['container_no']}.html"

    def handle(self, response):
        container_no = response.meta["container_no"]
        if self._is_container_no_invalid(response):
            yield ExportErrorData(
                container_no=container_no,
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )
            return

        table_selector = response.xpath("//*[@id='info']/div[1]/div[2]/table")
        left_table_locator = MainInfoTableLocator()
        left_table_locator.parse(table=table_selector)
        left_table = TableExtractor(table_locator=left_table_locator)

        table_selector = response.xpath("//*[@id='info']/div[1]/div[3]/table")
        right_table_locator = MainInfoTableLocator()
        right_table_locator.parse(table=table_selector)
        right_table = TableExtractor(table_locator=right_table_locator)

        yield TerminalItem(
            container_no=left_table.extract_cell(left="CONTAINER NO.") or None,
            mbl_no=left_table.extract_cell(left="MBL NO.") or None,
            last_free_day=right_table.extract_cell(left="LAST FREE DATE") or None,
            vessel=left_table.extract_cell(left="VESSEL") or None,
        )

    def _is_container_no_invalid(self, response):
        if response.css("div.Availability-table h1::text").get() == "Unable to Locate Shipment":
            return True
        return False


class MainInfoTableLocator(BaseTable):
    def parse(self, table: scrapy.Selector):
        trs = table.css("tr")
        for tr in trs:
            title = tr.css("th::text").get().strip()
            data_td = tr.css("td")
            self.add_left_header_set(title)
            td_dict = self._td_map.setdefault(0, {})
            td_dict[title] = data_td

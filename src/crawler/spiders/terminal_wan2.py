import scrapy

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.core.table import BaseTable, TableExtractor


BASE_URL = "https://cloud2.cargomanager.com/warehousingEMP/availability"


class TerminalEmpireCfsSpider(BaseMultiTerminalSpider):
    firms_code = "WAN2"
    name = "terminal_empire_cfs"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
            ContainerDetailRoutingRule(),
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
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
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
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
            )

        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = "CONTAINER"

    @classmethod
    def build_request_option(cls, container_no: str) -> RequestOption:
        url = f"{BASE_URL}/results.jsp"

        form_data = {
            "code": "EMP",
            "fileType": "CFS",
            "container": container_no,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=url,
            form_data=form_data,
            meta={"container_no": container_no},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_no = response.meta["container_no"]
        if self._is_container_no_invalid(response):
            yield InvalidContainerNoItem(container_no=container_no)
            return

        container_detail_href = response.css("a[target='details'] ::attr(href)").get()
        yield ContainerDetailRoutingRule.build_request_option(container_no=container_no, href=container_detail_href)

    def _is_container_no_invalid(self, response):
        if response.css("table.spreadsheet td::text").get() == "No results found":
            return True
        return False


class ContainerDetailRoutingRule(BaseRoutingRule):
    name = "CONTAINER_DETAIL"

    @classmethod
    def build_request_option(cls, container_no: str, href: str) -> RequestOption:
        url = f"{BASE_URL}/{href}"

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        table_selector = response.css("table.cfsdetails")
        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        yield TerminalItem(
            container_no=table.extract_cell(left="Container No:") or None,
            mbl_no=table.extract_cell(left="Master B/L No:") or None,
            vessel=table.extract_cell(left="Vessel Name:") or None,
            last_free_day=table.extract_cell(left="Free Time Expires:") or None,
            gate_out_date=table.extract_cell(left="G.O. Starts:") or None,
        )


class ContainerStatusTableLocator(BaseTable):
    def parse(self, table: scrapy.Selector):
        title_tds = table.css("td.label")
        data_tds = table.css("td:not([class='label'])").getall()
        data_tds = data_tds[:-3] + data_tds[-1:]

        for title_td, data_td in zip(title_tds, data_tds):
            title = title_td.css("::text").get().strip()
            data_td = scrapy.Selector(text=data_td)
            self.add_left_header_set(title)
            td_dict = self._td_map.setdefault(0, {})
            td_dict[title] = data_td

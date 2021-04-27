from scrapy import Request, FormRequest, Selector

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import (
    BaseTerminalItem, DebugItem, TerminalItem, InvalidContainerNoItem
)
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

BASE_URL = 'https://payments.gcterminals.com'


class TerminalGlobalMultiSpider(BaseMultiTerminalSpider):
    name = 'terminal_global_multi'

    def __init__(self, *args, **kwargs):
        super(TerminalGlobalMultiSpider, self).__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        for container_no in self.container_no_list:
            option = ContainerRoutingRule.build_request_option(container_no=container_no)
            yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseTerminalItem):
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
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        url = f'{BASE_URL}/GlobalTerminal/globalSearch.do'
        form_data = {
            'containerSelectedIndexParam': '',
            'searchId': 'BGLOB',
            'searchType': 'container',
            'searchTextArea': container_no,
            'searchText': '',
            'buttonClicked': 'Search',
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=url,
            form_data=form_data,
            meta={
                'container_no': container_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = response.meta['container_no']

        if self._is_container_no_invalid(response=response):
            yield InvalidContainerNoItem(container_no=container_no)
            return

        # extract
        result_table = response.css('div#results-div table')
        table_locator = GlobalLeftTableLocator()
        table_locator.parse(table=result_table)
        table_extractor = TableExtractor(table_locator=table_locator)

        assert container_no == table_extractor.extract_cell(left='Container #', top=None)

        yield TerminalItem(
            container_no=container_no,
            freight_release=table_extractor.extract_cell(left='Freight Released', top=None),
            customs_release=table_extractor.extract_cell(left='Customs Released', top=None),
            discharge_date=table_extractor.extract_cell(left='Discharge Date', top=None),
            ready_for_pick_up=table_extractor.extract_cell(left='Available for Pickup', top=None),
            last_free_day=table_extractor.extract_cell(left='Last Free Day', top=None),
            gate_out_date=table_extractor.extract_cell(left='Gate Out Date', top=None),
            demurrage=table_extractor.extract_cell(left='Demurrage', top=None),
            carrier=table_extractor.extract_cell(left='Line', top=None),
            container_spec=table_extractor.extract_cell(left='Container Type', top=None),
            vessel=table_extractor.extract_cell(left='Vessel', top=None),
            voyage=table_extractor.extract_cell(left='Voyage', top=None),
        )

    @staticmethod
    def _is_container_no_invalid(response: Selector) -> bool:
        return bool(response.css('div.error-messages'))


class GlobalLeftTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}  # title : td

    def parse(self, table: Selector):
        trs = table.css('tr')

        for tr in trs:
            titles = tr.css('td.label-column::text').getall()
            data_tds = tr.css('td.data-column')

            if len(titles) != len(data_tds):
                data_tds.extend(tr.css('td.data-column-red'))
                data_tds.extend(tr.css('td.data-column-blue'))

            for title, data_td in zip(titles, data_tds):
                title_without_colon = title.strip()[:-1]
                self._td_map[title_without_colon] = data_td

    def get_cell(self, left: str, top=None) -> Selector:
        assert top is None
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return self._td_map.get(left)


import requests
from scrapy import Request, FormRequest, Selector
from urllib.parse import urlencode

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
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
        unique_container_nos = list(self.cno_tid_map.keys())
        option = ContainerRoutingRule.build_request_option(container_no_list=unique_container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result['container_no']
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result['task_id'] = t_id
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
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no_list) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url='https://yahoo.com',
            meta={
                'container_no_list': container_no_list,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no_list = response.meta['container_no_list']
        # special case
        if len(container_no_list) == 1:
            container_no_list = container_no_list + container_no_list

        url = "http://payments.gcterminals.com/GlobalTerminal/globalSearch.do"

        for i in range(len(container_no_list)):
            form_data = {
                'containerSelectedIndexParam': str(i),
                'searchId': 'BGLOB',
                'searchType': 'container',
                'searchTextArea': '\n'.join(container_no_list),
                'searchText': '',
                'buttonClicked': 'Search',
            }

            headers = {
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Origin': 'http://payments.gcterminals.com',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Referer': 'http://payments.gcterminals.com/GlobalTerminal/globalSearch.do',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            resp = requests.request("POST", url, headers=headers, data=urlencode(form_data))
            resp_selector = Selector(text=resp.text)

            # extract
            result_table = resp_selector.css('div#results-div table')
            table_locator = GlobalLeftTableLocator()
            table_locator.parse(table=result_table, numbers=len(container_no_list))

            last_free_day_val = resp_selector.xpath('//*[@id="results-div"]/center[3]/table/tr[12]/td[4]/text()').get()

            yield TerminalItem(
                container_no=table_locator.get_cell(left=i, top='Container #'),
                freight_release=table_locator.get_cell(left=i, top='Freight Released'),
                customs_release=table_locator.get_cell(left=i, top='Customs Released'),
                ready_for_pick_up=table_locator.get_cell(left=i, top='Avail for Pickup'),
                discharge_date=table_locator.get_cell(left=i, top='Discharge Date'),
                gate_out_date=table_locator.get_cell(left=i, top='Gate Out Date'),
                last_free_day=last_free_day_val,
            )

    @staticmethod
    def _is_container_no_invalid(response: Selector) -> bool:
        return bool(response.css('div.error-messages'))


class GlobalLeftTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = []  # title : td

    def parse(self, table: Selector, numbers: int):
        titles_ths = table.css('th')
        titles = []
        for title in titles_ths:
            titles.append(' '.join(title.css('::text').extract()))

        trs = table.css('tr')
        for tr in trs:
            data_tds = tr.css('td a::text').getall() + tr.css('td::text').getall()
            data_tds = [td.strip() for td in data_tds]

            if len(data_tds) < len(titles):
                continue

            row = {}
            for title_index, title in enumerate(titles):
                row[title] = data_tds[title_index]
            self._td_map.append(row)

    def get_cell(self, left, top=None) -> Selector:
        try:
            return self._td_map[left][top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

import dataclasses
from typing import List, Dict, Tuple, Union

from scrapy import Request, Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, ContainerStatusItem, ContainerItem, VesselItem, DebugItem)
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.extractors.table_cell_extractors import FirstTextTdExtractor, BaseTableCellExtractor
from crawler.extractors.table_extractors import TopHeaderTableLocator, TableExtractor


class CarrierZimuSpider(BaseCarrierSpider):
    name = 'carrier_zimu'

    def __init__(self, *args, **kwargs):
        super(CarrierZimuSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        routing_request = MainInfoRoutingRule.build_routing_request(mbl_no=self.mbl_no)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RoutingRequest):
                yield self._rule_manager.build_request_by(routing_request=result)
            else:
                raise RuntimeError()


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
    name = 'MAIN_INFO'

    @classmethod
    def build_routing_request(cls, mbl_no) -> RoutingRequest:
        url = f'https://www.zim.com/tools/track-a-shipment?consnumber={mbl_no}'
        request = Request(url=url)
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        self._check_mbl_no(response=response)

        main_info = self._extract_main_info(response=response)

        raw_vessel_list = self._extract_vessel_list(response=response)
        raw_schedule_list = self._extract_schedule_list(response=response)

        vessel_list = self._arrange_vessel_list(raw_vessel_list)

        schedule_list = self._arrange_schedule_list(
            raw_schedule_list, pol=main_info['pol'], etd=main_info['etd'], pod=main_info['pod'], eta=main_info['eta'],
        )

        if len(vessel_list) >= len(schedule_list):
            raise CarrierResponseFormatError(
                reason=f'vessel_list: `{vessel_list}`, schedule_list: `{schedule_list}`')

        for vessel_index, vessel in enumerate(vessel_list):
            departure_info = schedule_list[vessel_index]
            arrival_info = schedule_list[vessel_index + 1]

            yield VesselItem(
                vessel_key=vessel_index,
                vessel=vessel.vessel,
                voyage=vessel.voyage,
                pol=LocationItem(name=departure_info.port_name),
                pod=LocationItem(name=arrival_info.port_name),
                etd=departure_info.etd or None,
                eta=arrival_info.eta or None,
            )

        to_pod_vessel = self._find_to_pod_vessel(vessel_list, schedule_list)

        final_dest = main_info['final_dest']
        if not final_dest:
            final_dest_un_lo_code = None
            final_dest_name = None
        elif len(final_dest) == 5:
            final_dest_un_lo_code = final_dest
            final_dest_name = None
        else:
            final_dest_un_lo_code = None
            final_dest_name = final_dest

        yield MblItem(
            mbl_no=main_info['mbl_no'],
            vessel=to_pod_vessel.vessel,
            voyage=to_pod_vessel.voyage,
            por=LocationItem(name=main_info['por']),
            pol=LocationItem(name=main_info['pol']),
            pod=LocationItem(name=main_info['pod']),
            final_dest=LocationItem(un_lo_code=final_dest_un_lo_code, name=final_dest_name),
            etd=main_info['etd'] or None,
            eta=main_info['eta'] or None,
            deliv_eta=main_info['deliv_eta'] or None,
        )

        container_no_list = self._extract_container_no_list(response=response)
        for container_no in container_no_list:
            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            container_status_list = self._extract_container_status_list(response=response, container_no=container_no)
            for container_status in container_status_list:
                yield ContainerStatusItem(
                    container_key=container_no,
                    description=container_status['description'],
                    local_date_time=container_status['local_time'],
                    location=LocationItem(name=container_status['location']),
                )

    @staticmethod
    def _check_mbl_no(response):
        no_result_information = response.css('section#noResult p')
        if no_result_information:
            raise CarrierInvalidMblNoError()

        wrong_format_message = response.css('span.field-validation-error')
        if wrong_format_message:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_main_info(response: Selector):
        mbl_no = response.css('dl.dl-inline dd::text').get()

        pod_dl = response.xpath("//dl[@class='dlist']/*[text()='POD']/..")
        if pod_dl:
            pod_info = dict(extract_dl(dl=pod_dl))
        else:
            pod_info = {
                'Arrival Date': '',
            }

        routing_schedule_dl_list = response.css('dl.dl-list')
        routing_schedule_list = []
        for routing_schedule_dl in routing_schedule_dl_list:
            routing_schedule_info = extract_dl(dl=routing_schedule_dl)
            routing_schedule_list.extend(routing_schedule_info)
        routing_schedule = dict(routing_schedule_list)

        if 'Final Destination:' in routing_schedule:
            final_dest = routing_schedule['Final Destination:'].strip()
            deliv_eta = response.css('dt#etaDate::text').get() or ''
            eta = pod_info['Arrival Date']
        else:
            final_dest = ''
            deliv_eta = ''
            eta = response.css('dt#etaDate::text').get() or ''

        return {
            'mbl_no': mbl_no.strip(),
            'por': routing_schedule.get('Place of Receipt (POR)') or None,
            'pol': routing_schedule['Port of Loading (POL)'].strip(),
            'pod': routing_schedule['Port of Discharge (POD)'].strip(),
            'final_dest': final_dest,
            'deliv_eta': deliv_eta.strip(),
            'etd': routing_schedule['Sailing Date'].strip(),
            'eta': eta.strip(),
        }

    @staticmethod
    def _extract_vessel_list(response) -> List[Dict]:
        vessel_list = []

        vessel_td_list = response.css('table.progress-info tr.bottom-row td')
        for vessel_td in vessel_td_list:
            if vessel_td.css('::attr(class)') == 'hidden':
                continue

            vessel_dl = vessel_td.css('dl')
            if not vessel_dl:
                vessel = {}
            else:
                vessel = dict(extract_dl(dl=vessel_dl))
            vessel_list.append(vessel)

        return vessel_list

    @staticmethod
    def _extract_schedule_list(response) -> List[Dict]:
        schedule_list = []

        schedule_td_list = response.css('table.progress-info tr.top-row td')
        for schedule_td in schedule_td_list:
            schedule_dl = schedule_td.css('dl')
            if not schedule_dl:
                schedule = {}
            else:
                may_empty_schedule = dict(extract_dl(dl=schedule_dl))
                schedule = {} if '' in may_empty_schedule else may_empty_schedule
            schedule_list.append(schedule)

        return schedule_list

    @staticmethod
    def _arrange_vessel_list(raw_vessel_list) -> List[VesselInfo]:
        vessel_list = []
        for raw_vessel in raw_vessel_list:
            if not raw_vessel:
                continue

            vessel_name, voyage = raw_vessel['Vessel / Voyage'].split('/', 1)
            vessel_list.append(VesselInfo(vessel=vessel_name, voyage=voyage))

        return vessel_list

    @staticmethod
    def _arrange_schedule_list(schedule_list, pol, etd, pod, eta) -> List[ScheduleInfo]:
        result = [
            ScheduleInfo(port_type='POL', port_name=pol, eta='', etd=etd),  # POL
        ]
        for schedule in schedule_list:
            if not schedule:
                continue

            elif 'Transshipment' in schedule:
                result.append(ScheduleInfo(
                    port_type='Transshipment',
                    port_name=schedule['Transshipment'],
                    eta=schedule.get('Arrival Date', ''),
                    etd=schedule.get('Sailing Date', ''),
                ))

            elif 'POD' in schedule:
                result.append(ScheduleInfo(
                    port_type='POD',
                    port_name=schedule['POD'],
                    eta=schedule['Arrival Date'],
                    etd='',
                ))

            elif 'POL' in schedule:
                pass

            else:
                raise CarrierResponseFormatError(reason=f'Unknown port type of schedule: `{schedule}`')

        # add POD ?
        last_schedule = result[-1]
        if last_schedule.port_type != 'POD':
            result.append(ScheduleInfo(
                port_type='POD',
                port_name=pod,
                eta=eta,
                etd='',
            ))

        return result

    @staticmethod
    def _find_to_pod_vessel(vessel_list, schedule_list) -> VesselInfo:
        last_schedule_info = schedule_list[-1]
        assert last_schedule_info.port_type == 'POD'

        is_last_vessel_to_pod = len(schedule_list) == (len(vessel_list) + 1)

        if is_last_vessel_to_pod:
            return vessel_list[-1]
        else:
            return VesselInfo(vessel=None, voyage=None)

    @staticmethod
    def _extract_container_no_list(response) -> List[str]:
        container_no_not_strip_list = response.css('div.opener h3::text').getall()
        container_no_list = []

        for container_no_not_strip in container_no_not_strip_list:
            container_no_list.append(container_no_not_strip.strip())
        return container_no_list

    @staticmethod
    def _extract_container_status_list(response, container_no) -> List[Dict]:
        table_css_query = f"div[data-cont-id='{container_no} '] + div.slide table"
        table_selector = response.css(table_css_query)

        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table_extractor = TableExtractor(table_locator=table_locator)
        first_text_td_extractor = FirstTextTdExtractor()

        container_status_list = []
        for left in table_locator.iter_left_header():
            container_status_list.append({
                'description': table_extractor.extract_cell(
                    top='Activity', left=left, extractor=first_text_td_extractor),
                'location': table_extractor.extract_cell(
                    top='Location', left=left, extractor=first_text_td_extractor),
                'local_time': table_extractor.extract_cell(
                    top='Local Date & Time', left=left, extractor=first_text_td_extractor),
            })

        return container_status_list


# ------------------------------------------------------------------------


class AllTextCellExtractor(BaseTableCellExtractor):

    def __init__(self, css_query: str = '::text'):
        self.css_query = css_query

    def extract(self, cell: Selector):
        text_not_strip_list = cell.css(self.css_query).getall()
        text_list = [text.strip() for text in text_not_strip_list if isinstance(text, str)]
        return ' '.join(text_list)


# ------------------------------------------------------------------------


def extract_dl(dl: Selector, dt_extractor=None, dd_extractor=None) -> List[Tuple[str, str]]:
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

    dt_list = dl.css('dt')
    dl_info_list = []

    for dt_index, dt in enumerate(dt_list):
        dd = dt.xpath('following-sibling::dd[1]')

        dt_text = dt_extractor.extract(dt)
        dd_text = dd_extractor.extract(dd)
        dl_info_list.append((dt_text, dd_text))

    return dl_info_list

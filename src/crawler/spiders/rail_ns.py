import random
import time
from typing import List

import scrapy

from crawler.core_rail.base_spiders import BaseMultiRailSpider
from crawler.core_rail.exceptions import RailResponseFormatError, DriverMaxRetryError
from crawler.core_rail.items import BaseRailItem, RailItem, DebugItem, InvalidContainerNoItem
from crawler.core_rail.request_helpers import RequestOption
from crawler.core_rail.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = 'https://accessns.nscorp.com'
MAX_RETRY_COUNT = 3


class Restart:
    pass


class RailNSSpider(BaseMultiRailSpider):
    name = 'rail_usns'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._retry_count = 0

    def start(self):
        yield self._prepare_restart()

    def _prepare_restart(self):
        if self._retry_count > MAX_RETRY_COUNT:
            raise DriverMaxRetryError()

        self._retry_count += 1

        uni_container_nos = list(self.cno_tid_map.keys())
        option = ContainerRoutingRule.build_request_option(container_nos=uni_container_nos)
        return self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, RailItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result['container_no']
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result['task_id'] = t_id
                    yield result
            elif isinstance(result, BaseRailItem):
                yield result
            elif isinstance(result, Restart):
                yield self._prepare_restart()
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_RAIL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
            )

        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )

        else:
            raise KeyError()


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    ERROR_BTN_XPATH = '/html/body/div[16]/div[2]/div[2]/div/div/a[1]'
    ERROR_P_XPATH = '/html/body/div[16]/div[2]/div[1]/div/div/div[1]/div/div/div[2]/div/div/div[1]/p'

    @classmethod
    def build_request_option(cls, container_nos) -> RequestOption:
        url = 'https://www.google.com'

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={'container_nos': container_nos},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_nos = response.meta['container_nos']
        event_code_mapper = EventCodeMapper()
        content_getter = ContentGetter()
        try:
            response_text = content_getter.search(container_nos=container_nos)
        except StaleElementReferenceException:
            yield Restart()
            return
        response = scrapy.Selector(text=response_text)

        invalid_container_nos = []
        if self._is_some_container_nos_invalid(response=response):
            invalid_container_nos = self._extract_invalid_container_nos(response=response)
            for cno in invalid_container_nos:
                yield InvalidContainerNoItem(container_no=cno)

        container_infos = self._extract_container_infos(response=response)
        for valid_c_no in set(container_nos) - set(invalid_container_nos):
            valid_c_no_without_check_code = valid_c_no[:-1]
            c_no_info = container_infos.get(valid_c_no_without_check_code)
            if c_no_info is None:
                continue

            yield RailItem(
                container_no=valid_c_no,
                last_event_date=c_no_info['last_event_date'],
                origin_location=c_no_info['origin'],
                final_destination=c_no_info['destination'],
                current_location=c_no_info['current_location'],
                description=event_code_mapper.get_event_description(c_no_info['event_code']),
                eta=c_no_info['eta'],
            )

    @staticmethod
    def _extract_container_infos(response: scrapy.Selector):
        table_locator = DivTopHeaderTableLocator()
        table_locator.parse(table=response)
        table_extractor = TableExtractor(table_locator=table_locator)

        container_info = {}
        for left in table_locator.iter_left_header():
            raw_container_no = table_extractor.extract_cell(top='Equipment Id', left=left)
            container_no = raw_container_no.replace(' ', '')

            container_info[container_no] = {
                'current_location': table_extractor.extract_cell(top='Current Location', left=left),
                'last_event_date': table_extractor.extract_cell(top='Last Event Date & Time', left=left),
                'event_code': table_extractor.extract_cell(top='Event Code', left=left),
                'origin': table_extractor.extract_cell(top='Origin', left=left),
                'destination': table_extractor.extract_cell(top='Destination', left=left),
                'eta': table_extractor.extract_cell(top='ETA/I', left=left),
            }

        return container_info

    def _is_some_container_nos_invalid(self, response: scrapy.Selector) -> bool:
        error_btn = response.xpath(self.ERROR_BTN_XPATH)

        return bool(error_btn)

    def _extract_invalid_container_nos(self, response: scrapy.Selector) -> List:
        error_p = response.xpath(self.ERROR_P_XPATH)
        if not error_p:
            raise RailResponseFormatError(reason=f'xpath: `{self.ERROR_P_XPATH}` can\'t find error text')

        raw_invalid_container_nos = error_p.css('::text').get_all()[1:-1]  # 0: title, -1: space
        invalid_container_nos = [cno.replace(' ', '') for cno in raw_invalid_container_nos]

        return invalid_container_nos


class ContentGetter:
    USER_NAME = 'hvv26'
    PASS_WORD = 'gofrt123'

    def __init__(self):

        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument(f'user-agent={self._random_choose_user_agent()}')
        self._driver = webdriver.Firefox(firefox_options=options)

        # options = webdriver.ChromeOptions()
        # options.add_argument('--disable-extensions')
        # options.add_argument('--disable-notifications')
        # options.add_argument('--headless')
        # options.add_argument("--enable-javascript")
        # options.add_argument('--disable-gpu')
        # options.add_argument(
        #     f'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
        #     f'Chrome/88.0.4324.96 Safari/537.36'
        # )
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-blink-features=AutomationControlled')
        # options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # options.add_experimental_option('useAutomationExtension', False)
        #
        # self._driver = webdriver.Chrome(options=options)
        self._driver.get('https://accessns.nscorp.com/accessNS/nextgen/#loginwithcredentials')
        self._is_first = True

    @staticmethod
    def _random_choose_user_agent():
        user_agents = [
            # firefox
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) ' 'Gecko/20100101 ' 'Firefox/80.0'),
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) ' 'Gecko/20100101 ' 'Firefox/79.0'),
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) ' 'Gecko/20100101 ' 'Firefox/78.0'),
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0.1) ' 'Gecko/20100101 ' 'Firefox/78.0.1'),
        ]

        return random.choice(user_agents)

    def _login(self):
        time.sleep(60)
        username_input = self._driver.find_element_by_xpath('//*[@id="textfield-1016-inputEl"]')
        password_input = self._driver.find_element_by_xpath('//*[@id="textfield-1017-inputEl"]')
        username_input.send_keys(self.USER_NAME)
        password_input.send_keys(self.PASS_WORD)

        time.sleep(random.randint(2, 4))
        login_btn = self._driver.find_element_by_id('button-1019')
        login_btn.click()
        time.sleep(60)

    def search(self, container_nos):
        if self._is_first:
            self._login()
            self._is_first = False

        # search
        WebDriverWait(self._driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.x-panel-header')))
        self._driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        search_input = self._driver.find_element_by_css_selector('textarea[placeholder]')
        # search_btn = self._driver.find_element_by_xpath('//*[@id="button-1429-btnInnerEl"]')
        search_btn = self._driver.find_element_by_css_selector('a.x-btn.ns-button__action.x-box-item')

        search_input.send_keys('\n'.join(container_nos))
        time.sleep(random.randint(3, 5))
        search_btn.click()

        # wait for result
        time.sleep(5)

        # try:
        #     result_btn = self._driver.find_element_by_xpath('//*[@id="button-1005"]')
        #     result_btn.click()
        # except NoSuchElementException:
        #     pass
        # time.sleep(10)
        # # close result and clean search bar
        # close_btn = self._driver.find_element_by_css_selector('div[data-qtip="Close dialog"]')
        # close_btn.click()
        # search_input.clear()

        return self._driver.page_source

    def quit(self):
        self._driver.quit()


class DivTopHeaderTableLocator(BaseTableLocator):
    TITLE_OUTER_DIV_XPATH = '/html/body/div[14]/div[2]/div/div[1]/div/div[2]/div/div'
    CONTENT_OUTER_DIV_XPATH = '/html/body/div[14]/div[2]/div/div[1]/div/div[3]'

    def __init__(self):
        self._td_map = {}  # top_header: [td, td, ...]

    def parse(self, table: scrapy.Selector):
        title_outer_div = table.xpath(self.TITLE_OUTER_DIV_XPATH)
        title_divs = title_outer_div.xpath('./div')
        titles = []
        for div_i, div in enumerate(title_divs):
            if div_i == 1:
                title = div.css('span span::text').get()
            else:
                title = div.css('span::text').get()

            titles.append(title)

        content_outer_div = table.xpath(self.CONTENT_OUTER_DIV_XPATH)
        trs = content_outer_div.css('table tr')
        for tr in trs:
            tds = tr.css('td')

            for data_id, td in enumerate(tds):
                title_id = data_id
                title = titles[title_id]

                self._td_map.setdefault(title, [])
                self._td_map[title].append(td)

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except (IndexError, KeyError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (left is None) and (top in self._td_map)

    def iter_left_header(self):
        first_title = list(self._td_map.keys())[0]
        content_len = len(self._td_map[first_title])

        for i in range(content_len):
            yield i


class EventCodeMapper:
    def __init__(self):
        self.event_map = {
            'ABNO': 'ARRIVED BUT NOT ORDERED',
            'ADRI': 'PULLED FROM THE CUSTOMER',
            'AETA': 'ADVANCED ETA',
            'AETI': 'ETA AT INTERCHANGE POINT',
            'AINV': 'INVENTORY MOVE (AAR USE ONLY)',
            'ARIL': 'ARRIVAL AT INTRANSIT LOCATION',
            'ARRI': 'ARRIVAL AT FINAL DESTINATION',
            'AVPL': 'AVAILABLE FOR PLACEMENT',
            'BADO': 'BAD ORDER',
            'BFRM': 'BAD ORDER FROM',
            'BHVY': 'BAD ORDER HEAVY-TO-REPAIR',
            'BLGT': 'BAD ORDER LIGHT-TO-REPAIR',
            'BOGD': 'BAD ORDER (SIMS)',
            'BOHR': 'BAD ORDER HOURS-TO-REPAIR',
            'BOLA': 'BILL OF LADING ENTERED BY SIMS',
            'BOLP': 'PHYSICAL BILL CREATED AT DEST',
            'BXNG': 'BOUNDARY CROSSING',
            'CGIP': 'CAR GRADE BY INSPECTION',
            'CGRD': 'CAR GRADE BY WAYBILL (AAR)',
            'CH80': 'CH RULE 5 TERMINAL SWITCH',
            'CH81': 'CH RULE 5-INTERMEDIAT SWITCH',
            'CH82': 'CH RULE 15 TO DELINQUENT RD',
            'CH83': 'CH RULE 15- TO HOLDING RD',
            'CH84': 'CH RULE 5-INTERM FOLLOW INTERM',
            'CH85': 'CH RULE 5-TERM FOLLOW INTERM',
            'CONF': 'CONFIRMATION OF NOTIFICATION',
            'CPRQ': 'REQUEST FOR CONSTRUCTIVE PLACE',
            'DAMG': 'DAMAGE TO EQUIP WAS REPORTED',
            'DCHG': 'DATA CHANGE TO BOL',
            'DFLC': 'DEPARTED FROM LOCATION',
            'DLCM': 'OUTGATE FOR CO-MATERIAL XFER',
            'DLEL': 'OUTGATE EMPTY FOR LOAD SHIFT',
            'DLFR': 'OUTGATED FOR RETIREMENT',
            'DLLL': 'LIVE LIFT OUTGATE',
            'DLLS': 'OUTGATE LOAD FOR LOAD SHIFT',
            'DLLT': 'OUTGATE LOAD FOR LOT TRANSFER',
            'DLNR': 'OUTGATE FOR NON-REVENUE LOAD',
            'DLOF': 'OUTGATE FOR RETURN',
            'DLOV': 'OUTGATE FOR OVER THE ROAD',
            'DLRP': 'OUTGATE FOR REPAIR',
            'DLTA': 'OUTGATE FOR TURNAROUND',
            'DLTN': 'OUTGATE FOR TERMINATION',
            'DPAC': 'DEMURRAGE PLACE',
            'DPUL': 'DEMURRAGE PULL',
            'DRMP': 'DERAMPED',
            'DUMP': 'COAL DUMP MOVE (TYES EVENT)',
            'ECHG': 'EQUIPMENT CHANGE ON BOL',
            'EMAV': 'EMPTY AVAILABLE FOR USE',
            'EMDV': 'EMPTY AVAILABLE FOR USE-GRD D',
            'ENRT': 'ENROUTE',
            'EQPP': 'EQUIPMENT POSITION REPORT',
            'ERPO': 'END REPOSITION OF EMPTY EQUIP',
            'EWIP': 'EARLY WARNING INSPECTION',
            'EWLT': 'EARLY WARNING LETTER--AAR ONLY',
            'FADD': 'INVENTORY FORCE ADD',
            'FDEL': 'INVENTORY FORCE DEL',
            'FMVE': 'INVENTORY FORCE MOVE',
            'FRTK': 'FROM REPAIR TRACK',
            'HADR': 'HWY DEPART FROM RR FAC TO CUST',
            'HHAR': 'HWY ARRIVAL AT RR FAC FROM CUS',
            'HIGT': 'INTERMODAL IN-GATE INTERMEDIAT',
            'HLCK': 'HITCH LOCK CHECK',
            'HMIS': 'TO HOLD, DELAYED, MISC',
            'HOGT': 'INTERMODAL OUT-GATE INTERMEDIA',
            'HOLD': 'HOLD ORDERS PLACED ON EQUIPMNT',
            'ICHD': 'INTERCHANGE DELIVERY',
            'ICHG': 'INTERCHANGE',
            'ICHR': 'INTERCHANGE RECEIPT',
            'ICHV': 'INTERCHANGE RECORD VERIFIED',
            'ILFC': 'INTERMEDIATE LOAD ON FLATCAR',
            'INSP': 'REEFER WAS INSPECTED',
            'IRFC': 'INTERMEDIATE REMOVE FROM CAR',
            'LASN': 'LOCOMOTIVE ASSIGNED TO TRAIN',
            'LCOM': 'LAST COMMODITY',
            'LDCH': 'CONTAINER ATTACHED TO CHASSIS',
            'LDFC': 'LOADED ON FLAT CAR',
            'LDSF': 'LOAD SHIFTED FROM',
            'LDST': 'LOAD SHIFTED TO',
            'LINE': 'RELEASE TRAILER FOR CASH',
            'LTCK': 'LOT INVENTORY COMPLETED',
            'LUSN': 'LOCOMOTIVE UNASSIGNED FROM TRN',
            'MAWY': 'MOVE AWAY',
            'MNOT': 'SHIPMENT CHANGE, RENOTIFY',
            'MRLS': 'MECH RLSE TO TRANSP FOR MVMNT',
            'MURL': 'MECH UN-RLSE TO TRANSP',
            'NCHG': 'SHIPMENT NOTIFICATION CHANGE',
            'NOBL': 'NO BILL AT LOCATION',
            'NOCU': 'NOTIFIED CUSTOMS',
            'ΝΟΡΑ': 'NOTIFY PATRON -- EQUIP AVAIL',
            'NOTE': 'NOTIFIED VIA EDI',
            'NOTF': 'NOTIFIED VIA FAX',
            'NOTV': 'NOTIFIED VIA VOICE',
            'NTFY': 'USER GENERATED CUSTOMER NOTIFY',
            'OPRO': 'PLACE REQUEST (CSAO)',
            'ORPL': 'ORDERED FOR PLACEMENT',
            'OSTH': 'FROM STORAGE,HOLD, DELAYED,MISC',
            'PACT': 'PLACEMENT - ACTUAL',
            'PCON': 'PLACEMENT CONSTRUCTIVE',
            'PFLT': 'PULL FROM LEASED TRACK',
            'PFPS': 'CAR PULLED FROM PATRON SIDING',
            'PLJI': 'PLACED AT JOINT INDUSTRY',
            'PLLF': 'PLACED LOAD TO LT FOR FORWARDI',
            'PLLT': 'PLACED TO LEASED TRACK',
            'PLMC': 'PLACED AT MIXING CENTER (TYES)',
            'PLRM': 'PLACED AT PIGGYBACK FACILITY',
            'PUJI': 'PULLED FROM JOINT INDUSTRY',
            'PULL': 'PULLED FOR SHIPMENT',
            'PUMC': 'PULLED FR MIXING CENTER (TYES)',
            'PURM': 'PULLED FROM PIGGYBACK FACILITY',
            'PURQ': 'PULL REQUEST (CSAO)',
            'RAMP': 'RAMPED',
            'RCCM': 'INGATE FOR CO-MATERIAL XFER',
            'RCEL': 'INGATE EMPTY FOR LOAD SHIFT',
            'RCFR': 'INGATE FOR RETIREMENT',
            'RCIF': 'INGATE FOR EQUIPMENT RETURN',
            'RCLL': 'LIVE LIFT INGATE',
            'RCLS': 'INGATE AS RETURN FOR LOAD SHFT',
            'RCLT': 'INGATE FROM LOT TRANSFER',
            'RCNR': 'INGATE FOR NON-REVENUE SHIPMNT',
            'RCOR': 'INGATE FROM EQUIP ORININATION',
            'RCOV': 'INGATE FOR OVER THE ROAD',
            'RCRP': 'INGATE FROM REPAIR',
            'REBL': 'REBILLED/RECONSIGNED/RESPOT',
            'REJS': 'REJECTION BY SHIPPER',
            'RELC': 'RELEASED FROM CUSTOMERS',
            'RELS': 'DEMURRAGE RELEASE',
            'RFLT': 'RELEASED FROM LT FOR FORWARDI',
            'RLOD': 'RELEASE LOADED',
            'RLSE': 'RELEASE FROM RAILWAY FOR PULL',
            'RLSH': 'RELEASE HOLD',
            'RMFC': 'REMOVED FROM FLATCAR',
            'RMTY': 'RELEASE EMPTY',
            'RNOT': 'RE-NOTIFICATION',
            'RRFS': 'OWNER/POOL OP ORDERED CAR RETN',
            'RTAA': 'TRAVELNG PER AAR/ICC DIRECTIVE',
            'RTOI': 'TRAVELNG TO OWNER PER HIS INST',
            'RTPO': 'TRAVELNG TO POOL OP--HIS INST',
            'SCAN': 'AEL SCANNER REPORTING',
            'SEAL': 'SEAL APPLIED TO UNIT',
            'STEA': 'TO STORAGE - ACTUAL(346-8)',
            'STEX': 'TO STORAGE INTENDED(346-8)',
            'STPL': 'TO STORAGE PROSPECTIVE LOADING',
            'STSE': 'TO STORAGE SEASONABLE USE',
            'STSU': 'TO STORAGE SERVICEABLE SURPLUS',
            'STUN': 'TO STORAGE UNSERVICEABLE',
            'SWAP': 'SWAP CHASSIS',
            'TKMV': 'TRACK MOVE/INVENTORY MOVE',
            'TOLA': 'TRANSFER OF LIABILITY-ACCEPTED',
            'TOLD': 'TRANSFER OF LIABILITY-DECLINED',
            'TOLS': 'TRANSFER OF LIABILITY-SENT',
            'TRTK': 'TO REPAIR TRACK',
            'ULCH': 'CONTAINER REMOVED FROM CHASSIS',
            'UNKN': 'CAR ON FILE, NO MOVES REPORTED',
            'UNLD': 'AUTOMOTIVE RAMP UNLOAD EVENT',
            'UPAC': 'TYES UPDATE OF ACCOUNT ROAD',
            'UPLR': 'UNPLACE AT RAMP',
            'URLS': 'UNRELEASE FROM RAMP',
            'UTCS': 'DISPATCH REPORTING',
            'VOID': 'BILL OF LADING VOIDED',
            'WAYB': 'WAYBILL RESPONSE',
            'WAYR': 'WAYBILL RATED',
            'WCIL': 'INTERLINE WAYBILL EVENT',
            'WCLN': 'LOCAL NON-REVENUE WAYBILL EVT',
            'WCLR': 'LOCAL REVENUE WAYBILL EVENT',
            'WCMT': 'EMPTY WAYBILL EVENT',
            'WREL': 'WAYBILL RELEASE',
            'XFRI': 'TYES TRANSFER INTO INVENTORY',
            'XFRO': 'TYES TRANSFER OUT OF INVENTORY',
            'YDEN': 'YARD END (TYES -- CREW OFF)',
            'YDST': 'YARD START (TYES -- CREW ON)',
        }

    def get_event_description(self, event_code: str) -> str:
        return self.event_map.get(event_code, event_code)

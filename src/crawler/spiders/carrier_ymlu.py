import dataclasses
import io
import logging
import re
from typing import List, Tuple, Union

import scrapy
from python_anticaptcha import AnticaptchaClient, AnticaptchaException, ImageToTextTask
from scrapy import Selector

from crawler.core.proxy import HydraproxyProxyManager
from crawler.core.table import BaseTable, TableExtractor
from crawler.core_carrier.base import (
    CARRIER_RESULT_STATUS_ERROR,
    SHIPMENT_TYPE_BOOKING,
    SHIPMENT_TYPE_MBL,
)
from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import (
    AntiCaptchaError,
    CarrierResponseFormatError,
    SuspiciousOperationError,
)
from crawler.core_carrier.items import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    ExportErrorData,
    LocationItem,
    MblItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.table_cell_extractors import (
    BaseTableCellExtractor,
    FirstTextTdExtractor,
)
from crawler.extractors.table_extractors import HeaderMismatchError

BASE_URL = "https://www.yangming.com"


@dataclasses.dataclass
class HiddenFormSpec:
    view_state: str
    view_state_generator: str
    event_validation: str
    previous_page: str


@dataclasses.dataclass
class Restart:
    reason: str = ""


class CarrierYmluSpider(BaseCarrierSpider):
    name = "carrier_ymlu"

    def __init__(self, *args, **kwargs):
        super(CarrierYmluSpider, self).__init__(*args, **kwargs)
        self._cookie_jar_id = 1

        bill_rules = [
            MainPageRoutingRule(),
            CaptchaRoutingRule(),
            MainInfoRoutingRule(),
            ContainerStatusRoutingRule(),
        ]

        booking_rules = [
            MainPageRoutingRule(),
            CaptchaRoutingRule(),
            BookingInfoRoutingRule(),
            ContainerStatusRoutingRule(),
        ]

        if self.mbl_no:
            self._rule_manager = RuleManager(rules=bill_rules)
            self.search_no = self.mbl_no
            self.search_type = SHIPMENT_TYPE_MBL
        else:
            self._rule_manager = RuleManager(rules=booking_rules)
            self.search_no = self.booking_no
            self.search_type = SHIPMENT_TYPE_BOOKING

        self._proxy_manager = HydraproxyProxyManager(session="ymlu", logger=self.logger)

    def start(self):
        self._proxy_manager.renew_proxy()

        option = MainPageRoutingRule.build_request_option(search_no=self.search_no, search_type=self.search_type)
        proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        cookie_proxy_option = self.__add_cookiejar_to_request_option(proxy_option)
        yield self._build_request_by(cookie_proxy_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        if routing_rule.name != CaptchaRoutingRule.name:
            save_name = routing_rule.get_save_name(response=response)
            self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result

            elif isinstance(result, RequestOption):
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(result)
                cookie_proxy_option = self.__add_cookiejar_to_request_option(proxy_option)
                yield self._build_request_by(cookie_proxy_option)

            elif isinstance(result, Restart):
                self.logger.warning(f"----- {result.reason}, try new proxy and restart")
                self._proxy_manager.renew_proxy()
                self._cookie_jar_id += 1

                option = MainPageRoutingRule.build_request_option(
                    search_no=self.search_no, search_type=self.search_type
                )
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(option)
                cookie_proxy_option = self.__add_cookiejar_to_request_option(proxy_option)
                yield self._build_request_by(cookie_proxy_option)

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

    def __add_cookiejar_to_request_option(self, option):
        cookie_option = option.copy_and_extend_by(meta={"cookiejar": self._cookie_jar_id})
        return cookie_option


class MainPageRoutingRule(BaseRoutingRule):
    name = "MAIN_PAGE"

    @classmethod
    def build_request_option(cls, search_no: str, search_type: str) -> RequestOption:
        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=f"{BASE_URL}/e-service/Track_Trace/track_trace_cargo_tracking.aspx",
            meta={
                "search_no": search_no,
                "search_type": search_type,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        search_no = response.meta["search_no"]
        search_type = response.meta["search_type"]

        if check_ip_error(response=response):
            yield Restart(reason="IP block")

        else:
            hidden_form_spec = self._extract_hidden_form(response=response)
            cookies_str = self._extract_cookies_str(response=response)

            yield CaptchaRoutingRule.build_request_option(
                search_no=search_no,
                search_type=search_type,
                hidden_form_spec=hidden_form_spec,
                cookies=cookies_str,
            )

    @staticmethod
    def _extract_cookies_str(response) -> str:
        cookies_list = []
        for cookie in response.headers.getlist("Set-Cookie"):
            item = cookie.decode("utf-8").split(";")[0]
            cookies_list.append(item)

        cookies = ";".join(cookies_list)
        return cookies

    @staticmethod
    def _extract_hidden_form(response: scrapy.Selector) -> HiddenFormSpec:
        view_state = response.css("input#__VIEWSTATE::attr(value)").get()
        event_validation = response.css("input#__EVENTVALIDATION::attr(value)").get()
        view_state_generator = response.css("input#__VIEWSTATEGENERATOR::attr(value)").get()
        previous_page = response.css("input#__PREVIOUSPAGE::attr(value)").get()
        return HiddenFormSpec(
            view_state=view_state,
            event_validation=event_validation,
            view_state_generator=view_state_generator,
            previous_page=previous_page,
        )


class CaptchaRoutingRule(BaseRoutingRule):
    name = "CAPTCHA"

    @classmethod
    def build_request_option(
        cls, search_no: str, search_type: str, hidden_form_spec: HiddenFormSpec, cookies: str
    ) -> RequestOption:
        headers = {
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.9"
            ),
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Origin": "https://www.yangming.com",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": cookies,
        }

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=f"{BASE_URL}/e-service/schedule/CAPTCHA.ashx",
            headers=headers,
            meta={
                "search_no": search_no,
                "search_type": search_type,
                "hidden_form_spec": hidden_form_spec,
                "headers": headers,
            },
        )

    def get_save_name(self, response) -> str:
        pass

    def handle(self, response):
        search_no = response.meta["search_no"]
        search_type = response.meta["search_type"]
        hidden_form_spec = response.meta["hidden_form_spec"]
        headers = response.meta["headers"]

        captcha = self._get_captcha(response.body)

        if search_type == SHIPMENT_TYPE_MBL:
            yield MainInfoRoutingRule.build_request_option(
                mbl_no=search_no,
                hidden_form_spec=hidden_form_spec,
                captcha=captcha,
                headers=headers,
            )
        else:
            yield BookingInfoRoutingRule.build_request_option(
                booking_no=search_no,
                hidden_form_spec=hidden_form_spec,
                captcha=captcha,
                headers=headers,
            )

    @staticmethod
    def _get_captcha(captcha_code):
        try:
            api_key = "fbe73f747afc996b624e8d2a95fa0f84"
            captcha_fp = io.BytesIO(captcha_code)
            client = AnticaptchaClient(api_key)
            task = ImageToTextTask(captcha_fp)
            job = client.createTask(task)
            job.join()
            return job.get_captcha_text()
        except AnticaptchaException:
            raise AntiCaptchaError()


class BookingInfoRoutingRule(BaseRoutingRule):
    name = "BOOKING_INFO"

    @classmethod
    def build_request_option(cls, booking_no, hidden_form_spec: HiddenFormSpec, captcha, headers) -> RequestOption:
        form_data = {
            "__EVENTARGUMENT": "",
            "__EVENTTARGET": "",
            "__VIEWSTATE": hidden_form_spec.view_state,
            "__VIEWSTATEGENERATOR": hidden_form_spec.view_state_generator,
            "__VIEWSTATEENCRYPTED": "",
            "__EVENTVALIDATION": hidden_form_spec.event_validation,
            "__PREVIOUSPAGE": hidden_form_spec.previous_page,
            "ctl00$hidButtonType": "0",
            "ctl00$ContentPlaceHolder1$rdolType": "BK",
            "ctl00$ContentPlaceHolder1$num1": booking_no,
            "ctl00$ContentPlaceHolder1$txtVcode": captcha,
            "ctl00$ContentPlaceHolder1$btnTrack": "Track",
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=f"{BASE_URL}/e-service/Track_Trace/track_trace_cargo_tracking.aspx",
            headers=headers,
            form_data=form_data,
            meta={
                "headers": headers,
                "booking_no": booking_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        headers = response.meta["headers"]
        booking_no = response.meta["booking_no"]

        if check_ip_error(response=response):
            yield Restart(reason="IP block")

        else:
            if not self._search_success(response=response):
                yield Restart("Search Fail")
                return

            if self._is_mbl_no_invalid(response=response):
                yield ExportErrorData(
                    booking_no=booking_no,
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )
                return

            booking_no = self._extract_booking_no(response=response)
            basic_info = self._extract_basic_info(response=response)
            pol = basic_info["pol"]
            pod = basic_info["pod"]

            routing_schedule = self._extract_routing_schedule(response=response, pol=pol, pod=pod)
            firms_code = self._extract_firms_code(response=response)
            release_status = self._extract_release_status(response=response)

            yield MblItem(
                booking_no=booking_no,
                por=LocationItem(name=basic_info["por"]),
                pol=LocationItem(name=pol),
                pod=LocationItem(name=pod),
                place_of_deliv=LocationItem(name=basic_info["place_of_deliv"]),
                etd=routing_schedule["etd"],
                atd=routing_schedule["atd"],
                eta=routing_schedule["eta"],
                ata=routing_schedule["ata"],
                berthing_time=routing_schedule["berthing_time"],
                firms_code=firms_code,
                carrier_status=release_status["carrier_status"],
                carrier_release_date=release_status["carrier_release_date"],
                customs_release_status=release_status["customs_release_status"],
                customs_release_date=release_status["customs_release_date"],
            )

            last_free_day_dict = self._extract_last_free_day(response=response)
            container_info_list = self._extract_container_info(response=response)

            for container_info in container_info_list:
                container_no = container_info["container_no"]
                last_free_day = last_free_day_dict.get(container_no)

                yield ContainerItem(
                    container_key=container_no,
                    container_no=container_no,
                    last_free_day=last_free_day,
                    terminal=LocationItem(name=firms_code),
                )

                follow_url = container_info["follow_url"]
                yield ContainerStatusRoutingRule.build_request_option(
                    follow_url=follow_url,
                    container_no=container_no,
                    headers=headers,
                )

    @staticmethod
    def _search_success(response: Selector):
        if response.css("div#ContentPlaceHolder1_divResult"):
            return True
        logging.warning(response.text)
        return False

    @staticmethod
    def _is_mbl_no_invalid(response):
        no_data_found_selector = response.css("div#ContentPlaceHolder1_rptBLNo_divNoDataFound_0")
        style = no_data_found_selector.css("::attr(style)").get()

        if "display: none" in style:
            # Error message is hide
            return False

        # Error message is shown
        return True

    @staticmethod
    def _extract_booking_no(response: Selector):
        booking_no = response.xpath('//*[@id="ContentPlaceHolder1_rptBLNo_lblBKNo_0"]/text()').get()
        return booking_no.strip()

    @staticmethod
    def _extract_basic_info(response: Selector):
        table_selector = response.css("table#ContentPlaceHolder1_rptBLNo_gvBasicInformation_0")
        if not table_selector:
            CarrierResponseFormatError("Can not found basic info table !!!")

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

        return {
            "por": table.extract_cell(top="Receipt", extractor=span_text_td_extractor) or None,
            "pol": table.extract_cell(top="Loading", extractor=span_text_td_extractor) or None,
            "pod": table.extract_cell(top="Discharge", extractor=span_text_td_extractor) or None,
            "place_of_deliv": table.extract_cell(top="Delivery", extractor=span_text_td_extractor) or None,
        }

    @staticmethod
    def _extract_routing_schedule(response: Selector, pol: str, pod: str):
        div = response.css("div.cargo-trackbox3")
        parser = ScheduleParser(div)
        schedules = parser.parse()

        etd, atd, eta, ata = None, None, None, None
        berthing_time = None
        for place, time_status, berthing_time_str in schedules:
            if time_status in ["To Be Advised …", "To Be Advised...", None]:
                actual_time, estimate_time = None, None
            else:
                actual_time, estimate_time = MainInfoRoutingRule._parse_time_status(time_status)

            if pol.startswith(place):
                atd = actual_time
                etd = estimate_time
            elif pod.startswith(place):
                ata = actual_time
                eta = estimate_time
                berthing_time = berthing_time_str

        return {
            "etd": etd,
            "atd": atd,
            "eta": eta,
            "ata": ata,
            "berthing_time": berthing_time,
        }

    @staticmethod
    def _parse_time_status(time_status) -> Tuple[str, str]:
        """
        time_status = 'YYYY/MM/DD HH:mm (Actual/Estimated)'
        """
        patt = re.compile(r"^(?P<date_time>\d{4}/\d{2}/\d{2} \d{2}:\d{2}) [(](?P<status>Actual|Estimated)[)]$")

        m = patt.match(time_status)
        if not m:  # empty <date_time> case
            return None, None

        time, status = m.group("date_time"), m.group("status")
        actual_time = time if status == "Actual" else None
        estimated_time = time if status == "Estimated" else None

        return actual_time, estimated_time

    @staticmethod
    def _extract_container_info(response):
        table_selector = response.css("table#ContentPlaceHolder1_rptBLNo_gvLatestEvent_0")

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        a_text_td_extractor = TdExtractorFactory.build_a_text_td_extractor()
        a_href_td_extractor = TdExtractorFactory.build_a_href_extractor()

        container_info_list = []
        for left in table_locator.iter_left_header():
            container_no = table.extract_cell(top="Container No.", left=left, extractor=a_text_td_extractor)
            follow_url = table.extract_cell(top="Container No.", left=left, extractor=a_href_td_extractor)

            container_info_list.append(
                {
                    "container_no": container_no,
                    "follow_url": follow_url,
                }
            )

        return container_info_list

    @staticmethod
    def _extract_release_status(response):
        """
        case 1: 'Customs Status : (No entry filed)' or '(not yet Customs Release)' appear in page
            carrier_status_with_date = None
            custom_status = '(No entry filed)' or '(not yet Customs Release)'
        case 2: Both customs status and carrier status are not in page
            carrier_status_with_date = 'Label'
            custom_status = 'Label'
        """
        carrier_status_with_date = response.css("span#ContentPlaceHolder1_rptBLNo_lblCarrierStatus_0::text").get()
        if carrier_status_with_date in [None, "Label"]:
            carrier_status, carrier_date = None, None
        else:
            carrier_status_with_date = carrier_status_with_date.strip()
            carrier_status, carrier_date = MainInfoRoutingRule._parse_carrier_status(carrier_status_with_date)

        customs_status = response.css("span#ContentPlaceHolder1_rptBLNo_lblCustomsStatus_0::text").get()
        if customs_status == "Customs Release":
            customs_table_selector = response.css("table#ContentPlaceHolder1_rptBLNo_gvCustomsStatus_0")

            table_locator = TopHeaderIsTdTableLocator()
            table_locator.parse(table=customs_table_selector)
            table = TableExtractor(table_locator=table_locator)

            span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

            customs_date = None
            for left in table_locator.iter_left_header():
                event_code = table.extract_cell(top="Event", left=left, extractor=span_text_td_extractor)
                if event_code == "1C":
                    customs_date = table.extract_cell(top="Date/Time", left=left, extractor=span_text_td_extractor)
                    break

        elif customs_status in [None, "Label"]:
            customs_status = None
            customs_date = None
        else:  # means customs_status in ['(No entry filed)', '(not yet Customs Release)']
            customs_date = None

        return {
            "carrier_status": carrier_status,
            "carrier_release_date": carrier_date,
            "customs_release_status": customs_status,
            "customs_release_date": customs_date,
        }

    @staticmethod
    def _parse_carrier_status(carrier_status_with_date) -> Tuple[str, str]:
        """
        carrier_status_with_date = 'carrier_status YYYY/MM/DD HH:mm'
        """
        patt = re.compile(r"(?P<status>.+)\s+(?P<release_date>\d{4}/\d{2}/\d{2} \d{2}:\d{2})")

        m = patt.match(carrier_status_with_date)
        if m is None:
            raise CarrierResponseFormatError(reason=f"Carrier Status format error: `{carrier_status_with_date}`")

        status = m.group("status").strip()
        release_date = m.group("release_date").strip()
        return status, release_date

    @staticmethod
    def _extract_firms_code(response: Selector):
        # [0]WEST BASIN CONTAINER TERMINAL [1](Firms code:Y773)
        discharged_port_terminal_text = response.css("span#ContentPlaceHolder1_rptBLNo_lblDischarged_0 ::text").getall()
        if len(discharged_port_terminal_text) == 1:
            return None
        elif len(discharged_port_terminal_text) > 2:
            error_message = f"Discharged Port Terminal format error: `{discharged_port_terminal_text}`"
            raise CarrierResponseFormatError(reason=error_message)

        firms_code_text = discharged_port_terminal_text[1]
        firms_code = MainInfoRoutingRule._parse_firms_code(firms_code_text)
        return firms_code

    @staticmethod
    def _parse_firms_code(firms_code_text):
        """
        firms_code_text = '(Firms code:Y123)'
        """
        pat = re.compile(r".+:(?P<firms_code>\w{4})")

        m = pat.match(firms_code_text)
        if m:
            return m.group("firms_code")

    @staticmethod
    def _extract_last_free_day(response):
        table_selector = response.css("table#ContentPlaceHolder1_rptBLNo_gvLastFreeDate_0")
        if table_selector is None:
            return {}

        table_locator = TopHeaderThInTbodyTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

        last_free_day_dict = {}  # container_no: last_free_day
        for left in table_locator.iter_left_header():
            container_no = table.extract_cell(top="Container No.", left=left, extractor=span_text_td_extractor)

            last_free_date = None
            for top in ["Ramp Last Free Date", "Terminal Last Free Date"]:
                if table.has_header(top=top):
                    last_free_date = table.extract_cell(top=top, left=left, extractor=span_text_td_extractor)

            last_free_day_dict[container_no] = last_free_date

        return last_free_day_dict


class MainInfoRoutingRule(BaseRoutingRule):
    name = "MAIN_INFO"

    @classmethod
    def build_request_option(cls, mbl_no, hidden_form_spec: HiddenFormSpec, captcha, headers) -> RequestOption:
        form_data = {
            "__EVENTARGUMENT": "",
            "__EVENTTARGET": "",
            "__VIEWSTATE": hidden_form_spec.view_state,
            "__VIEWSTATEGENERATOR": hidden_form_spec.view_state_generator,
            "__VIEWSTATEENCRYPTED": "",
            "__EVENTVALIDATION": hidden_form_spec.event_validation,
            "__PREVIOUSPAGE": hidden_form_spec.previous_page,
            "ctl00$hidButtonType": "0",
            "ctl00$ContentPlaceHolder1$rdolType": "BL",
            "ctl00$ContentPlaceHolder1$num1": mbl_no,
            "ctl00$ContentPlaceHolder1$txtVcode": captcha,
            "ctl00$ContentPlaceHolder1$btnTrack": "Track",
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=f"{BASE_URL}/e-service/Track_Trace/track_trace_cargo_tracking.aspx",
            headers=headers,
            form_data=form_data,
            meta={
                "headers": headers,
                "mbl_no": mbl_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        headers = response.meta["headers"]
        mbl_no = response.meta["mbl_no"]

        if check_ip_error(response=response):
            yield Restart(reason="IP block")

        else:
            if not self._search_success(response=response):
                yield Restart("Search Fail")
                return

            if self._is_mbl_no_invalid(response=response):
                yield ExportErrorData(
                    mbl_no=mbl_no,
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )
                return

            mbl_no = self._extract_mbl_no(response=response)
            basic_info = self._extract_basic_info(response=response)
            pol = basic_info["pol"]
            pod = basic_info["pod"]

            routing_schedule = self._extract_routing_schedule(response=response, pol=pol, pod=pod)
            firms_code = self._extract_firms_code(response=response)
            release_status = self._extract_release_status(response=response)

            yield MblItem(
                mbl_no=mbl_no,
                por=LocationItem(name=basic_info["por"]),
                pol=LocationItem(name=pol),
                pod=LocationItem(name=pod),
                place_of_deliv=LocationItem(name=basic_info["place_of_deliv"]),
                etd=routing_schedule["etd"],
                atd=routing_schedule["atd"],
                eta=routing_schedule["eta"],
                ata=routing_schedule["ata"],
                berthing_time=routing_schedule["berthing_time"],
                firms_code=firms_code,
                carrier_status=release_status["carrier_status"],
                carrier_release_date=release_status["carrier_release_date"],
                customs_release_status=release_status["customs_release_status"],
                customs_release_date=release_status["customs_release_date"],
            )

            last_free_day_dict = self._extract_last_free_day(response=response)
            container_info_list = self._extract_container_info(response=response)

            for container_info in container_info_list:
                container_no = container_info["container_no"]
                last_free_day = last_free_day_dict.get(container_no)

                yield ContainerItem(
                    container_key=container_no,
                    container_no=container_no,
                    last_free_day=last_free_day,
                    terminal=LocationItem(name=firms_code),
                )

                follow_url = container_info["follow_url"]
                yield ContainerStatusRoutingRule.build_request_option(
                    follow_url=follow_url,
                    container_no=container_no,
                    headers=headers,
                )

    @staticmethod
    def _search_success(response: Selector):
        if response.css("div#ContentPlaceHolder1_divResult"):
            return True
        logging.warning(response.text)
        return False

    @staticmethod
    def _is_mbl_no_invalid(response):
        no_data_found_selector = response.css("div#ContentPlaceHolder1_rptBLNo_divNoDataFound_0")
        style = no_data_found_selector.css("::attr(style)").get()

        if "display: none" in style:
            # Error message is hide
            return False

        # Error message is shown
        return True

    @staticmethod
    def _extract_mbl_no(response: Selector):
        mbl_no = response.css("span#ContentPlaceHolder1_rptBLNo_lblBLNo_0::text").get()
        return mbl_no.strip()

    @staticmethod
    def _extract_basic_info(response: Selector):
        table_selector = response.css("table#ContentPlaceHolder1_rptBLNo_gvBasicInformation_0")
        if not table_selector:
            CarrierResponseFormatError("Can not found basic info table !!!")

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

        return {
            "por": table.extract_cell(top="Receipt", extractor=span_text_td_extractor) or None,
            "pol": table.extract_cell(top="Loading", extractor=span_text_td_extractor) or None,
            "pod": table.extract_cell(top="Discharge", extractor=span_text_td_extractor) or None,
            "place_of_deliv": table.extract_cell(top="Delivery", extractor=span_text_td_extractor) or None,
        }

    @staticmethod
    def _extract_routing_schedule(response: Selector, pol: str, pod: str):
        div = response.css("div.cargo-trackbox3")
        parser = ScheduleParser(div)
        schedules = parser.parse()

        etd, atd, eta, ata = None, None, None, None
        berthing_time = None
        for place, time_status, berthing_time_str in schedules:
            if time_status in ["To Be Advised …", "To Be Advised...", None]:
                actual_time, estimate_time = None, None
            else:
                actual_time, estimate_time = MainInfoRoutingRule._parse_time_status(time_status)

            if pol.startswith(place):
                atd = actual_time
                etd = estimate_time
            elif pod.startswith(place):
                ata = actual_time
                eta = estimate_time
                berthing_time = berthing_time_str

        return {
            "etd": etd,
            "atd": atd,
            "eta": eta,
            "ata": ata,
            "berthing_time": berthing_time,
        }

    @staticmethod
    def _parse_time_status(time_status) -> Tuple[str, str]:
        """
        time_status = 'YYYY/MM/DD HH:mm (Actual/Estimated)'
        """
        patt = re.compile(r"^(?P<date_time>\d{4}/\d{2}/\d{2} \d{2}:\d{2}) [(](?P<status>Actual|Estimated)[)]$")

        m = patt.match(time_status)
        if not m:  # empty <date_time> case
            return None, None

        time, status = m.group("date_time"), m.group("status")
        actual_time = time if status == "Actual" else None
        estimated_time = time if status == "Estimated" else None

        return actual_time, estimated_time

    @staticmethod
    def _extract_container_info(response):
        table_selector = response.css("table#ContentPlaceHolder1_rptBLNo_gvLatestEvent_0")

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        a_text_td_extractor = TdExtractorFactory.build_a_text_td_extractor()
        a_href_td_extractor = TdExtractorFactory.build_a_href_extractor()

        container_info_list = []
        for left in table_locator.iter_left_header():
            container_no = table.extract_cell(top="Container No.", left=left, extractor=a_text_td_extractor)
            follow_url = table.extract_cell(top="Container No.", left=left, extractor=a_href_td_extractor)

            container_info_list.append(
                {
                    "container_no": container_no,
                    "follow_url": follow_url,
                }
            )

        return container_info_list

    @staticmethod
    def _extract_release_status(response):
        """
        case 1: 'Customs Status : (No entry filed)' or '(not yet Customs Release)' appear in page
            carrier_status_with_date = None
            custom_status = '(No entry filed)' or '(not yet Customs Release)'
        case 2: Both customs status and carrier status are not in page
            carrier_status_with_date = 'Label'
            custom_status = 'Label'
        """
        carrier_status_with_date = response.css("span#ContentPlaceHolder1_rptBLNo_lblCarrierStatus_0::text").get()
        if carrier_status_with_date in [None, "Label"]:
            carrier_status, carrier_date = None, None
        else:
            carrier_status_with_date = carrier_status_with_date.strip()
            carrier_status, carrier_date = MainInfoRoutingRule._parse_carrier_status(carrier_status_with_date)

        customs_status = response.css("span#ContentPlaceHolder1_rptBLNo_lblCustomsStatus_0::text").get()
        if customs_status == "Customs Release":
            customs_table_selector = response.css("table#ContentPlaceHolder1_rptBLNo_gvCustomsStatus_0")

            table_locator = TopHeaderIsTdTableLocator()
            table_locator.parse(table=customs_table_selector)
            table = TableExtractor(table_locator=table_locator)

            span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

            customs_date = None
            for left in table_locator.iter_left_header():
                event_code = table.extract_cell(top="Event", left=left, extractor=span_text_td_extractor)
                if event_code == "1C":
                    customs_date = table.extract_cell(top="Date/Time", left=left, extractor=span_text_td_extractor)
                    break

        elif customs_status in [None, "Label"]:
            customs_status = None
            customs_date = None
        else:  # means customs_status in ['(No entry filed)', '(not yet Customs Release)']
            customs_date = None

        return {
            "carrier_status": carrier_status,
            "carrier_release_date": carrier_date,
            "customs_release_status": customs_status,
            "customs_release_date": customs_date,
        }

    @staticmethod
    def _parse_carrier_status(carrier_status_with_date) -> Tuple[str, str]:
        """
        carrier_status_with_date = 'carrier_status YYYY/MM/DD HH:mm'
        """
        patt = re.compile(r"(?P<status>.+)\s+(?P<release_date>\d{4}/\d{2}/\d{2} \d{2}:\d{2})")

        m = patt.match(carrier_status_with_date)
        if m is None:
            raise CarrierResponseFormatError(reason=f"Carrier Status format error: `{carrier_status_with_date}`")

        status = m.group("status").strip()
        release_date = m.group("release_date").strip()
        return status, release_date

    @staticmethod
    def _extract_firms_code(response: Selector):
        # [0]WEST BASIN CONTAINER TERMINAL [1](Firms code:Y773)
        discharged_port_terminal_text = response.css("span#ContentPlaceHolder1_rptBLNo_lblDischarged_0 ::text").getall()
        if len(discharged_port_terminal_text) == 1:
            return None
        elif len(discharged_port_terminal_text) > 2:
            error_message = f"Discharged Port Terminal format error: `{discharged_port_terminal_text}`"
            raise CarrierResponseFormatError(reason=error_message)

        firms_code_text = discharged_port_terminal_text[1]
        firms_code = MainInfoRoutingRule._parse_firms_code(firms_code_text)
        return firms_code

    @staticmethod
    def _parse_firms_code(firms_code_text):
        """
        firms_code_text = '(Firms code:Y123)'
        """
        pat = re.compile(r".+:(?P<firms_code>\w{4})")

        m = pat.match(firms_code_text)
        if m:
            return m.group("firms_code")

    @staticmethod
    def _extract_last_free_day(response):
        table_selector = response.css("table#ContentPlaceHolder1_rptBLNo_gvLastFreeDate_0")
        if table_selector is None:
            return {}

        table_locator = TopHeaderThInTbodyTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

        last_free_day_dict = {}  # container_no: last_free_day
        for left in table_locator.iter_left_header():
            container_no = table.extract_cell(top="Container No.", left=left, extractor=span_text_td_extractor)

            last_free_date = None
            for top in ["Ramp Last Free Date", "Terminal Last Free Date"]:
                if table.has_header(top=top):
                    last_free_date = table.extract_cell(top=top, left=left, extractor=span_text_td_extractor)

            last_free_day_dict[container_no] = last_free_date

        return last_free_day_dict


class ScheduleParser:
    LI_ROUTING_INDEX = 0
    LI_DATETIME_INDEX = 1

    def __init__(self, selector):
        self.selector = selector

    def parse(self) -> List[Tuple]:
        schedules = []

        uls = self.selector.css("ul")
        for ul in uls:
            lis = ul.css("li")
            routing = lis[self.LI_ROUTING_INDEX].css("span::text").get()
            datetime = lis[self.LI_DATETIME_INDEX].css("span::text").get()
            # datetime could be None
            berthing_time = None
            if lis[self.LI_DATETIME_INDEX].css("span > font::text").get() == "*":
                berthing_time_str = lis[self.LI_DATETIME_INDEX].css("span::text").getall()[-1].strip()
                patt = re.compile(
                    r"^Berthing time at terminal: "
                    r"(?P<berthing_time>\d{4}/\d{2}/\d{2} \d{2}:\d{2}) [(](Actual|Estimated)[)]$"
                )
                m = patt.match(berthing_time_str)
                if m:
                    berthing_time = m.group("berthing_time")

            striped_datetime = datetime.strip() if isinstance(datetime, str) else datetime
            routing_tuple = (routing.strip(), striped_datetime, berthing_time)

            schedules.append(routing_tuple)

        return schedules


class TopHeaderStartswithTableLocator(BaseTable):
    """
    +----------+----------+-----+----------+ <thead>
    | Title 1  | Title 2  | ... | Title N  | <tr> <td>
    +----------+----------+-----+----------+ <\thead>
    +----------+----------+-----+----------+ <tbody>
    | Data 1,1 | Data 2,1 | ... | Data N,1 | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,2 | Data 2,2 | ... | Data N,2 | <tr> <td>
    +----------+----------+-----+----------+
    | ...      |   ...    | ... |   ...    | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,M | Data 2,M | ... | Data N,M | <tr> <td>
    +----------+----------+-----+----------+ <\tbody>
    """

    def parse(self, table: Selector):
        title_td_list = table.css("thead td")
        data_tr_list = table.css("tbody tr")
        self._left_header_set = set(range(len(data_tr_list)))

        for title_index, title_td in enumerate(title_td_list):
            data_index = title_index

            title = title_td.css("::text").get().strip()
            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]

                self._td_map[title].append(data_td)

    def get_cell(self, top: Union[str, int] = 0, left: Union[str, int] = 0) -> Selector:
        top_header = self._get_top_header(top=top)
        left_header = left

        try:
            return self._td_map[top_header][left_header]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        try:
            self._get_top_header(top=top)
        except HeaderMismatchError:
            return False

        return left is None

    def _get_top_header(self, top):
        if top in self._td_map:
            return top

        for top_header in self._td_map:
            if top_header.startswith(top):
                return top_header

        raise HeaderMismatchError(repr(top))


# --------------------------------------------------------------------


class TopHeaderThInTbodyTableLocator(BaseTable):
    """
    +----------+----------+-----+----------+ <tbody>
    | Titie 1  | Title 2  | ... | Title N  | <tr> <th>
    +----------+----------+-----+----------+
    | Data 1,1 | Data 2,1 | ... | Data N,1 | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,2 | Data 2,2 | ... | Data N,2 | <tr> <td>
    +----------+----------+-----+----------+
    | ...      | ...      | ... | ...      |
    +----------+----------+-----+----------+
    | Data 1,M | Data 2,M | ... | Data N,M | <tr> <td>
    +----------+----------+-----+----------+ <\tbody>
    """

    TR_DATA_BEGIN = 1

    def parse(self, table: Selector):
        title_td_list = table.css("th")
        data_tr_list = table.css("tr")[self.TR_DATA_BEGIN :]
        self._left_header_set = set(range(len(data_tr_list)))

        for title_index, title_td in enumerate(title_td_list):
            data_index = title_index

            title = title_td.css("::text").get().strip()
            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]

                self._td_map[title].append(data_td)


# --------------------------------------------------------------------


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"

    @classmethod
    def build_request_option(cls, follow_url, container_no, headers) -> RequestOption:
        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=f"{BASE_URL}/e-service/Track_Trace/{follow_url}",
            headers=headers,
            meta={
                "follow_url": follow_url,
                "container_no": container_no,
            },
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta["container_no"]
        return f"{self.name}_{container_no}.html"

    def handle(self, response):
        container_no = response.meta["container_no"]

        if check_ip_error(response=response):
            yield Restart(reason="IP blocked")

        else:
            container_status_list = self._extract_container_status(response=response)
            rail = None
            for container_status in container_status_list:
                yield ContainerStatusItem(
                    container_key=container_no,
                    description=container_status["description"],
                    local_date_time=container_status["timestamp"],
                    location=LocationItem(name=container_status["location_name"]),
                    transport=container_status["transport"] or None,
                )
                if "Rail" in container_status["transport"]:
                    rail = container_status["location_name"]
            if rail:
                yield ContainerItem(
                    container_key=container_no,
                    railway=rail,
                )

    @staticmethod
    def _extract_container_status(response):
        table_selector = response.css("table#ContentPlaceHolder1_gvContainerNo")

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()
        span_all_text_td_extractor = SpanAllTextTdExtractor()

        container_stauts_list = []
        for left in table_locator.iter_left_header():
            location_name_with_eol = table.extract_cell(
                top="At Facility", left=left, extractor=span_all_text_td_extractor
            )
            location_name = location_name_with_eol.replace("\n", " ")

            container_stauts_list.append(
                {
                    "timestamp": table.extract_cell(top="Date/Time", left=left, extractor=span_text_td_extractor),
                    "description": table.extract_cell(top="Event", left=left, extractor=span_text_td_extractor),
                    "location_name": location_name,
                    "transport": table.extract_cell(top="Mode", left=left, extractor=span_all_text_td_extractor),
                }
            )

        return container_stauts_list


# --------------------------------------------------------------------


class TopHeaderIsTdTableLocator(BaseTable):
    """
    +----------+----------+-----+----------+ <thead>
    | Title 1  | Title 2  | ... | Title N  | <tr> <td>
    +----------+----------+-----+----------+ <\thead>
    +----------+----------+-----+----------+ <tbody>
    | Data 1,1 | Data 2,1 | ... | Data N,1 | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,2 | Data 2,2 | ... | Data N,2 | <tr> <td>
    +----------+----------+-----+----------+
    | ...      |   ...    | ... |   ...    | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,M | Data 2,M | ... | Data N,M | <tr> <td>
    +----------+----------+-----+----------+ <\tbody>
    """

    def parse(self, table: Selector):
        title_td_list = table.css("thead td")
        data_tr_list = table.css("tbody tr")
        self._left_header_set = set(range(len(data_tr_list)))

        for title_index, title_td in enumerate(title_td_list):
            data_index = title_index

            title = title_td.css("::text").get().strip()
            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]

                self._td_map[title].append(data_td)


# --------------------------------------------------------------------


class TdExtractorFactory:
    @staticmethod
    def build_span_text_td_extractor():
        return FirstTextTdExtractor("span::text")

    @staticmethod
    def build_a_text_td_extractor():
        return FirstTextTdExtractor("a::text")

    @staticmethod
    def build_a_href_extractor():
        return FirstTextTdExtractor("a::attr(href)")


class SpanAllTextTdExtractor(BaseTableCellExtractor):
    def __init__(self, css_query: str = "span::text"):
        self.css_query = css_query

    def extract(self, cell: Selector):
        all_text = cell.css(self.css_query).getall()
        text = " ".join(all_text)
        return text


def check_ip_error(response):
    ip_error_selector = response.css("div#divBlock")

    if ip_error_selector:
        return True

    return False

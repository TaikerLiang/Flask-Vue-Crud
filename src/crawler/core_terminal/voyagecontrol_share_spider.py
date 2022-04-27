import dataclasses
import json
import re
from typing import Dict, List

from scrapy import Request

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_FATAL
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import BaseTerminalError
from crawler.core_terminal.items import DebugItem, ExportErrorData, TerminalItem
from crawler.core_terminal.rules import BaseRoutingRule, RequestOption, RuleManager

MAX_PAGE_NUM = 5


@dataclasses.dataclass
class CompanyInfo:
    lower_short: str
    upper_short: str
    email: str
    password: str


@dataclasses.dataclass
class WarningMessage:
    msg: str


class VoyagecontrolShareSpider(BaseMultiTerminalSpider):
    name = ""
    company_info = CompanyInfo(
        lower_short="",
        upper_short="",
        email="",
        password="",
    )

    def __init__(self, *args, **kwargs):
        super(VoyagecontrolShareSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            AddContainerToTraceRoutingRule(),
            ListTracedContainerRoutingRule(),
            ContainerInquiryRoutingRule(),
            DelContainerFromTraceRoutingRule(),
            # SearchMblRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = LoginRoutingRule.build_request_option(
            container_nos=unique_container_nos, company_info=self.company_info
        )
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, ExportErrorData):
                c_no = result["container_no"]
                if c_no:
                    t_ids = self.cno_tid_map[c_no]
                    for t_id in t_ids:
                        result["task_id"] = t_id
                        yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            elif isinstance(result, WarningMessage):
                self.logger.warning(msg=result.msg)
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
        elif option.method == RequestOption.METHOD_POST_BODY:
            return Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
                method="POST",
                body=option.body,
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


# -------------------------------------------------------------------------------


class LoginRoutingRule(BaseRoutingRule):
    name = "LOGIN"

    @classmethod
    def build_request_option(cls, container_nos: List[str], company_info: CompanyInfo) -> RequestOption:
        url = f"https://{company_info.lower_short}.voyagecontrol.com/api/jwt/login/?venue={company_info.lower_short}"
        headers = {
            "Content-Type": "application/json",
        }
        form_data = {
            "email": company_info.email,
            "password": company_info.password,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers=headers,
            body=json.dumps(form_data),
            meta={
                "container_nos": container_nos,
                "company_info": company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        company_info = response.meta["company_info"]

        response_json = json.loads(response.text)
        authorization_token = response_json["token"]

        yield ListTracedContainerRoutingRule.build_request_option(
            container_nos=container_nos,
            authorization_token=authorization_token,
            company_info=company_info,
            is_first=True,
        )

        # if mbl_no:
        #     yield SearchMblRoutingRule.build_request_option(mbl_no=mbl_no, token=authorization_token)


# -------------------------------------------------------------------------------


class ListTracedContainerRoutingRule(BaseRoutingRule):
    name = "LIST_TRACED_CONTAINER"

    @classmethod
    def build_request_option(
        cls, container_nos: List[str], authorization_token: str, company_info: CompanyInfo, is_first: bool = False
    ) -> RequestOption:
        url = f"https://{company_info.lower_short}.voyagecontrol.com/lynx/container/?venue={company_info.lower_short}"
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            headers={
                "authorization": "JWT " + authorization_token,
            },
            meta={
                "is_first": is_first,
                "container_nos": container_nos,
                "authorization_token": authorization_token,
                "company_info": company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        is_first = response.meta["is_first"]
        container_nos = response.meta["container_nos"]
        authorization_token = response.meta["authorization_token"]
        company_info = response.meta["company_info"]

        response_json = json.loads(response.text)

        containers = self._get_containers_from(response_json=response_json, container_nos=container_nos[:MAX_PAGE_NUM])

        if containers:
            if is_first:
                # update existing container: delete -> add
                yield DelContainerFromTraceRoutingRule.build_request_option(
                    container_nos=container_nos,
                    authorization_token=authorization_token,
                    company_info=company_info,
                    not_finished=True,
                )

                return

            collated_containers = self._extract_container_info(containers=containers)

            for container_data in collated_containers:
                yield ContainerInquiryRoutingRule.build_request_option(
                    authorization_token=authorization_token, company_info=company_info, container_data=container_data
                )

            yield DelContainerFromTraceRoutingRule.build_request_option(
                container_nos=container_nos,
                authorization_token=authorization_token,
                company_info=company_info,
            )

            yield NextRoundRoutingRule.build_request_option(
                container_nos=container_nos, authorization_token=authorization_token, company_info=company_info
            )

        else:
            yield AddContainerToTraceRoutingRule.build_request_option(
                container_nos=container_nos,
                authorization_token=authorization_token,
                company_info=company_info,
            )

    @staticmethod
    def _get_containers_from(response_json: Dict, container_nos: List[str]):
        containers = []
        container_info = response_json["rows"]

        for info in container_info:
            if info["containerId"] in container_nos:
                containers.append(info)

        return containers

    def _extract_container_info(self, containers: List[Dict]) -> List[Dict]:
        container_info = []
        for container in containers:
            status_name = container["containerStatus"]["name"]
            container_status = self._extract_container_status(contain_container_status=status_name)

            container_info.append(
                {
                    "container_no": container["containerId"],
                    "ready_for_pick_up": container_status,
                    "appointment_date": container["status"].get("APPOINTMENT_HOLD", ""),
                    "last_free_day": container["status"].get("PORT_LFD", ""),
                    "demurrage": container["status"].get("DEMURRAGE", ""),
                    "holds": container["status"].get("HOLD_INFO", ""),
                    "cy_location": container["status"].get("LOCATIONDETAILS", ""),
                    # release information might be elsewhere(i.e. container inquiry) for fenix
                    "customs_release": container["status"].get("CUSTOMS", ""),
                    "carrier_release": container["status"].get("FREIGHT", ""),
                }
            )

        return container_info

    @staticmethod
    def _extract_container_status(contain_container_status: str):
        pattern = re.compile(r"CONTAINER_STATUS_(?P<container_status>\w+)")
        match = pattern.match(contain_container_status)

        return match.group("container_status")


class ContainerInquiryRoutingRule(BaseRoutingRule):
    name = "CONTAINER_INQUIRY"

    @classmethod
    def build_request_option(
        cls, authorization_token: str, company_info: CompanyInfo, container_data: Dict
    ) -> RequestOption:
        url = f'https://{company_info.lower_short}.voyagecontrol.com/api/bookings_inquiry/container_tracking/?param={container_data["container_no"]}&venue={company_info.lower_short}'
        headers = {
            "Content-Type": "application/json",
            "authorization": "JWT " + authorization_token,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            headers=headers,
            meta={
                "authorization_token": authorization_token,
                "dont_retry": True,
                "container_data": container_data,
                "company_info": company_info,
            },
        )

    def handle(self, response):
        container_data = response.meta["container_data"]
        data = json.loads(response.text)
        if data["data"][0]:
            data = json.loads(data["data"][0])
            if data["query-response"]["data-table"]["rows"]:
                if isinstance(data["query-response"]["data-table"]["rows"]["row"], list):
                    row = data["query-response"]["data-table"]["rows"]["row"][0]["field"]
                else:
                    row = data["query-response"]["data-table"]["rows"]["row"]["field"]

                if row[23].strip():
                    container_data["last_free_day"] = row[23].strip()

        yield TerminalItem(**container_data)


# -------------------------------------------------------------------------------


class AddContainerToTraceRoutingRule(BaseRoutingRule):
    name = "ADD_CONTAINER_TO_TRACE"

    @classmethod
    def build_request_option(
        cls, container_nos: List[str], authorization_token: str, company_info: CompanyInfo
    ) -> RequestOption:
        url = f"https://{company_info.lower_short}.voyagecontrol.com/lynx/container/ids/insert?venue={company_info.lower_short}"
        headers = {
            "Content-Type": "application/json",
            "authorization": "JWT " + authorization_token,
        }
        form_data = {
            "containerIds": container_nos[:MAX_PAGE_NUM],
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers=headers,
            body=json.dumps(form_data),
            meta={
                "container_nos": container_nos,
                "authorization_token": authorization_token,
                "dont_retry": True,
                "company_info": company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        authorization_token = response.meta["authorization_token"]
        company_info = response.meta["company_info"]

        # 200: add valid container_no into container_traced_list
        if response.status != 200:
            raise VoyagecontrolResponseStatusCodeError(
                reason=f"AddContainerToTraceRoutingRule: Unexpected status code: `{response.status}`"
            )

        yield ListTracedContainerRoutingRule.build_request_option(
            container_nos=container_nos, authorization_token=authorization_token, company_info=company_info
        )


# -------------------------------------------------------------------------------


class DelContainerFromTraceRoutingRule(BaseRoutingRule):
    name = "DEL_CONTAINER_FROM_TRACE"

    @classmethod
    def build_request_option(
        cls, container_nos: List[str], authorization_token: str, company_info: CompanyInfo, not_finished: bool = False
    ) -> RequestOption:
        url = f"https://{company_info.lower_short}.voyagecontrol.com/lynx/container/ids/delete?venue={company_info.lower_short}"
        headers = {
            "Content-Type": "application/json",
            "authorization": "JWT " + authorization_token,
        }
        form_data = {
            "containerIds": container_nos[:MAX_PAGE_NUM],
            "bookingRefs": [None],
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers=headers,
            body=json.dumps(form_data),
            meta={
                "container_nos": container_nos,
                "authorization_token": authorization_token,
                "not_finished": not_finished,
                "company_info": company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        authorization_token = response.meta["authorization_token"]
        not_finished = response.meta["not_finished"]
        company_info = response.meta["company_info"]

        if response.status != 200:
            raise VoyagecontrolResponseStatusCodeError(
                reason=f"DelContainerFromTraceRoutingRule: Unexpected status code: `{response.status}`"
            )

        if not_finished:
            yield AddContainerToTraceRoutingRule.build_request_option(
                container_nos=container_nos,
                authorization_token=authorization_token,
                company_info=company_info,
            )
        else:
            # because of parse(), need to yield empty item
            yield TerminalItem(container_no="")


# -------------------------------------------------------------------------------


# class SearchMblRoutingRule(BaseRoutingRule):
#     name = "SEARCH_MBL"

#     @classmethod
#     def build_request_option(cls, mbl_no, token, company_info: CompanyInfo) -> RequestOption:
#         url = f"https://{company_info.lower_short}.voyagecontrol.com/api/bookings_inquiry/landingbill/?param={mbl_no}&venue={company_info.lower_short}"
#         headers = {
#             "Content-Type": "application/json",
#             "authorization": "JWT " + token,
#         }

#         return RequestOption(
#             rule_name=cls.name,
#             method=RequestOption.METHOD_GET,
#             url=url,
#             headers=headers,
#             meta={
#                 "handle_httpstatus_list": [404],
#                 "mbl_no": mbl_no,
#                 "company_info": company_info,
#             },
#         )

#     def get_save_name(self, response) -> str:
#         return f"{self.name}.json"

#     def handle(self, response):
#         mbl_no = response.meta["mbl_no"]
#         company_info = response.meta["company_info"]

#         if response.status == 404:
#             # we want to log this error msg, but we don't want close spider, so we don't raise an exception.
#             yield WarningMessage(msg=f"[{self.name}] ----- handle -> mbl_no is invalid : `{mbl_no}`")
#             return

#         response_json = json.loads(response.text)

#         self.__check_format(response_json=response_json)

#         mbl_info = self.__extract_mbl_info(response_json=response_json)
#         yield TerminalItem(container="", **mbl_info)

#     @staticmethod
#     def __check_format(response_json: Dict):
#         bill_of_health = response_json["bill_of_health"]
#         data_table = response_json["bill_of_health"]["query-response"]["data-table"]

#         if len(bill_of_health) == 1 and "lineStatus" not in bill_of_health:
#             pass
#         elif len(bill_of_health) == 2 and "lineStatus" in bill_of_health:
#             pass
#         else:
#             raise TerminalResponseFormatError(reason=f"Unexpected bill_of_health format: `{bill_of_health}`")

#         if len(data_table) != 4:
#             raise TerminalResponseFormatError(reason=f"Unexpected data-table format: `{data_table}`")

#         if len(data_table["columns"]["column"]) == 12 and len(data_table["rows"]["row"]["field"]) == 12:
#             return

#         raise TerminalResponseFormatError(reason=f"Unexpected data-table format: `{data_table}`")

#     @staticmethod
#     def __extract_mbl_info(response_json: Dict) -> Dict:
#         bill_of_health = response_json["bill_of_health"]
#         data_table = bill_of_health["query-response"]["data-table"]
#         title = data_table["columns"]["column"]
#         data = data_table["rows"]["row"]["field"]

#         mbl_info_dict = {}
#         for key, value in zip(title, data):
#             mbl_info_dict[key] = value

#         line_status = None
#         if "lineStatus" in bill_of_health:
#             line_status = bill_of_health["lineStatus"].get("@id")

#         return {
#             "freight_release": line_status if line_status else "Released",
#             # hard code here, we don't find the other value.
#             "customs_release": "Released",
#             "carrier": mbl_info_dict["Line Op"],
#             "mbl_no": mbl_info_dict["BL Nbr"],
#             "voyage": mbl_info_dict["Ves. Visit"],
#         }


# --------------------------------------------------------------------


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    @classmethod
    def build_request_option(cls, container_nos, authorization_token, company_info: CompanyInfo) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={
                "container_nos": container_nos,
                "authorization_token": authorization_token,
                "company_info": company_info,
            },
        )

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        authorization_token = response.meta["authorization_token"]
        company_info = response.meta["company_info"]

        if len(container_nos) <= MAX_PAGE_NUM:
            return

        container_nos = container_nos[MAX_PAGE_NUM:]

        yield ListTracedContainerRoutingRule.build_request_option(
            container_nos=container_nos,
            authorization_token=authorization_token,
            company_info=company_info,
            is_first=True,
        )


# -------------------------------------------------------------------------------


class VoyagecontrolResponseStatusCodeError(BaseTerminalError):
    status = TERMINAL_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<status-code-error> {self.reason}")

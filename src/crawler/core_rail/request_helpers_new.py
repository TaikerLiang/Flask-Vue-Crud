from __future__ import annotations

import dataclasses
import random
import string
from logging import Logger
from typing import Dict

from w3lib.http import basic_auth_header

from crawler.core.exceptions_new import MaxRetryError


@dataclasses.dataclass
class RequestOption:
    METHOD_GET = "GET"
    METHOD_POST_FORM = "POST_FORM"
    METHOD_POST_BODY = "METHOD_POST_BODY"

    rule_name: str
    method: str
    url: str
    headers: Dict = dataclasses.field(default_factory=dict)
    cookies: Dict = dataclasses.field(default_factory=dict)
    form_data: Dict = dataclasses.field(default_factory=dict)
    body: str = ""
    meta: Dict = dataclasses.field(default_factory=dict)

    def copy_and_extend_by(self, headers=None, meta=None) -> RequestOption:
        return RequestOption(
            rule_name=self.rule_name,
            method=self.method,
            url=self.url,
            headers={
                **self.headers,
                **(headers or {}),
            },
            cookies={
                **self.cookies,
            },
            form_data={
                **self.form_data,
            },
            body=self.body,
            meta={
                **self.meta,
                **(meta or {}),
            },
        )


# -------------------------------------------------------------------------------


PROXY_GROUP_SHADER = "SHADER"
PROXY_GROUP_RESIDENTIAL = "RESIDENTIAL"


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class ProxyManager:
    PROXY_URL = "http://proxy.apify.com:8000"
    PROXY_PASSWORD = "XZTBLpciyyTCFb3378xWJbuYY"

    def __init__(self, session: str, logger: Logger):
        self._logger = logger

        self._proxy_options = [
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
        ]

        self._proxy_username = ""

    @staticmethod
    def _generate_random_string():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=20))

    def renew_proxy(self):
        if not self._proxy_options:
            raise MaxRetryError()

        option = self._proxy_options.pop(0)
        self._logger.warning(f"----- renew proxy ({len(self._proxy_options)}) {option}")

        self._proxy_username = f"groups-{option.group},session-{option.session}"

    def apply_proxy_to_request_option(self, option: RequestOption) -> RequestOption:
        return option.copy_and_extend_by(
            headers={
                "Proxy-Authorization": basic_auth_header(self._proxy_username, self.PROXY_PASSWORD),
            },
            meta={
                "proxy": self.PROXY_URL,
            },
        )

    def get_phantom_js_service_args(self):
        return [
            f"--proxy={self.PROXY_URL}",
            "--proxy-type=http",
            f"--proxy-auth={self._proxy_username}:{self.PROXY_PASSWORD}",
        ]

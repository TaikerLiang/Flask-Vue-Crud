from __future__ import annotations

import dataclasses
import random
import string
from logging import Logger
from typing import Dict

from w3lib.http import basic_auth_header

from crawler.core_carrier.exceptions import CarrierProxyMaxRetryError


@dataclasses.dataclass
class RequestOption:
    METHOD_GET = 'GET'
    METHOD_POST_FORM = 'POST_FORM'

    rule_name: str
    method: str
    url: str
    headers: Dict = dataclasses.field(default_factory=dict)
    cookies: Dict = dataclasses.field(default_factory=dict)
    form_data: Dict = dataclasses.field(default_factory=dict)
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
            meta={
                **self.meta,
                **(meta or {}),
            },
        )


# -------------------------------------------------------------------------------


class ProxyManager:
    PROXY_URL = 'proxy.apify.com:8000'
    PROXY_PASSWORD = 'XZTBLpciyyTCFb3378xWJbuYY'
    MAX_RENEW = 10

    def __init__(self, session: str, logger: Logger):
        self._session = session
        self._logger = logger

        self._proxy_username = ''
        self._renew_count = 0

    def renew_proxy(self):
        if self._renew_count > self.MAX_RENEW:
            raise CarrierProxyMaxRetryError()

        self._renew_count += 1
        self._logger.warning(f'----- renew proxy ({self._renew_count})')

        rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        self._proxy_username = f'groups-RESIDENTIAL,session-{self._session}{rand_str}'

    def apply_proxy_to_request_option(self, option: RequestOption) -> RequestOption:
        return option.copy_and_extend_by(
            headers={
                'Proxy-Authorization': basic_auth_header(self._proxy_username, self.PROXY_PASSWORD),
            },
            meta={
                'proxy': self.PROXY_URL,
            },
        )

    def get_phantom_js_service_args(self):
        return [
            f'--proxy=http://{self.PROXY_URL}',
            '--proxy-type=http',
            f'--proxy-auth={self._proxy_username}:{self.PROXY_PASSWORD}',
        ]

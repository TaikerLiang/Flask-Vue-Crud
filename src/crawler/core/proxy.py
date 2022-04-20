import abc
import dataclasses
from logging import Logger
import random
import string
from typing import Dict

from .base import PROXY_GROUP_RESIDENTIAL
from .exceptions import ProxyMaxRetryError


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

    def copy_and_extend_by(self, headers=None, meta=None):
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


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class ProxyManager:
    PROXY_DOMAIN = ""
    MAX_RETRY = 30

    def __init__(self, logger: Logger):
        self._logger = logger
        self._proxy_username = ""
        self._proxy_password = ""
        self._proxy_options = []

    @staticmethod
    def _generate_random_string():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=20))

    def apply_proxy_to_request_option(self, option: RequestOption) -> RequestOption:
        proxy_url = f"http://{self._proxy_username}:{self.PROXY_PASSWORD}@{self.PROXY_DOMAIN}"
        return option.copy_and_extend_by(meta={"proxy": proxy_url})

    def get_phantom_js_service_args(self):
        return [
            f"--proxy={self.PROXY_URL}",
            "--proxy-type=http",
            f"--proxy-auth={self._proxy_username}:{self.PROXY_PASSWORD}",
        ]

    @property
    def proxy_username(self):
        return self._proxy_username

    @property
    def proxy_password(self):
        return self._proxy_password

    @property
    def proxy_domain(self):
        return self.PROXY_DOMAIN

    @abc.abstractmethod
    def renew_proxy(self):
        pass


class ApifyProxyManager(ProxyManager):
    PROXY_DOMAIN = "proxy.apify.com:8000"
    PROXY_PASSWORD = "XZTBLpciyyTCFb3378xWJbuYY"

    def __init__(self, session: str, logger: Logger):
        super().__init__(logger)
        self._session = session
        self._retry = 0

    def renew_proxy(self):
        if self._retry > self.MAX_RETRY:
            raise ProxyMaxRetryError()

        option = self._get_new_proxy_option()
        self._logger.warning(f"----- renew proxy ({len(self._proxy_options)}) {option}")

        self._proxy_username = f"groups-{option.group},session-{option.session}"
        self._retry += 1

    def _get_new_proxy_option(self) -> ProxyOption:
        return ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{self._session}{self._generate_random_string()}")


class HydraproxyProxyManager(ProxyManager):
    PROXY_DOMAIN = "isp2.hydraproxy.com:9989"
    PROXY_OPTIONS_LIST = [
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
        ProxyOption(group="gofr13759rvuv55872", session="Aj1NJaZqWa1xS7e1"),
    ]

    def __init__(self, session: str, logger: Logger):
        super().__init__(logger)
        self._proxy_options = self.PROXY_OPTIONS_LIST

    def renew_proxy(self, allow_reset=False):
        if not self._proxy_options:
            if allow_reset:
                self._proxy_options = self.PROXY_OPTIONS_LIST
            else:
                raise ProxyMaxRetryError()

        option = random.choice(self._proxy_options)
        self._proxy_options.remove(option)
        self._logger.warning(f"----- renew proxy ({len(self._proxy_options)}) {option}")

        self._proxy_username = option.group
        self._proxy_password = option.session

    def apply_proxy_to_request_option(self, option: RequestOption) -> RequestOption:
        proxy_url = f"http://{self._proxy_username}:{self._proxy_password}@{self.PROXY_DOMAIN}"
        return option.copy_and_extend_by(meta={"proxy": proxy_url})

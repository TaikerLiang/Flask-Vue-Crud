from logging import Logger
from typing import Dict
import random
import string
import dataclasses

from .exceptions import ProxyMaxRetryError
from .base import PROXY_GROUP_RESIDENTIAL


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
            headers={**self.headers, **(headers or {}),},
            cookies={**self.cookies,},
            form_data={**self.form_data,},
            body=self.body,
            meta={**self.meta, **(meta or {}),},
        )


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class ProxyManager:
    PROXY_URL = "proxy.apify.com:8000"
    PROXY_PASSWORD = "XZTBLpciyyTCFb3378xWJbuYY"

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


class ApifyProxyManager(ProxyManager):
    PROXY_DOMAIN = "proxy.apify.com:8000"
    PROXY_PASSWORD = "XZTBLpciyyTCFb3378xWJbuYY"

    def __init__(self, session: str, logger: Logger):
        super().__init__(logger)
        self._proxy_options = [
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
            ProxyOption(group=PROXY_GROUP_RESIDENTIAL, session=f"{session}{self._generate_random_string()}"),
        ]

    def renew_proxy(self):
        if not self._proxy_options:
            raise ProxyMaxRetryError()

        option = self._proxy_options.pop(0)
        self._logger.warning(f"----- renew proxy ({len(self._proxy_options)}) {option}")

        self._proxy_username = f"groups-{option.group},session-{option.session}"


class HydraproxyProxyManager(ProxyManager):
    PROXY_DOMAIN = "isp2.hydraproxy.com:9989"

    def __init__(self, session: str, logger: Logger):
        super().__init__(logger)
        self._proxy_options = [
            ProxyOption(group="gofr13759lcdh32673", session="17r6FJjK3x8IQKP3"),
            ProxyOption(group="gofr13759qobk32672", session="WEmjH3S3iJEq1KHz"),
            ProxyOption(group="gofr13759rkwe32671", session="FwdQIHlCTlvBnOz8"),
            ProxyOption(group="gofr13759lyhe32670", session="rrr600sphho4UuqA"),
            ProxyOption(group="gofr13759wewq32669", session="ac2Ghfpl5I3cV7f2"),
            ProxyOption(group="gofr13759izgb32668", session="3Ac4f9EuD83UQhT1"),
            ProxyOption(group="gofr13759dlld32667", session="XpIjRLF7ZNzl4YaP"),
            ProxyOption(group="gofr13759xtkt32666", session="3ASdrSZqW96WEIdX"),
            ProxyOption(group="gofr13759xsfv32656", session="IRESQtdTKshvmQUU"),
            ProxyOption(group="gofr13759arzb32655", session="9jx9Els7Ea8YvFCy"),
            ProxyOption(group="gofr13759drdq32360", session="ZOU1a2G3ccUG7rId"),
        ]

    def renew_proxy(self):
        if not self._proxy_options:
            raise ProxyMaxRetryError()

        option = random.choice(self._proxy_options)
        self._proxy_options.remove(option)
        self._logger.warning(f"----- renew proxy ({len(self._proxy_options)}) {option}")

        self._proxy_username = option.group
        self._proxy_password = option.session

    def apply_proxy_to_request_option(self, option: RequestOption) -> RequestOption:
        proxy_url = f"http://{self._proxy_username}:{self._proxy_password}@{self.PROXY_DOMAIN}"
        return option.copy_and_extend_by(meta={"proxy": proxy_url})

import logging
from logging import Logger
import random
import string
import dataclasses
import abc

from exceptions import ProxyMaxRetryError

PROXY_GROUP_RESIDENTIAL = "RESIDENTIAL"


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class ProxyManager:
    PROXY_DOMAIN = ""
    PROXY_PASSWORD = ""

    def __init__(self, logger: Logger):
        if logger:
            self._logger = logger
        else:
            self._logger = logging.getLogger("local-crawler")

        self._proxy_username = ""
        self._proxy_password = ""
        self._proxy_options = []

    @staticmethod
    def _generate_random_string():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=20))

    @abc.abstractmethod
    def renew_proxy(self):
        pass

    @property
    def proxy_domain(self):
        return self.PROXY_DOMAIN

    @property
    def proxy_username(self):
        return self._proxy_username

    @property
    def proxy_password(self):
        return self._proxy_password


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
        self._proxy_password = self.PROXY_PASSWORD


class HydraproxyProxyManager(ProxyManager):
    PROXY_DOMAIN = "isp2.hydraproxy.com:9989"

    def __init__(self, logger: Logger):
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
            ProxyOption(group="gofr13759yvdl36220", session="GaBpxGf6g7Z7E66B"),
            ProxyOption(group="gofr13759vvqe36219", session="Y99mI2aYysg9z7V3"),
            ProxyOption(group="gofr13759ogik36218", session="kTA62vzds7Q6OKyC"),
            ProxyOption(group="gofr13759eoay36217", session="u7mcvxFArKdlUL8G"),
            ProxyOption(group="gofr13759xoqu36225", session="pucO3Ieel00WE7Ip_country-UnitedStates"),
            ProxyOption(group="gofr13759kwam36224", session="O3WIQz1KdWh8kv4W_country-UnitedStates"),
            ProxyOption(group="gofr13759cijc36223", session="sdrBBKFJbffKT5RW_country-UnitedStates"),
            ProxyOption(group="gofr13759awmw36222", session="bwZVktukWSEeb7Lt_country-UnitedStates"),
            ProxyOption(group="gofr13759hvzv36221", session="BW0RajxUJdLB1dA6_country-UnitedStates"),
        ]

    def renew_proxy(self):
        if not self._proxy_options:
            raise ProxyMaxRetryError()

        option = random.choice(self._proxy_options)
        self._proxy_options.remove(option)
        self._logger.warning(f"----- renew proxy ({len(self._proxy_options)}) {option}")

        self._proxy_username = option.group
        self._proxy_password = option.session

from crawler.core_terminal.portsamerica_share_spider import (
    CompanyInfo,
    PortsamericaShareSpider,
)


class TerminalWbctSpider(PortsamericaShareSpider):
    code = "Y773"
    name = "terminal_wbct"
    company_info = CompanyInfo(
        upper_short="WBCT_LA",
        email="hc89scooter",
        password="25450953",
    )

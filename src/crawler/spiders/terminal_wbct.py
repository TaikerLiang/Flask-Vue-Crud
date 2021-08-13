from crawler.core_terminal.portsamerica_share_spider import (
    PortsamericaShareSpider,
    CompanyInfo,
)


class TerminalWbctSpider(PortsamericaShareSpider):
    code = "Y773"
    name = "terminal_wbct"
    company_info = CompanyInfo(
        upper_short="WBCT_LA",
        site_name="WBCT Los Angeles",
        email="hc89scooter",
        password="GoFt202108",
    )

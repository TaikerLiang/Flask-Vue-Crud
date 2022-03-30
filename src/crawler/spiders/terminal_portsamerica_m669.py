from crawler.core_terminal.portsamerica_share_spider import (
    CompanyInfo,
    PortsamericaShareSpider,
)


class TerminalWbctSpider(PortsamericaShareSpider):
    code = "M669"
    name = "terminal_tampa"
    company_info = CompanyInfo(
        upper_short="PTCT_FL",
        email="HardcoreTK",
        password="Hardc0re",
    )

from crawler.core_terminal.propassva_ptp_share_spider import (
    CompanyInfo,
    PropassvaPtpShareSpider,
)


class TerminalNewYorkContainerSpider(PropassvaPtpShareSpider):
    firms_code = "E005"
    name = "terminal_ptp_newyork_container"
    company_info = CompanyInfo(
        site_name="porttruckpass",
        username="HardcoreTK",
        password="Hardc0re",
    )

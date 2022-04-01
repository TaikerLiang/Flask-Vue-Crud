from crawler.core_terminal.propassva_ptp_share_spider import (
    CompanyInfo,
    PropassvaPtpShareSpider,
)


class TerminalPropassvaNitSpider(PropassvaPtpShareSpider):
    firms_code = "L005"
    name = "terminal_propassva_nit"
    company_info = CompanyInfo(
        site_name="propassva",
        username="tk@hardcoretech.co",
        password="Hardc0re",
    )

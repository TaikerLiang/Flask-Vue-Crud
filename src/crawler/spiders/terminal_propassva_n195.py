from crawler.core_terminal.propassva_ptp_share_spider import (
    CompanyInfo,
    PropassvaPtpShareSpider,
)


class TerminalPropassvaVigSpider(PropassvaPtpShareSpider):
    firms_code = "N195"
    name = "terminal_propassva_vig"
    company_info = CompanyInfo(
        site_name="propassva",
        username="tk@hardcoretech.co",
        password="Hardc0re",
    )

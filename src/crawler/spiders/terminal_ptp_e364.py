from crawler.core_terminal.propassva_ptp_share_spider import (
    CompanyInfo,
    PropassvaPtpShareSpider,
)


class TerminalGctBayonneSpider(PropassvaPtpShareSpider):
    firms_code = "E364"
    name = "terminal_ptp_gct_bayonne"
    company_info = CompanyInfo(
        site_name="porttruckpass",
        username="HardcoreTK",
        password="Hardc0re",
    )

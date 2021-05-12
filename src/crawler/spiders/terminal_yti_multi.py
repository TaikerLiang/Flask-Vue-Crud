from crawler.core_terminal.voyagecontrol_share_spider import (
    VoyagecontrolShareSpider,
    CompanyInfo,
)


class TerminalYtiSpider(VoyagecontrolShareSpider):
    code = "Y790"
    name = "terminal_yti_multi"
    company_info = CompanyInfo(
        lower_short="yti",
        upper_short="YTI",
        email="hard202006010@gmail.com",
        password="hardc0re",
    )

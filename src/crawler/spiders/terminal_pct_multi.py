from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalPctSpider(TideworksShareSpider):
    name = 'terminal_pct_multi'
    company_info = CompanyInfo(
        lower_short='pct',
        upper_short='PCT',
        email='m10715033@mail.ntust.edu.tw',
        password='1234567890',
    )

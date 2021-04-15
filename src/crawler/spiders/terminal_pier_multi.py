from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalPierSpider(TideworksShareSpider):
    name = 'terminal_pier_multi'
    company_info = CompanyInfo(
        lower_short='pier',
        upper_short='PA',
        email='w87818@yahoo.com.tw',
        password='1234567890',
    )

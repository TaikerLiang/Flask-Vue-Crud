from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalT18Spider(TideworksShareSpider):
    firms_code = 'X117'
    name = 'terminal_t18_multi'
    company_info = CompanyInfo(
        lower_short='t18',
        upper_short='T18',
        email='Scott.lu@gofreight.co',
        password='hardc0re',
    )

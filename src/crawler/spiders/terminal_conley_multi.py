from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalConleySpider(TideworksShareSpider):
    firms_code = 'A295'
    name = 'terminal_conley_multi'
    company_info = CompanyInfo(
        lower_short='mct',
        upper_short='MCT',
        email='tk@hardcoretech.co',
        password='Hardc0re',
    )

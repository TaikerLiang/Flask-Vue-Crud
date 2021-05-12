from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalPomtocSpider(TideworksShareSpider):
    name = 'terminal_pomtoc_multi'
    company_info = CompanyInfo(
        lower_short='pomtoc-online',
        upper_short='POM',
        email='Scott.lu@gofreight.co',
        password='hardc0re',
    )

from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalOictSpider(TideworksShareSpider):
    firms_code = 'Z985'
    name = 'terminal_oict_multi'
    company_info = CompanyInfo(
        lower_short='b58',
        upper_short='OICT',
        email='Scott.lu@gofreight.co',
        password='hardc0re',
    )

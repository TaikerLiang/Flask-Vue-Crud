from crawler.core_terminal.tti_wut_share_spider import TtiWutShareSpider, CompanyInfo


class TerminalTtiSpider(TtiWutShareSpider):
    firms_code = 'Z952'
    name = 'terminal_tti'
    company_info = CompanyInfo(
        upper_short='TTI',
        url='https://www.ttilgb.com',
        email='RLTC',
        password='Hardc0re',
    )

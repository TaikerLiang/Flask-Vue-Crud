from crawler.core_terminal.tti_wut_share_spider import TtiWutShareSpider, CompanyInfo


class TerminalWutSpider(TtiWutShareSpider):
    firms_code = 'Z705'
    name = 'terminal_wut'
    company_info = CompanyInfo(
        upper_short='WUT',
        url='http://tns.uswut.com/',
        email='RLTC',
        password='Hardc0re',
    )

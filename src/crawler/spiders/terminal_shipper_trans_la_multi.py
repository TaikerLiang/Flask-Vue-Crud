from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalShipperTransLASpider(TideworksShareSpider):
    name = 'terminal_shipper_trans_la_multi'
    company_info = CompanyInfo(
        lower_short='sta',
        upper_short='STA',
        email='Scott.lu@gofreight.co',
        password='hardc0re',
    )

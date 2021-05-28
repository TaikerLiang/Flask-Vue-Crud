from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalShipperTransOakSpider(TideworksShareSpider):
    name = 'terminal_shipper_trans_oak_multi'
    company_info = CompanyInfo(
        lower_short='sto',
        upper_short='STO',
        email='Scott.lu@gofreight.co',
        password='hardc0re',
    )

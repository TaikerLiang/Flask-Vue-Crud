from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalShipperTransCarSpider(TideworksShareSpider):
    firms = 'Z773'
    name = 'terminal_shipper_trans_car_multi'
    company_info = CompanyInfo(
        lower_short='stl',
        upper_short='STL',
        email='Scott.lu@gofreight.co',
        password='hardc0re',
    )

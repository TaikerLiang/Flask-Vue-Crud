from crawler.core_terminal.portsamerica_share_spider import PortsamericaShareSpider, CompanyInfo


class TerminalWbctSpider(PortsamericaShareSpider):
    name = 'terminal_wbct_multi'
    company_info = CompanyInfo(
        upper_short='WBCT_LA',
        site_name='WBCT Los Angeles',
        email='hc89scooter',
        password='bd19841018',
    )

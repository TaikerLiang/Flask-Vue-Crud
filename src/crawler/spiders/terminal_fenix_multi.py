from crawler.core_terminal.voyagecontrol_share_spider import VoyagecontrolShareSpider, CompanyInfo


class TerminalFenixSpider(VoyagecontrolShareSpider):
    name = 'terminal_fenix_multi'
    company_info = CompanyInfo(
        lower_short='fenixmarine',
        upper_short='FENIXMARINE',
        email='hard202006010@gmail.com',
        password='hardc0re',
    )

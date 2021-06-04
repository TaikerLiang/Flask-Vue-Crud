from crawler.core_terminal.tms_share_spider import TmsSharedSpider, CompanyInfo


class TerminalPctSpider(TmsSharedSpider):
    firms_code = 'Z693'
    name = 'terminal_tms_husky_multi'
    terminal_id = 3
    company_info = CompanyInfo(
        email='BrianLee',
        password='ZD_uSUFMy!6Nfu',
    )

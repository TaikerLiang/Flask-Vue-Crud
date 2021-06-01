from crawler.core_terminal.apm_share_spider import ApmShareSpider


class TerminalApmPESpider(ApmShareSpider):
    firms_code = 'E425'
    name = 'terminal_apm_pe_multi'
    terminal_id = 'cfc387ee-e47e-400a-80c5-85d4316f1af9'
from crawler.core_terminal.apm_share_spider import ApmShareSpider


class TerminalApmPESpider(ApmShareSpider):
    firms_code = "E425"
    name = "terminal_apm_pe"
    terminal_id = "cfc387ee-e47e-400a-80c5-85d4316f1af9"
    data_source_id = "0214600e-9b26-46c2-badd-bd4f3a295e13"

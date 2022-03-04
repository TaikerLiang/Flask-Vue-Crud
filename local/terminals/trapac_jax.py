import scrapy

from local.core import BaseLocalCrawler
from local.terminals.share.trapac import TrapacContentGetter
from src.crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from src.crawler.core_terminal.items import ExportErrorData, TerminalItem
from src.crawler.core_terminal.trapac_share_spider import MainRoutingRule


class JaxTrapacContentGetter(TrapacContentGetter):
    UPPER_SHORT = "JAX"
    LOWER_SHORT = "jacksonville"
    EMAIL = ""
    PASSWORD = ""

    def __init__(self, proxy: bool):
        super().__init__(proxy=proxy)


class JaxTrapacLocalCrawler(BaseLocalCrawler):
    code = "M029"

    def __init__(self, proxy: bool):
        super().__init__(proxy=proxy)
        self.content_getter = JaxTrapacContentGetter(proxy=proxy)

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        container_nos = container_nos.split(",")
        id_container_map = {container_no: task_id for task_id, container_no in zip(task_ids, container_nos)}

        res = self.content_getter.search_and_return(container_no_list=container_nos)
        scrapy.Selector(text=res)
        for container_info in MainRoutingRule.extract_container_result_table(
            response=scrapy.Selector(text=res), numbers=len(container_nos)
        ):
            container_no = container_info["container_no"]
            container_nos.remove(container_no)

            yield TerminalItem(  # html field
                task_id=id_container_map.get(container_info["container_no"], ""),
                container_no=container_info["container_no"],  # number
                last_free_day=container_info["last_free_day"],  # demurrage-lfd
                customs_release=container_info.get("custom_release"),  # holds-customs
                demurrage=container_info["demurrage"],  # demurrage-amt
                container_spec=container_info["container_spec"],  # dimensions
                holds=container_info["holds"],  # demurrage-hold
                gate_out_date=container_info["cy_location"],  # yard status
                vessel=container_info["vessel"],  # vsl / voy
                voyage=container_info["voyage"],  # vsl / voy
            )

        for container_no in container_nos:  # with invalid no left
            yield ExportErrorData(
                task_id=id_container_map.get(container_no, ""),
                container_no=container_no,
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )

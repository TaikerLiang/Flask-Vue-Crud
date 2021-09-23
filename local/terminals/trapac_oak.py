from typing import List

from local.terminals.share.trapac import TrapacContentGetter
from local.core import BaseLocalCrawler


class OakTrapacContentGetter(TrapacContentGetter):
    UPPER_SHORT = "OAK"
    LOWER_SHORT = "oakland"
    EMAIL = ""
    PASSWORD = ""

    def __init__(self):
        super().__init__()


class OakTrapacLocalCrawler(BaseLocalCrawler):
    code = "Y549"

    def __init__(self):
        super().__init__()
        self.content_getter = OakTrapacContentGetter()

    def start_crawler(self, mbl_no: str, booking_no: str, container_no: str):
        res = self.content_getter.search_and_return(mbl_no=mbl_no)

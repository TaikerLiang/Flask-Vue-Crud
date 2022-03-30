import logging.config
import time

import config

from src.crawler.services.edi_service import EdiClientService

logger = logging.getLogger("local-generator")

CARRIER_TASKS = [
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "219992", "mbl_no": "ZIMUTPE8201344"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "220004", "mbl_no": "ZIMUSNH1651309"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "220034", "mbl_no": "ZIMUSHH30744766"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "220035", "mbl_no": "ZIMUSHH30754994"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "220115", "mbl_no": "ZIMUSHH30736982"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "220170", "mbl_no": "ZIMUSHH30751885"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233851", "mbl_no": "ZIMUNYC998979"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233850", "mbl_no": "ZIMUNYC998416"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233824", "mbl_no": "ZIMUXIA8237146"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233770", "mbl_no": "ZIMUSNH1565371"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233729", "mbl_no": "ZIMUNGB9886166"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233728", "mbl_no": "ZIMUNGB9886389"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233678", "mbl_no": "ZIMUHKG001655671"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233674", "mbl_no": "ZIMUSNH1565369"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233577", "mbl_no": "ZIMUXIA8240119"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233485", "mbl_no": "ZIMUNGB9815921"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233422", "mbl_no": "ZIMUHCM80225099"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233416", "mbl_no": "ZIMUSHH30759067"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233276", "mbl_no": "ZIMUSHH30744848"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233275", "mbl_no": "ZIMUSHH30769362"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233274", "mbl_no": "ZIMUSHH30762577"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233252", "mbl_no": "ZIMUNGB1119782"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233205", "mbl_no": "ZIMUNGB9749159"},
    {"type": "carrier", "scac_code": "ZIMU", "task_id": "233175", "mbl_no": "ZIMUNGB1132028"},
]


TERMINAL_TASKS = [
    {"type": "terminal", "firms_code": "Y258", "task_id": "234918", "container_no": "BEAU4697246"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234919", "container_no": "TGCU0033364"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234920", "container_no": "UACU5419949"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234921", "container_no": "TCLU6958695"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234922", "container_no": "SEGU5895356"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234923", "container_no": "TWCU8035793"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234924", "container_no": "UACU5419949"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234925", "container_no": "NYKU4384665"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234926", "container_no": "KKTU7951262"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234927", "container_no": "TRHU3889360"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234930", "container_no": "TRHU3952903"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234931", "container_no": "MOAU0612730"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234932", "container_no": "NYKU4954011"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234933", "container_no": "GCXU5265073"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234934", "container_no": "TCNU6649610"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234935", "container_no": "NYKU4929282"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234936", "container_no": "CAIU7401183"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234937", "container_no": "GESU3583797"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234938", "container_no": "MTSU9663827"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234939", "container_no": "FANU3113440"},
    {"type": "terminal", "firms_code": "Y258", "task_id": "234940", "container_no": "MAGU2547291"},
]


class TaskGenerator:
    def __init__(self, mode: str, task_type: str):
        self.mode = mode
        self.task_type = task_type

    def get_local_tasks(self, num: int):
        if self.mode == "dev":
            if self.task_type == "carrier":
                return self._get_carrier_tasks(num=num)
            elif self.task_type == "terminal":
                return self._get_terminal_tasks(num=num)
            else:
                return []
        else:
            carrier_edi_client = EdiClientService(
                url=f"{config.EDI_DOMAIN}/api/tracking-carrier/local/",
                edi_user=config.EDI_USER,
                edi_token=config.EDI_TOKEN,
            )
            local_tasks = carrier_edi_client.get_local_tasks()
            logger.info(f"number of tasks: {len(local_tasks)}")
            if len(local_tasks) == 0:
                logger.warning("sleep 10 minutes")
                time.sleep(10 * 60)

            return local_tasks

    @staticmethod
    def _get_carrier_tasks(num: int):
        return CARRIER_TASKS[:num]

    @staticmethod
    def _get_terminal_tasks(num: int):
        return TERMINAL_TASKS[:num]

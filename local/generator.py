import logging.config
import time

import config

from src.crawler.services.edi_service import EdiClientService

logger = logging.getLogger("local-generator")

CARRIER_TASKS = [
    {"type": "carrier", "scac_code": "WHLC", "task_id": "277601", "mbl_no": "025B686600"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "277597", "mbl_no": "031B568849"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220034", "mbl_no": "031C516638"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220035", "mbl_no": "027C536139"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220115", "mbl_no": "034C512262"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220170", "mbl_no": "031C519830"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "277601", "mbl_no": "025B686600"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "277597", "mbl_no": "031B568849"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220034", "mbl_no": "031C516638"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220035", "mbl_no": "027C536139"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220115", "mbl_no": "034C512262"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220170", "mbl_no": "031C519830"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "277601", "mbl_no": "025B686600"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "277597", "mbl_no": "031B568849"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220034", "mbl_no": "031C516638"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220035", "mbl_no": "027C536139"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220115", "mbl_no": "034C512262"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220170", "mbl_no": "031C519830"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "277601", "mbl_no": "025B686600"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "277597", "mbl_no": "031B568849"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220034", "mbl_no": "031C516638"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220035", "mbl_no": "027C536139"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220115", "mbl_no": "034C512262"},
    {"type": "carrier", "scac_code": "WHLC", "task_id": "220170", "mbl_no": "031C519830"},
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

import time
import logging.config

from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

import config
from config import ScreenColor
from src.crawler.services.edi_service import EdiClientService
from local.helpers import CrawlerHelper
from local.defines import LocalTask
from local.core import BaseLocalCrawler
from local.services import DataHandler, TaskAggregator
from local.exceptions import AccessDeniedError, DataNotFoundError, TimeoutError
from local.utility import timeout

logger = logging.getLogger("local-crawler")


class LocalCrawler:
    def __init__(self, _type: str, crawler: BaseLocalCrawler):
        self.helper = CrawlerHelper()
        self.handler = DataHandler()
        self.type = _type
        self.crawler = crawler

    def run(self, task: LocalTask):
        items = list(
            self.crawler.start_crawler(
                task_ids=",".join(task.task_ids),
                mbl_nos=",".join(task.mbl_nos),
                booking_nos=",".join(task.booking_nos),
                container_nos=",".join(task.container_nos),
            )
        )

        init_items = self.handler.build_init_item_response(
            spider_tag=task.code,
            task_ids=",".join(task.task_ids),
            mbl_nos=",".join(task.mbl_nos),
            booking_nos=",".join(task.booking_nos),
            container_nos=",".join(task.container_nos),
        )
        # TODO: handle data was not found here (init_items)
        for resp_data in self.handler.build_response_data(_type=self.type, items=items):
            yield self.handler.update_resp_data(data=resp_data, result=init_items[resp_data["task_id"]])

    def build_error_resp(self, task_id: str, task: LocalTask, err_msg: str):
        init_items = self.handler.build_init_item_response(
            spider_tag=task.code,
            task_ids=",".join(task.task_ids),
            mbl_nos=",".join(task.mbl_nos),
            booking_nos=",".join(task.booking_nos),
            container_nos=",".join(task.container_nos),
        )

        return self.handler.update_error_message(result=init_items[task_id], err_msg=err_msg)

    def quit(self):
        self.crawler.quit()


@timeout(180, "Function slow; aborted")
def run_spider(local_crawler, edi_client, task, start_time):
    for result in local_crawler.run(task=task):
        code, resp = edi_client.send_provider_result_back(
            task_id=result["task_id"], provider_code="local", item_result=result
        )
        logger.info(
            f"{ScreenColor.SUCCESS} SUCCESS, time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids} {code}"
        )


def start():
    carrier_edi_client = EdiClientService(
        url=f"{config.EDI_DOMAIN}/api/tracking-carrier/local/", edi_user=config.EDI_USER, edi_token=config.EDI_TOKEN
    )
    local_tasks = carrier_edi_client.get_local_tasks()
    logger.info(f"number of tasks: {len(local_tasks)}")

    # local_tasks = [
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '219992', 'mbl_no': 'ZIMUTPE8201344'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '220004', 'mbl_no': 'ZIMUSNH1651309'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '220034', 'mbl_no': 'ZIMUSHH30744766'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '220035', 'mbl_no': 'ZIMUSHH30754994'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '220115', 'mbl_no': 'ZIMUSHH30736982'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '220170', 'mbl_no': 'ZIMUSHH30751885'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233851', 'mbl_no': 'ZIMUNYC998979'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233850', 'mbl_no': 'ZIMUNYC998416'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233824', 'mbl_no': 'ZIMUXIA8237146'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233770', 'mbl_no': 'ZIMUSNH1565371'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233729', 'mbl_no': 'ZIMUNGB9886166'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233728', 'mbl_no': 'ZIMUNGB9886389'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233678', 'mbl_no': 'ZIMUHKG001655671'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233674', 'mbl_no': 'ZIMUSNH1565369'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233577', 'mbl_no': 'ZIMUXIA8240119'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233485', 'mbl_no': 'ZIMUNGB9815921'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233422', 'mbl_no': 'ZIMUHCM80225099'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233416', 'mbl_no': 'ZIMUSHH30759067'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233276', 'mbl_no': 'ZIMUSHH30744848'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233275', 'mbl_no': 'ZIMUSHH30769362'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233274', 'mbl_no': 'ZIMUSHH30762577'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233252', 'mbl_no': 'ZIMUNGB1119782'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233205', 'mbl_no': 'ZIMUNGB9749159'},
    #     {'type': 'carrier', 'scac_code': 'ZIMU', 'task_id': '233175', 'mbl_no': 'ZIMUNGB1132028'},
    # ]

    if len(local_tasks) == 0:
        logger.warning(f"sleep 10 minutes")
        time.sleep(10 * 60)

    task_aggregator = TaskAggregator()
    _map = task_aggregator.aggregate_tasks(tasks=local_tasks)
    helper = CrawlerHelper()

    for key, local_tasks in _map.items():
        _type, _code = key.split("-")
        crawler = helper.get_crawler(code=_code)
        if not crawler:
            continue

        if _type == "terminal":
            url = f"{config.EDI_DOMAIN}/api/tracking-terminal/local/"
        else:
            url = f"{config.EDI_DOMAIN}/api/tracking-carrier/local/"
        edi_client = EdiClientService(url=url, edi_user=config.EDI_USER, edi_token=config.EDI_TOKEN)

        local_crawler = LocalCrawler(_type=_type, crawler=crawler)
        logger.warning(f"Browser Opened {local_crawler}")
        start_time = time.time()

        for task in local_tasks:
            try:
                run_spider(local_crawler=local_crawler, edi_client=edi_client, task=task, start_time=start_time)
            except (TimeoutException, TimeoutError):
                logger.warning(
                    f"{ScreenColor.WARNING} (TimeoutException), time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids}"
                )
                logger.warning(f"Browser Closed")
                local_crawler.quit()
                time.sleep(1)
                local_crawler = LocalCrawler(_type=_type, crawler=helper.get_crawler(code=_code))
            except (NoSuchElementException, StaleElementReferenceException):
                logger.warning(
                    f"{ScreenColor.WARNING} (NoSuchElementException, StaleElementReferenceException), time consuming: {(time.time() - start_time):.2f}, code: {task.code} task_ids: {task.task_ids}"
                )
                continue
            except AccessDeniedError:
                logger.warning(
                    f"{ScreenColor.WARNING} (AccessDeniedError), time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids}"
                )
                logger.warning(f"Browser Closed")
                local_crawler.quit()
                time.sleep(60)
                local_crawler = LocalCrawler(_type=_type, crawler=helper.get_crawler(code=_code))
            except DataNotFoundError as e:
                logger.warning(
                    f"{ScreenColor.WARNING} (DataNotFoundError), time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids}"
                )
                local_crawler.build_error_resp(task_id=e.task_id, task=task, err_msg="Data was not found")
            except Exception as e:
                logger.error(
                    f"{ScreenColor.ERROR} Unknown Exception: {str(e)}, time consuming: {(time.time() - start_time):.2f}, code: {task.code} task_ids: {task.task_ids}"
                )
                local_crawler.quit()
                time.sleep(1)
                local_crawler = LocalCrawler(_type=_type, crawler=helper.get_crawler(code=_code))
            finally:
                start_time = time.time()
                print()

        logger.warning(f"Browser Closed")
        local_crawler.quit()


if __name__ == "__main__":
    logging.config.fileConfig(fname="log.conf", disable_existing_loggers=False)
    while True:
        start()

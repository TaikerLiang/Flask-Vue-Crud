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
from local.exceptions import AccessDeniedError, DataNotFoundError

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


def start():
    # carrier_edi_client = EdiClientService(
    #     url=f"{config.EDI_DOMAIN}/api/tracking-carrier/local/", edi_user=config.EDI_USER, edi_token=config.EDI_TOKEN
    # )
    # local_tasks = carrier_edi_client.get_local_tasks()
    # logger.info(f"number of tasks: {len(local_tasks)}")

    local_tasks = [
        {"type": "carrier", "scac_code": "MSCU", "task_id": "135434", "mbl_no": "MEDUT8157140"},
        {"type": "carrier", "scac_code": "MSCU", "task_id": "135405", "mbl_no": "MEDUQ5828072"},
    ]

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
                for result in local_crawler.run(task=task):
                    code, resp = edi_client.send_provider_result_back(
                        task_id=result["task_id"], provider_code="local", item_result=result
                    )
                    logger.info(
                        f"{ScreenColor.SUCCESS} SUCCESS, time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids} {code}"
                    )
            except TimeoutException:
                logger.warning(
                    f"{ScreenColor.WARNING} (TimeoutException), time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids}"
                )
                logger.warning(f"Browser Closed")
                local_crawler.quit()
                print(f"sleeping 5 mins")
                time.sleep(5 * 60)
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
                print(f"sleeping 5 mins")
                time.sleep(5 * 60)
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

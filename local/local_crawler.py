import time
import click
import datetime
import logging.config

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

import config
from config import ScreenColor
from local.helpers import CrawlerHelper
from local.defines import LocalTask
from local.core import BaseLocalCrawler
from local.services import DataHandler, TaskAggregator
from local.exceptions import AccessDeniedError, DataNotFoundError, TimeoutError
from local.utility import timeout
from generator import TaskGenerator
from src.crawler.services.edi_service import EdiClientService

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

    def reset(self):
        self.crawler.reset()

    def quit(self):
        self.crawler.quit()


@timeout(300, "Function slow; aborted")
def run_spider(local_crawler, edi_client, task, start_time: datetime, mode: str):
    for result in local_crawler.run(task=task):
        if mode != "dev":
            code, resp = edi_client.send_provider_result_back(
                task_id=result["task_id"], provider_code="local", item_result=result
            )
            logger.info(
                f"{ScreenColor.SUCCESS} SUCCESS, time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids} response_code: {code}"
            )
        else:
            logger.info(
                f"{ScreenColor.SUCCESS} SUCCESS, time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids}"
            )


@click.command()
@click.option(
    "-m",
    "--mode",
    required=True,
    type=click.Choice(["dev", "prd"], case_sensitive=False),
    default="dev",
    show_default=True,
    help="get the tasks from",
)
@click.option(
    "-t",
    "--task_type",
    required=False,
    type=click.Choice(["carrier", "terminal", "rail"], case_sensitive=False),
    default="carrier",
    show_default=True,
    help="which type of tasks (prd mode doesn't need it)",
)
@click.option(
    "-n",
    "--num",
    required=False,
    default=20,
    type=int,
    show_default=True,
    help="how many tasks do you want to take",
)
@click.option(
    "--proxy/--no-proxy",
    default=False,
    type=bool,
    show_default=True,
    help="with proxy or not",
)
def start(mode: str, task_type: str, num: int, proxy: bool):
    task_generator = TaskGenerator(mode=mode, task_type=task_type)
    local_tasks = task_generator.get_local_tasks(num)
    task_aggregator = TaskAggregator()
    task_mapper = task_aggregator.aggregate_tasks(tasks=local_tasks)
    helper = CrawlerHelper()

    print("proxy", proxy)

    for key, local_tasks in task_mapper.items():
        _type, _code = key.split("-")
        crawler = helper.get_crawler(code=_code, proxy=proxy)
        if not crawler:
            continue

        local_crawler = LocalCrawler(_type=_type, crawler=crawler)
        start_time = time.time()
        logger.warning(f"{start_time}: Browser Opened {local_crawler}")

        for task in local_tasks:
            try:
                run_spider(
                    local_crawler=local_crawler,
                    edi_client=EdiClientService(
                        url=f"{config.EDI_DOMAIN}/api/tracking-{_type}/local/",
                        edi_user=config.EDI_USER,
                        edi_token=config.EDI_TOKEN,
                    ),
                    task=task,
                    start_time=start_time,
                    mode=mode,
                )
            except (TimeoutException, TimeoutError):
                logger.warning(
                    f"{ScreenColor.WARNING} (TimeoutException), time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids}"
                )
                logger.warning(f"Browser Closed")
                local_crawler.quit()
                time.sleep(1)
                local_crawler = LocalCrawler(_type=_type, crawler=helper.get_crawler(code=_code, proxy=True))
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
                time.sleep(1)
                local_crawler = LocalCrawler(_type=_type, crawler=helper.get_crawler(code=_code, proxy=True))
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
                local_crawler = LocalCrawler(_type=_type, crawler=helper.get_crawler(code=_code, proxy=False))
            finally:
                start_time = time.time()
                print()

        logger.warning(f"Browser Closed")
        local_crawler.quit()


if __name__ == "__main__":
    logging.config.fileConfig(fname="log.conf", disable_existing_loggers=False)
    start()

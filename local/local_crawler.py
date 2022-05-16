import datetime
import logging.config
import os
import time

import click
from config import ScreenColor
from generator import TaskGenerator
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)

from local.config import EDI_DOMAIN, EDI_TOKEN, EDI_USER
from local.exceptions import AccessDeniedError, TimeoutError
from local.helpers import CrawlerHelper
from local.services import TaskAggregator
from local.utility import timeout

logger = logging.getLogger("local-crawler")


@timeout(300, "Function slow; aborted")
def run_spider(crawler, task, start_time: datetime):
    crawler.start_crawler(
        task_ids=",".join(task.task_ids),
        mbl_nos=",".join(task.mbl_nos),
        booking_nos=",".join(task.booking_nos),
        container_nos=",".join(task.container_nos),
    )
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
def start(mode: str, task_type: str, num: int):
    task_generator = TaskGenerator(mode=mode, task_type=task_type)
    local_tasks = task_generator.get_local_tasks(num)
    task_aggregator = TaskAggregator()
    task_mapper = task_aggregator.aggregate_tasks(tasks=local_tasks)
    helper = CrawlerHelper()
    os.environ["RUNNING_AT"] = "local"
    os.environ["RUNNING_MODE"] = mode
    os.environ["SCRAPY_SETTINGS_MODULE"] = "src.crawler.settings"
    os.environ["EDI_ENGINE_USER"] = EDI_USER or ""
    os.environ["EDI_ENGINE_TOKEN"] = EDI_TOKEN or ""
    os.environ["EDI_ENGINE_BASE_URL"] = f'{EDI_DOMAIN or ""}/api/'

    for key, local_tasks in task_mapper.items():
        _type, _code = key.split("-")
        crawler = helper.get_crawler(type=_type, code=_code)
        if not crawler:
            continue

        start_time = time.time()
        logger.warning(f"{start_time}: Browser Opened {crawler}")

        for task in local_tasks:
            try:
                run_spider(
                    crawler=crawler,
                    task=task,
                    start_time=start_time,
                )
            except (TimeoutException, TimeoutError):
                logger.warning(
                    f"{ScreenColor.WARNING} (TimeoutException), time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids}"
                )
                logger.warning("Browser Closed")
                crawler.quit()
                time.sleep(1)
                crawler = helper.get_crawler(type=_type, code=_code)
            except (NoSuchElementException, StaleElementReferenceException):
                logger.warning(
                    f"{ScreenColor.WARNING} (NoSuchElementException, StaleElementReferenceException), time consuming: {(time.time() - start_time):.2f}, code: {task.code} task_ids: {task.task_ids}"
                )
            except AccessDeniedError:
                logger.warning(
                    f"{ScreenColor.WARNING} (AccessDeniedError), time consuming: {(time.time() - start_time):.2f} code: {task.code} task_ids: {task.task_ids}"
                )
                logger.warning("Browser Closed")
                crawler.quit()
                time.sleep(60 * 5)
                crawler = helper.get_crawler(type=_type, code=_code)
            except Exception as e:
                logger.error(
                    f"{ScreenColor.ERROR} Unknown Exception: {str(e)}, time consuming: {(time.time() - start_time):.2f}, code: {task.code} task_ids: {task.task_ids}"
                )
                crawler.quit()
                time.sleep(1)
                crawler = helper.get_crawler(type=_type, code=_code)
            finally:
                start_time = time.time()
                print()

        logger.warning("Browser Closed")
        crawler.quit()


if __name__ == "__main__":
    logging.config.fileConfig(fname="log.conf", disable_existing_loggers=False)
    start()

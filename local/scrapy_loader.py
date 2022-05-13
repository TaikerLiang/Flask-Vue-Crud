import concurrent.futures
import logging

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy.utils.project import get_project_settings

from local.exceptions import AccessDeniedError

logger = logging.getLogger("scrapy-loader")


class DisableLogger:
    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, exit_type, exit_value, exit_traceback):
        logging.disable(logging.NOTSET)


def get_scrapy_project_settings():
    settings = get_project_settings()
    settings.set("LOG_LEVEL", "ERROR")
    return settings


def run_scrapy_spider(
    name: str,
    task_ids: str,
    mbl_nos: str,
    booking_nos: str,
    container_nos: str,
):
    results = []

    def crawler_results(signal, sender, item, response, spider):
        if spider.has_error():
            results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_dropped)
    with DisableLogger():
        process = CrawlerProcess(get_scrapy_project_settings())
        process.crawl(name, task_ids=task_ids, mbl_nos=mbl_nos, booking_nos=booking_nos, container_nos=container_nos)
        process.start()

    if results:
        result = results[0]
        if result["detail"].startswith("AccessDeniedError"):
            raise AccessDeniedError(result["detail"])
        else:
            raise Exception(result["detail"])


class ScrapyLoader:
    def __init__(self, type: str, code: str):
        self.spider_name = f"{type}_{code}_multi".lower()
        with DisableLogger():
            CrawlerProcess(get_scrapy_project_settings()).create_crawler(self.spider_name)

    def start_crawler(
        self,
        task_ids: str,
        mbl_nos: str,
        booking_nos: str,
        container_nos: str,
    ):
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                run_scrapy_spider,
                name=self.spider_name,
                task_ids=task_ids,
                mbl_nos=mbl_nos,
                booking_nos=booking_nos,
                container_nos=container_nos,
            )
            future.result()

    def quit(self):
        pass

    def reset(self):
        pass

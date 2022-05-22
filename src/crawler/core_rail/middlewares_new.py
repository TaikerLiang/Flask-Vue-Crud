import sys
import traceback

import scrapy
from scrapy.exceptions import CloseSpider

from crawler.core.base_new import RESULT_STATUS_FATAL
from crawler.core.exceptions_new import BaseError
from crawler.core.items_new import ExportErrorData
from crawler.core_rail.items_new import ExportFinalData


class RailSpiderMiddleware:
    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def process_spider_output(self, response, result, spider):
        error = spider.has_error()

        if error:
            return

        try:
            for i in result:
                if isinstance(i, scrapy.Request):
                    spider.logger.warning(f"[{self.__class__.__name__}] ----- send request: {i.url}")

                yield i

        except Exception:
            spider.mark_error()

            exc_type, exc_value, exc_traceback = sys.exc_info()

            spider.logger.warning(
                f"[{self.__class__.__name__}] ----- process_spider_output -> exception ({exc_type.__name__})"
            )

            error_data = build_error_data_from_exc(exc_type, exc_value, exc_traceback)

            yield error_data

            raise CloseSpider(error_data["status"])

        # [StackOverflow] How to get the number of requests in queue in scrapy?
        # https://stackoverflow.com/questions/28169756/how-to-get-the-number-of-requests-in-queue-in-scrapy
        in_scheduler_count = len(spider.crawler.engine.slot.scheduler)
        in_progress_count = len(spider.crawler.engine.slot.inprogress)

        spider.logger.info(
            f"[{self.__class__.__name__}] ----- process_spider_output"
            f" (in_scheduler={in_scheduler_count}, in_progress={in_progress_count})"
        )

        if (in_scheduler_count == 0) and (in_progress_count <= 1):
            spider.logger.warning(f"[{self.__class__.__name__}] ----- process_spider_output (FINAL)")
            yield ExportFinalData()


def build_error_data_from_exc(exc_type, exc_value, exc_traceback) -> ExportErrorData:
    if isinstance(exc_value, BaseError):
        error_data = exc_value.build_error_data()
    else:
        status = RESULT_STATUS_FATAL
        detail = f"{exc_type.__name__} -- {exc_value}"
        error_data = ExportErrorData(status=status, detail=detail)

    # add traceback info
    tb_info_list = traceback.format_tb(exc_traceback)
    error_data["traceback_info"] = tb_info_list

    return error_data

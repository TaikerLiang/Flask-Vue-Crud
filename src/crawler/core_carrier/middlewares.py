# -*- coding: utf-8 -*-
from scrapy.exceptions import CloseSpider

from .base import CARRIER_RESULT_STATUS_FATAL
from .exceptions import CarrierExceptionBase
from .items import ExportFinalData, ExportErrorData


class CarrierSpiderMiddleware(object):

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def process_spider_output(self, response, result, spider):
        error = spider.has_error()

        if not error:
            for i in result:
                yield i

        # [StackOverflow] How to get the number of requests in queue in scrapy?
        # https://stackoverflow.com/questions/28169756/how-to-get-the-number-of-requests-in-queue-in-scrapy
        in_scheduler_count = len(spider.crawler.engine.slot.scheduler)
        in_progress_count = len(spider.crawler.engine.slot.inprogress)

        spider.logger.info(
            f'[{self.__class__.__name__}] ----- process_spider_output'
            f' (error={error}, in_scheduler={in_scheduler_count}, in_progress={in_progress_count})'
        )

        if (not error) and (in_scheduler_count == 0) and (in_progress_count <= 1):
            spider.logger.warning(f'[{self.__class__.__name__}] ----- process_spider_output (FINAL)')
            yield ExportFinalData()

    def process_spider_exception(self, response, exception, spider):
        spider.logger.warning(
            f'[{self.__class__.__name__}] ----- process_spider_exception ({exception.__class__.__name__})'
        )

        spider.mark_error()

        if isinstance(exception, CarrierExceptionBase):
            status = exception.status
            error_data = exception.build_error_data()
        else:
            status = CARRIER_RESULT_STATUS_FATAL
            detail = f'{exception!r}'
            error_data = ExportErrorData(status=status, detail=detail)

        yield error_data

        raise CloseSpider(status)

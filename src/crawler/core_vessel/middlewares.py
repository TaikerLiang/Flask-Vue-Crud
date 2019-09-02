from scrapy.exceptions import CloseSpider

from crawler.core_vessel.base import VESSEL_RESULT_STATUS_FATAL
from crawler.core_vessel.exceptions import BaseVesselError
from crawler.core_vessel.items import VesselErrorData


class VesselSpiderMiddleware:

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def process_spider_output(self, response, result, spider):
        error = spider.has_error()

        if not error:
            for i in result:
                yield i

    def process_spider_exception(self, response, exception, spider):
        spider.logger.warning(
            f'[{self.__class__.__name__}] ----- process_spider_exception ({exception.__class__.__name__})'
        )

        spider.mark_error()

        if isinstance(exception, BaseVesselError):
            status = exception.status
            error_data = exception.build_error_data()
        else:
            status = VESSEL_RESULT_STATUS_FATAL
            detail = f'{exception!r}'
            error_data = VesselErrorData(status=status, detail=detail)

        yield error_data

        raise CloseSpider(status)

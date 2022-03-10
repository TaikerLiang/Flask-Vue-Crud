from scrapy.exceptions import CloseSpider

from crawler.core.base_new import RESULT_STATUS_FATAL
from crawler.core.exceptions_new import BaseError
from crawler.core_vessel.items import VesselErrorData


class VesselSpiderMiddleware:
    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def process_spider_output(self, response, result, spider):
        error = spider.has_error()

        if not error:
            for i in result:
                yield i

    def process_spider_exception(self, response, exception, spider):
        spider.logger.warning(
            f"[{self.__class__.__name__}] ----- process_spider_exception ({exception.__class__.__name__})"
        )

        spider.mark_error()

        if isinstance(exception, BaseError):
            status = exception.status
            error_data = exception.build_error_data()
        else:
            status = RESULT_STATUS_FATAL
            detail = repr(exception)
            error_data = VesselErrorData(status=status, detail=detail)

        yield error_data

        raise CloseSpider(status)

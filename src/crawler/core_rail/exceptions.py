import abc

from crawler.core_rail.base import RAIL_RESULT_STATUS_FATAL, RAIL_RESULT_STATUS_ERROR
from crawler.core_rail.items import ExportErrorData


class BaseRailError(Exception):
    status = RAIL_RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass


class RailInvalidContainerNoError(BaseRailError):
    status = RAIL_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<invalid-container-no>')


class RailResponseFormatError(BaseRailError):
    status = RAIL_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f'<format-error> {self.reason}')


class ProxyMaxRetryError(BaseRailError):
    status = RAIL_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<proxy-max-retry-error>')


class LoadWebsiteTimeOutFatal(BaseRailError):
    status = RAIL_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<load-website-timeout-fatal>')


class LoginNotSuccessFatal(BaseRailError):
    status = RAIL_RESULT_STATUS_FATAL

    def __init__(self, success_status):
        self.status = success_status

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f'<login-not-success-fatal> status: `{self.status}`')


class DriverMaxRetryError(BaseRailError):
    status = RAIL_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<driver-max-retry-error>')

import abc

from crawler.core_air.base import AIR_RESULT_STATUS_ERROR, AIR_RESULT_STATUS_FATAL
from crawler.core_air.items import ExportErrorData


class BaseAirError(Exception):
    status = AIR_RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass


class AntiCaptchaError(BaseAirError):
    status = AIR_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<anti-captcha-error>")


class AirInvalidMawbNoError(BaseAirError):
    status = AIR_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<invalid-mawb-no>")


class AirResponseFormatError(BaseAirError):
    status = AIR_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<format-error> {self.reason}")


class ProxyMaxRetryError(BaseAirError):
    status = AIR_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<proxy-max-retry-error>")


class LoadWebsiteTimeOutFatal(BaseAirError):
    status = AIR_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<load-website-timeout-fatal>")


class LoginNotSuccessFatal(BaseAirError):
    status = AIR_RESULT_STATUS_FATAL

    def __init__(self, success_status):
        self.status = success_status

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<login-not-success-fatal> status: `{self.status}`")

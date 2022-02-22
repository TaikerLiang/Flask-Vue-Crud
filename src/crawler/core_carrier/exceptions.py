import abc

from .base import CARRIER_RESULT_STATUS_FATAL, CARRIER_RESULT_STATUS_ERROR
from .items import ExportErrorData


class BaseCarrierError(Exception):
    status = CARRIER_RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass


class CarrierSearchNoLengthUnmatchedError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def __init__(self, search_type):
        self._search_type = search_type

    def build_error_data(self):
        return ExportErrorData(
            status=self.status, detail=f"<search-no-length-unmatched> search type: `{self._search_type}`"
        )


class CarrierInvalidSearchNoError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def __init__(self, search_type):
        self._search_type = search_type

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<invalid-search-no> search type: `{self._search_type}`")


class CarrierInvalidMblNoError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<invalid-mbl-no>")


class CarrierMblNotReady(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<mbl-not-ready>")


class CarrierResponseFormatError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def __repr__(self) -> str:
        return f"CarrierResponseFormatError({self.reason})"

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<format-error> {self.reason}")


class LoadWebsiteTimeOutFatal(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<load-website-timeout-fatal>")


class LoadWebsiteTimeOutError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def __init__(self, url):
        self.url = url

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<load-website-timeout-error> on {self.url}")


class ProxyMaxRetryError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<proxy-max-retry-error>")


class DriverMaxRetryError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<driver-max-retry-error>")


class SuspiciousOperationError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def __init__(self, msg: str):
        self.msg = msg

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<suspicious-operation> {self.msg}")


class AntiCaptchaError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f"<anti-captcha-error>")


class DataNotFoundError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<data-not-found>")


class AccessDeniedError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<access-denied>")

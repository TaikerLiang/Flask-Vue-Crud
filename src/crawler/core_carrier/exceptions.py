import abc

from .base import CARRIER_RESULT_STATUS_FATAL, CARRIER_RESULT_STATUS_ERROR
from .items import ExportErrorData


class BaseCarrierError(Exception):
    status = CARRIER_RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass


class CarrierInvalidMblNoError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<invalid-mbl-no>')


class CarrierMblNotReady(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<mbl-not-ready>')


class CarrierResponseFormatError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f'<format-error> {self.reason}')


class LoadWebsiteTimeOutError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<load-website-timeout-error>')

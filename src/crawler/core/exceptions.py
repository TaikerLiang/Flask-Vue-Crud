import abc
import random
import string

from .base import RESULT_STATUS_FATAL
from .items import ExportErrorData


class BaseError(Exception):
    status = RESULT_STATUS_FATAL

    def __init__(self, task_id: str = "", mbl_no: str = "", booking_no: str = "", container_no: str = ""):
        self.task_id = task_id
        self.mbl_no = mbl_no
        self.booking_no = booking_no
        self.container_no = container_no

    @abc.abstractmethod
    def build_error_data(self, detail):
        pass


class ProxyMaxRetryError(BaseError):
    def build_error_data(self, detail: str = ""):
        return ExportErrorData(status=self.status, detail="<proxy-max-retry-error>")


class FormatError(BaseError):
    def build_error_data(self, detail: str = ""):
        return ExportErrorData(status=self.status, detail=detail)

import abc
import random
import string

from .base import RESULT_STATUS_FATAL
from .items import ExportErrorData


class BaseError(Exception):
    status = RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass


class ProxyMaxRetryError(BaseError):
    status = RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail="<proxy-max-retry-error>")

import abc

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_FATAL, TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.items import ExportErrorData


class BaseTerminalError(Exception):
    status = TERMINAL_RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass


class TerminalInvalidMblNoError(BaseTerminalError):
    status = TERMINAL_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<invalid-mbl-no>')


class TerminalInvalidContainerNoError(BaseTerminalError):
    status = TERMINAL_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<invalid-container-no>')


class TerminalResponseFormatError(BaseTerminalError):
    status = TERMINAL_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f'<format-error> {self.reason}')


class ProxyMaxRetryError(BaseTerminalError):
    status = TERMINAL_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<proxy-max-retry-error>')

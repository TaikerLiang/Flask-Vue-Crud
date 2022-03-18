import abc

from crawler.core.base_new import RESULT_STATUS_ERROR, RESULT_STATUS_FATAL
from crawler.core.items_new import ExportErrorData

# ---------------------------------------------------------------------
# Fatal Error
# ---------------------------------------------------------------------


class BaseError(Exception):
    status = RESULT_STATUS_FATAL

    def __init__(self, task_id: str = "", search_no: str = "", search_type: str = "", reason: str = ""):
        self.task_id = task_id
        self.search_no = search_no
        self.search_type = search_type
        self.reason = reason

        self._param = {
            "task_id": self.task_id,
            "search_no": self.search_no,
            "search_type": self.search_type,
            "status": self.status,
        }

    def __repr__(self) -> str:
        return repr(self.build_error_data())

    @abc.abstractmethod
    def build_error_data(self) -> ExportErrorData:
        pass


class GeneralFatalError(BaseError):
    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail=f"<general-fatal-error> {self.reason}")


class LoginFailError(BaseError):
    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail=f"<login-fail> {self.reason}")


# Response unexpected
class FormatError(BaseError):
    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail=f"<format-error> {self.reason}")


class ResponseStatusCodeError(BaseError):
    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail=f"<status-code-error> {self.reason}")


class SuspiciousOperationError(BaseError):
    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail=f"<suspicious-operation> {self.reason}")


class SearchNoLengthMismatchError(BaseError):
    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail=f"<search-no-length-mismatch> {self.reason}")


# ---------------------------------------------------------------------
# Non-Fatal Error
# ---------------------------------------------------------------------


class GeneralError(BaseError):
    status = RESULT_STATUS_ERROR

    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail=f"<general-error> {self.reason}")


class DidNotEndError(BaseError):
    status = RESULT_STATUS_ERROR

    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail="<Task did not end>")


class TimeOutError(BaseError):
    status = RESULT_STATUS_ERROR

    def build_error_data(self) -> ExportErrorData:
        detail = "<website-timeout-error>"
        if self.reason:
            detail += f" url='{self.reason}'"

        return ExportErrorData(**self._param, detail=detail)


class AccessDeniedError(BaseError):
    status = RESULT_STATUS_ERROR

    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail="<access-denied>")


class MaxRetryError(BaseError):
    status = RESULT_STATUS_ERROR

    def build_error_data(self) -> ExportErrorData:
        return ExportErrorData(**self._param, detail=f"<max-retry-error> {self.reason}")

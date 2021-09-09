import abc

from crawler.core_air.base import AIR_RESULT_STATUS_ERROR, AIR_RESULT_STATUS_FATAL


class BaseTerminalError(Exception):
    status = AIR_RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass

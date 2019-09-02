import abc

from crawler.core_vessel.base import VESSEL_RESULT_STATUS_FATAL


class BaseVesselError(Exception):
    status = VESSEL_RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass

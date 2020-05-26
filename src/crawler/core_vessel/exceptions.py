import abc

from crawler.core_vessel.base import VESSEL_RESULT_STATUS_FATAL
from crawler.core_vessel.items import VesselErrorData


class BaseVesselError(Exception):
    status = VESSEL_RESULT_STATUS_FATAL

    @abc.abstractmethod
    def build_error_data(self):
        pass


class LoadWebsiteTimeOutError(BaseVesselError):
    status = VESSEL_RESULT_STATUS_FATAL

    def build_error_data(self):
        return VesselErrorData(status=self.status, detail='<load-website-timeout-error>')

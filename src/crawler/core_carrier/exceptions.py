# -*- coding: utf-8 -*-
from .base import CARRIER_RESULT_STATUS_FATAL, CARRIER_RESULT_STATUS_ERROR
from .items import ExportErrorData


class CarrierExceptionBase(Exception):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        raise NotImplementedError


class CarrierInvalidMblNoError(CarrierExceptionBase):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<invalid-mbl-no>')


class CarrierMblNotReady(CarrierExceptionBase):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<mbl-not-ready>')


class CarrierResponseFormatError(CarrierExceptionBase):
    status = CARRIER_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f'<format-error> {self.reason}')

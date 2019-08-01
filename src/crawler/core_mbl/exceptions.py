# -*- coding: utf-8 -*-
from crawler.core_mbl.base import CARRIER_RESULT_STATUS_FATAL, CARRIER_RESULT_STATUS_ERROR
from crawler.core_mbl.items import ExportErrorData


class MblExceptionBase(Exception):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        raise NotImplementedError


class MblInvalidMblNoError(MblExceptionBase):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<invalid-mbl-no>')


class MblInfoNotReady(MblExceptionBase):
    status = CARRIER_RESULT_STATUS_ERROR

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<mbl-not-ready>')


class MblResponseFormatError(MblExceptionBase):
    status = CARRIER_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f'<format-error> {self.reason}')

# -*- coding: utf-8 -*-
from crawler.core_mbl.items import ExportErrorData

CATEGORY_WARNING = 'warning'
CATEGORY_ERROR = 'error'
CATEGORY_MBL_NO_ERROR = 'mbl_no_error'
CATEGORY_FORMAT_ERROR = 'format_error'
CATEGORY_EXCEPTION = 'exception'


class MblExceptionBase(Exception):
    category = CATEGORY_ERROR

    def build_error_data(self):
        raise NotImplementedError


class MblInvalidMblNoError(MblExceptionBase):
    category = CATEGORY_MBL_NO_ERROR

    def build_error_data(self):
        return ExportErrorData(category=self.category)


class MblInfoNotReady(MblExceptionBase):
    category = CATEGORY_WARNING

    def build_error_data(self):
        return ExportErrorData(category=self.category, reason='mbl not ready')


class MblResponseFormatError(MblExceptionBase):
    category = CATEGORY_FORMAT_ERROR

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(category=self.category, reason=f'{self.reason}')

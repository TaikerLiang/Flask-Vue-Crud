from crawler.core_carrier.items import ExportErrorData
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR


class Verifier:
    @staticmethod
    def verify(results):
        assert results[0] == ExportErrorData(
            mbl_no="HLCUHKG1911AVNM",
            status=CARRIER_RESULT_STATUS_ERROR,
            detail="Data was not found",
        )

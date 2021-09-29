import pytest
from typing import Dict, List

from crawler.core_air.base import AIR_RESULT_STATUS_DEBUG, AIR_RESULT_STATUS_ERROR, AIR_RESULT_STATUS_FATAL
from crawler.core_air.items import AirItem, DebugItem, ExportErrorData, FlightItem, HistoryItem
from crawler.core_air.pipelines import AirResultCollector


TEST_AIR = [
    dict(task_id="1", mawb="11111111", origin="KYOTO", destination="TOKYO", atd="2021-8-2", ata="2021-8-3"),
    dict(task_id="2", mawb="22222222", origin="HONGKONG", destination="SHANGHAI", atd="2021-9-1", ata="2021-9-2"),
    dict(task_id="3", mawb="33333333", origin="TAIPEI", destination="TAICHUNG", atd="2021-9-6", ata="2021-9-7"),
]

TEST_FLIGHT = [
    dict(task_id="1", flight_number="F1", origin="KYOTO", destination="TOKYO", atd="2021-8-2", ata="2021-8-3"),
    dict(task_id="2", flight_number="F2", origin="HONGKONG", destination="SHANGHAI", atd="2021-9-1", ata="2021-9-2"),
    dict(task_id="3", flight_number="F3", origin="TAIPEI", destination="TAICHUNG", atd="2021-9-6", ata="2021-9-7"),
]

TEST_HISTORY = [
    dict(task_id="1", status="Depart", flight_number="F1", location="KYOTO", pieces="5", weight="55", time="2021-8-2"),
    dict(task_id="1", status="Arrive", flight_number="F1", location="TOKYO", pieces="5", weight="55", time="2021-8-3"),
    dict(task_id="1", status="Notify", flight_number="F1", location="TOKYO", pieces="5", weight="55", time="2021-8-3"),
]

TEST_ERROR = [
    dict(mawb_no="87654321", status=AIR_RESULT_STATUS_FATAL, detail=""),
    dict(mawb_no="88888888", status=AIR_RESULT_STATUS_FATAL, detail=""),
]

TEST_DEBUG = [
    dict(info="I'm a debug item"),
]


class TestAirlineResultCollector:
    @pytest.mark.parametrize(
        "test_air",
        [
            TEST_AIR[0],
            TEST_AIR[1],
            TEST_AIR[2],
        ],
    )
    def test_collect_air_item(self, test_air: Dict):
        # arrange
        collector = AirResultCollector(request_args={})

        # action
        collector.collect_air_item(item=AirItem(**test_air))

        data = collector.build_final_data()

        # assert
        assert data["air"] == test_air

    @pytest.mark.parametrize(
        "test_flight",
        [
            TEST_FLIGHT,
        ],
    )
    def test_collect_flight_item(self, test_flight: List):
        # arrange
        collector = AirResultCollector(request_args={})

        # action
        for flight in test_flight:
            collector.collect_flight_item(item=FlightItem(**flight))

        data = collector.build_final_data()

        # assert
        assert data["flights"] == test_flight

    @pytest.mark.parametrize(
        "test_history",
        [
            TEST_HISTORY,
        ],
    )
    def test_collect_history_item(self, test_history: List):
        # arrange
        collector = AirResultCollector(request_args={})

        # action
        for history in test_history:
            collector.collect_history_item(item=HistoryItem(**history))

        data = collector.build_final_data()

        # assert
        assert data["history"] == test_history

    def test_build_final_data(self):
        # arrange
        request_args = {"task_id": "12345", "mawb": "87654321"}

        collector = AirResultCollector(request_args=request_args)

        # action
        data = collector.build_final_data()

        # assert
        assert data is None

    @pytest.mark.parametrize(
        "test_error",
        [
            TEST_ERROR[0],
            TEST_ERROR[1],
        ],
    )
    def test_build_error_data(self, test_error: Dict):
        # arrange
        request_args = {"task_id": "12345", "mawb": "87654321"}

        collector = AirResultCollector(request_args=request_args)

        # action
        data = collector.build_error_data(item=ExportErrorData(**test_error))

        test_error.update({"request_args": request_args})

        # assert
        assert data == test_error

    @pytest.mark.parametrize(
        "test_debug",
        [
            TEST_DEBUG[0],
        ],
    )
    def test_build_debug_data(self, test_debug: Dict):
        # arrange
        collector = AirResultCollector(request_args={})

        # action
        data = collector.build_debug_data(item=DebugItem(**test_debug))

        # assert
        test_debug.update({"status": AIR_RESULT_STATUS_DEBUG})

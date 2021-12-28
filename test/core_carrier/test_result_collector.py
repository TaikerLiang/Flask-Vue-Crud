from typing import Container
from crawler.core_carrier.items import ContainerStatusItem, RailItem, VesselItem, ContainerItem
from crawler.core_carrier.pipelines import CarrierResultCollector


class TestCarrierResultCollector:
    def test_collect_vessel_item(self):
        expect_vessels = [
            dict(vessel_key="V1", vessel="V1", etd="2019-08-01", eta="2019-08-10"),
            dict(vessel_key="V2", vessel="", etd="2019-08-11", eta="2019-08-20"),
            dict(vessel_key="V3", vessel="V3", etd="2019-08-21", eta="2019-08-30"),
        ]

        # arrange
        collector = CarrierResultCollector(request_args={})

        # action
        collector.collect_vessel_item(item=VesselItem(**expect_vessels[0]))
        collector.collect_vessel_item(item=VesselItem(**expect_vessels[1]))
        collector.collect_vessel_item(item=VesselItem(**expect_vessels[2]))

        # assert
        data = collector.build_final_data()
        assert data["vessels"] == expect_vessels

    def test_collect_container_item(self):
        expect_containers = [
            dict(container_key="CT1", container_no="CT1", last_free_day="2019-08-01", status=[], rail_status=[]),
            dict(container_key="CT2", container_no="", last_free_day="2019-08-11", status=[], rail_status=[]),
            dict(container_key="CT3", container_no="CT3", last_free_day="2019-08-21", status=[], rail_status=[]),
        ]

        # arrange
        collector = CarrierResultCollector(request_args={})

        ct0 = {k: v for k, v in expect_containers[0].items() if k != "status" and k != "rail_status"}
        ct1 = {k: v for k, v in expect_containers[1].items() if k != "status" and k != "rail_status"}
        ct2 = {k: v for k, v in expect_containers[2].items() if k != "status" and k != "rail_status"}

        # action
        collector.collect_container_item(item=ContainerItem(**ct0))
        collector.collect_container_item(item=ContainerItem(**ct1))
        collector.collect_container_item(item=ContainerItem(**ct2))

        # assert
        data = collector.build_final_data()
        assert data["containers"] == expect_containers

    def test_collect_carrier_status_item(self):
        expect_status = [
            dict(container_key="CT1"),
            dict(container_key="CT2"),
            dict(container_key="CT3"),
        ]
        expect_containers = [
            dict(container_key="CT1", container_no="CT1", status=[expect_status[0]], rail_status=[]),
            dict(container_key="CT2", container_no="CT2", status=[expect_status[1]], rail_status=[]),
            dict(container_key="CT3", container_no="CT3", status=[expect_status[2]], rail_status=[]),
        ]

        # arrange
        collector = CarrierResultCollector(request_args={})

        ct0 = {k: v for k, v in expect_containers[0].items() if k != "status" and k != "rail_status"}
        ct1 = {k: v for k, v in expect_containers[1].items() if k != "status" and k != "rail_status"}
        ct2 = {k: v for k, v in expect_containers[2].items() if k != "status" and k != "rail_status"}
        st0 = {k: v for k, v in expect_status[0].items()}
        st1 = {k: v for k, v in expect_status[1].items()}
        st2 = {k: v for k, v in expect_status[2].items()}

        # action
        collector.collect_container_item(item=ContainerItem(**ct0))
        collector.collect_container_item(item=ContainerItem(**ct1))
        collector.collect_container_item(item=ContainerItem(**ct2))
        collector.collect_container_status_item(item=ContainerStatusItem(**st0))
        collector.collect_container_status_item(item=ContainerStatusItem(**st1))
        collector.collect_container_status_item(item=ContainerStatusItem(**st2))

        # assert
        data = collector.build_final_data()
        assert data["containers"] == expect_containers

    def test_collect_rail_item(self):
        expect_rail_status = [
            dict(container_key="CT1"),
            dict(container_key="CT2"),
            dict(container_key="CT3"),
        ]
        expect_containers = [
            dict(container_key="CT1", container_no="CT1", status=[], rail_status=[expect_rail_status[0]]),
            dict(container_key="CT2", container_no="CT2", status=[], rail_status=[expect_rail_status[1]]),
            dict(container_key="CT3", container_no="CT3", status=[], rail_status=[expect_rail_status[2]]),
        ]

        # arrange
        collector = CarrierResultCollector(request_args={})

        ct0 = {k: v for k, v in expect_containers[0].items() if k != "status" and k != "rail_status"}
        ct1 = {k: v for k, v in expect_containers[1].items() if k != "status" and k != "rail_status"}
        ct2 = {k: v for k, v in expect_containers[2].items() if k != "status" and k != "rail_status"}
        st0 = {k: v for k, v in expect_rail_status[0].items()}
        st1 = {k: v for k, v in expect_rail_status[1].items()}
        st2 = {k: v for k, v in expect_rail_status[2].items()}

        # action
        collector.collect_container_item(item=ContainerItem(**ct0))
        collector.collect_container_item(item=ContainerItem(**ct1))
        collector.collect_container_item(item=ContainerItem(**ct2))
        collector.collect_rail_item(item=RailItem(**st0))
        collector.collect_rail_item(item=RailItem(**st1))
        collector.collect_rail_item(item=RailItem(**st2))

        # assert
        data = collector.build_final_data()
        assert data["containers"] == expect_containers

    def test_build_final_data(self):
        # arrange
        request_args = {"task_id": "88444", "mbl_no": "123"}
        collector = CarrierResultCollector(request_args=request_args)

        # action
        final_data = collector.build_final_data()

        # assertion
        assert final_data is None

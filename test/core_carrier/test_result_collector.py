from crawler.core_carrier.items import VesselItem, ContainerItem
from crawler.core_carrier.pipelines import CarrierResultCollector


class TestCarrierResultCollector:

    def test_collect_vessel_item(self):
        expect_vessels = [
            dict(vessel_key='V1', vessel='V1', etd='2019-08-01', eta='2019-08-10'),
            dict(vessel_key='V2', vessel='', etd='2019-08-11', eta='2019-08-20'),
            dict(vessel_key='V3', vessel='V3', etd='2019-08-21', eta='2019-08-30'),
        ]

        # arrange
        collector = CarrierResultCollector(request_args={})

        # action
        collector.collect_vessel_item(item=VesselItem(**expect_vessels[0]))
        collector.collect_vessel_item(item=VesselItem(**expect_vessels[1]))
        collector.collect_vessel_item(item=VesselItem(**expect_vessels[2]))

        # assert
        data = collector.build_final_data()
        assert data['vessels'] == expect_vessels

    def test_collect_container_item(self):
        expect_containers = [
            dict(container_key='CT1', container_no='CT1', last_free_day='2019-08-01', status=[]),
            dict(container_key='CT2', container_no='', last_free_day='2019-08-11', status=[]),
            dict(container_key='CT3', container_no='CT3', last_free_day='2019-08-21', status=[]),
        ]

        # arrange
        collector = CarrierResultCollector(request_args={})

        ct0 = {k: v for k, v in expect_containers[0].items() if k != 'status'}
        ct1 = {k: v for k, v in expect_containers[1].items() if k != 'status'}
        ct2 = {k: v for k, v in expect_containers[2].items() if k != 'status'}

        # action
        collector.collect_container_item(item=ContainerItem(**ct0))
        collector.collect_container_item(item=ContainerItem(**ct1))
        collector.collect_container_item(item=ContainerItem(**ct2))

        # assert
        data = collector.build_final_data()
        assert data['containers'] == expect_containers

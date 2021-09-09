from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:
    def verify(self, results):
        assert results[0] == ContainerStatusItem(
            container_key='HMCU9173542',
            description='Empty pick-up by merchant haulage',
            local_date_time='AUG-09-2019',
            location=LocationItem(name='KAOHSIUNG (TW)'),
            task_id='1',
        )

        assert results[6] == ContainerStatusItem(
            container_key='HMCU9173542',
            description='Transship container loaded on vessel',
            local_date_time='AUG-28-2019',
            location=LocationItem(name='PUSAN (KR)'),
            task_id='1',
        )

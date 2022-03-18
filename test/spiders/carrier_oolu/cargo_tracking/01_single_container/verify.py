from crawler.core_carrier.items import MblItem, LocationItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_oolu import ContainerStatusRule


def verify(results):
    assert results[0] == MblItem(
        mbl_no='2625845270',
        vessel='XIN YING KOU',
        voyage='089E',
        por=LocationItem(name='Yantian, Shenzhen, Guangdong, China'),
        pol=LocationItem(name='Yantian, Shenzhen, Guangdong, China'),
        pod=LocationItem(name='Long Beach, Los Angeles, California, United States'),
        etd=None,
        atd='10 Sep 2019, 12:38 CCT',
        eta=None,
        ata='28 Sep 2019, 06:10 PDT',
        place_of_deliv=LocationItem(name='BNSF - Chicago LPC'),
        deliv_eta=None,
        deliv_ata='07 Oct 2019, 07:13 CDT',
        final_dest=LocationItem(name='Chicago, Cook, Illinois, United States'),
        customs_release_status='Cleared',
        customs_release_date='07 Oct 2019, 07:15 GMT',
    )

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == ContainerStatusRule.name
    assert results[1].meta == {
        'container_no': 'OOCU8081870',
        'click_element_css': "a[id='form:link0']",
    }

from crawler.core_carrier.items import MblItem, LocationItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_oolu_multi import ContainerStatusRule


def verify(results):
    assert results[0] == {
        'date': '07 Oct 2019, 07:15 GMT',
        'status': 'Cleared'
    }
    assert results[1] == {
        'ata': '28 Sep 2019, 06:10 PDT',
         'atd': '10 Sep 2019, 12:38 CCT',
         'deliv_ata': '07 Oct 2019, 07:13 CDT',
         'deliv_eta': None,
         'eta': None,
         'etd': None,
         'final_dest': 'Chicago, Cook, Illinois, United States',
         'place_of_deliv': 'BNSF - Chicago LPC',
         'pod': 'Long Beach, Los Angeles, California, United States',
         'pol': 'Yantian, Shenzhen, Guangdong, China',
         'por': 'Yantian, Shenzhen, Guangdong, China',
         'vessel': 'XIN YING KOU',
         'voyage': '089E'
    }


import scrapy

from crawler.core_carrier.items import MblItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SITDNBBK351734',
        pol=LocationItem(name='NINGBO'),
        final_dest=LocationItem(name='BANGKOK'),
    )

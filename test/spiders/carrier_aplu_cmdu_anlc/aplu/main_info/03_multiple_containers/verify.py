from crawler.spiders.carrier_aplu_cmdu_anlc import SharedUrlFactory, UrlSpec, CarrierApluSpider


def verify(results):
    url_factory = SharedUrlFactory(home_url=CarrierApluSpider.home_url, mbl_no='SHSE015942')
    url_builder = url_factory.get_container_url_builder()

    assert results[0].url == url_builder.build_url_from_spec(
        UrlSpec(
            container_no='TCNU1868370',
        )
    )

    assert results[1].url == url_builder.build_url_from_spec(
        UrlSpec(
            container_no='APHU6968583',
        )
    )

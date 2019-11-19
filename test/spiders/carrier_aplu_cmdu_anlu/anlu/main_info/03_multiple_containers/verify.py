from crawler.spiders.carrier_aplu_cmdu_anlu import SharedUrlFactory, CarrierAnluSpider, UrlSpec


def verify(results):
    url_factory = SharedUrlFactory(home_url=CarrierAnluSpider.home_url, mbl_no='AWT0143454')
    url_builder = url_factory.get_container_url_builder()
    assert results[0].url == url_builder.build_url_from_spec(
        UrlSpec(
            container_no='TEXU1028151',
        )
    )

    assert results[1].url == url_builder.build_url_from_spec(
        UrlSpec(
            container_no='AMCU2500184',
        )
    )

    assert results[2].url == url_builder.build_url_from_spec(
        UrlSpec(
            container_no='TLLU1233702',
        )
    )

    assert results[3].url == url_builder.build_url_from_spec(
        UrlSpec(
            container_no='TCLU7717882',
        )
    )

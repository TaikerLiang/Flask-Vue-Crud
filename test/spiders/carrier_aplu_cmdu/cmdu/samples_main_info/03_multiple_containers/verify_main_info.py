from crawler.spiders.carrier_aplu_cmdu import SharedUrlFactory, UrlSpec, CarrierCmduSpider


class Verifier:
    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        url_factory = SharedUrlFactory(home_url=CarrierCmduSpider.home_url, mbl_no=self.mbl_no)
        url_builder = url_factory.get_container_url_builder()

        assert results[0].url == url_builder.build_url_from_spec(
            UrlSpec(
                    container_no='ECMU9893257',
            ),
        )

        assert results[1].url == url_builder.build_url_from_spec(
            UrlSpec(
                    container_no='ECMU9836072',
            ),
        )

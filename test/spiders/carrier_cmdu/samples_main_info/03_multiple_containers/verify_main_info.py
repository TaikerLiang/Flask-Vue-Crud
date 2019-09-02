from crawler.spiders.carrier_aplu_cmdu import SharedUrlFactory, UrlSpec, CarrierCmduSpider


class Verifier:
    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        url_factory = SharedUrlFactory(home_url=CarrierCmduSpider.home_url, mbl_no=self.mbl_no)
        assert results[0].url == url_factory.build_container_url(
            UrlSpec(
                    container_no='ECMU9893257',
            ),
        )

        assert results[1].url == url_factory.build_container_url(
            UrlSpec(
                    container_no='ECMU9836072',
            ),
        )

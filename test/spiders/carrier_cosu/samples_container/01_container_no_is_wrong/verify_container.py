from crawler.core_carrier.items import ContainerItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):
        assert results[0] == ContainerItem(**{
            'container_no': 'OOLU3647169',
            'container_key': '1',
        })

        expect_url = 'http://elines.coscoshipping.com/ebtracking/public/container/status/OOLU3647169?billNumber=6205749080&timestamp='
        assert results[1].url.startswith(expect_url)

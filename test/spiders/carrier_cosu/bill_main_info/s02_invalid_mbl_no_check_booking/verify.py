from scrapy import Request


def verify(results, mbl_no):
    assert isinstance(results[0], Request)

    expect_url = f'http://elines.coscoshipping.com/ebtracking/public/booking/{mbl_no}'

    assert expect_url in results[0].url

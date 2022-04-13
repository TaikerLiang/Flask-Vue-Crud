from crawler.core_carrier.request_helpers_new import RequestOption


def verify(results, mbl_no):
    assert isinstance(results[0], RequestOption)

    expect_url = f"http://elines.coscoshipping.com/ebtracking/public/booking/{mbl_no}"

    assert expect_url in results[0].url

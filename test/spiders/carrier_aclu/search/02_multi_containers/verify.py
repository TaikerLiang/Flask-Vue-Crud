import scrapy


def verify(results):
    assert isinstance(results[0], scrapy.Request)
    assert isinstance(results[1], scrapy.Request)
    assert isinstance(results[2], scrapy.Request)
    assert isinstance(results[3], scrapy.Request)
    assert isinstance(results[4], scrapy.Request)
    assert isinstance(results[5], scrapy.Request)
    assert isinstance(results[6], scrapy.Request)
    assert isinstance(results[7], scrapy.Request)
    assert isinstance(results[8], scrapy.Request)
    assert isinstance(results[9], scrapy.Request)

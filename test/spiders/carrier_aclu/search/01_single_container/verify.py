import scrapy


def verify(results):
    assert isinstance(results[0], scrapy.Request)

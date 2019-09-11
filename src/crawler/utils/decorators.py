from functools import wraps


def merge_yields(f):
    """
    Workaround for scrapy issue :
        process_spider_exception() not invoked for generators
        (https://github.com/scrapy/scrapy/issues/220)
    """
    @wraps(f)
    def _wrapper(*args, **kwargs):
        return list(f(*args, **kwargs))
    return _wrapper

import random


def _random_choice_user_agent() -> str:
    user_agents = [
        # chrome
        # 2020/09/14 maybe too old, new ver in zimu
        (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2)'
            ' AppleWebKit/537.36 (KHTML, like Gecko)'
            ' Chrome/75.0.3770.142'
            ' Safari/537.36'
        ),
        (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2)'
            ' AppleWebKit/537.36 (KHTML, like Gecko)'
            ' Chrome/79.0.3945.88'
            ' Safari/537.36'
        ),

        # firefox
        (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:67.0)'
            ' Gecko/20100101'
            ' Firefox/67.0'
        ),
        (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:68.0)'
            ' Gecko/20100101'
            ' Firefox/68.0'
        ),
        (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:69.0)'
            ' Gecko/20100101'
            ' Firefox/69.0'
        ),
        (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:70.0)'
            ' Gecko/20100101'
            ' Firefox/70.0'
        ),
    ]

    return random.choice(user_agents)


class UserAgentDownloaderMiddleware:

    def __init__(self, user_agent: str):
        assert user_agent
        self.user_agent = user_agent

    @classmethod
    def from_crawler(cls, crawler):
        user_agent = _random_choice_user_agent()
        return cls(user_agent=user_agent)

    def process_request(self, request, spider):
        if request.headers.get('User-Agent'):
            return
        request.headers.setdefault(b'User-Agent', self.user_agent)

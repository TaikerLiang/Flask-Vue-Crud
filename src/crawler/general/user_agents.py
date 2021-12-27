import random


def _random_choice_user_agent() -> str:
    user_agents = [
        # chrome
        # 2020/09/14 maybe too old, new ver in zimu
        (
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        ),
        ("Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        ),
        # firefox
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 12.1; rv:95.0) Gecko/20100101 Firefox/95.0"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 12.1; rv:94.0) Gecko/20100101 Firefox/94.0"),
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
        if request.headers.get("User-Agent"):
            return
        request.headers.setdefault(b"User-Agent", self.user_agent)

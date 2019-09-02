import random


class UserAgentDownloaderMiddleware:

    def __init__(self, user_agent: str):
        assert user_agent
        self.user_agent = user_agent

    @classmethod
    def from_crawler(cls, crawler):
        user_agents = crawler.settings['AVAILABLE_USER_AGENTS']
        user_agent = random.choice(user_agents) if user_agents else 'Scrapy'
        return cls(user_agent=user_agent)

    def process_request(self, request, spider):
        if request.headers.get('User-Agent'):
            return
        request.headers.setdefault(b'User-Agent', self.user_agent)

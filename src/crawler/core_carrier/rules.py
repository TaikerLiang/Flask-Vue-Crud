import abc
from typing import List, Union, Optional


from crawler.core_carrier.request_helpers import RequestOption


class BaseRoutingRule:
    name = ""

    @staticmethod
    def build_request_option(*args, **kwargs) -> RequestOption:
        raise NotImplementedError()

    def get_save_name(self, response) -> str:
        return self.name

    @abc.abstractmethod
    def handle(self, response):
        pass


class RuleManager:
    META_CARRIER_CORE_RULE_NAME = "CARRIER_CORE_RULE_NAME"

    def __init__(self, rules: List[BaseRoutingRule]):
        self._rule_map = {r.name: r for r in rules}

    def get_rule_by_response(self, response) -> BaseRoutingRule:
        rule_name = response.meta[self.META_CARRIER_CORE_RULE_NAME]
        rule = self._rule_map[rule_name]
        return rule

    def get_rule_by_name(self, name) -> Optional[BaseRoutingRule]:
        if name in self._rule_map:
            return self._rule_map[name]
        return None


class RequestOptionQueue:
    def __init__(self):
        self._queue = []

    def is_empty(self):
        return not self._queue

    def add_request(self, request_option: RequestOption):
        self._queue.append(request_option)

    def add_high_priority_request(self, request_option: RequestOption):
        self._queue.insert(0, request_option)

    def get_next_request(self) -> Union[RequestOption, None]:
        return self._queue.pop(0)

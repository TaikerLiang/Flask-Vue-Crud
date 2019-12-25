import abc
import dataclasses
from typing import List, Union

import scrapy


@dataclasses.dataclass
class RoutingRequest:
    request: scrapy.Request
    rule_name: str


class BaseRoutingRule:
    name = ''

    @staticmethod
    def build_routing_request(*args, **kwargs) -> RoutingRequest:
        raise NotImplementedError()

    def get_save_name(self, response) -> str:
        return self.name

    @abc.abstractmethod
    def handle(self, response):
        pass


class RuleManager:
    META_CARRIER_CORE_RULE_NAME = 'CARRIER_CORE_RULE_NAME'

    def __init__(self, rules: List[BaseRoutingRule]):
        self._rule_map = {
            r.name: r for r in rules
        }

    def get_rule_by_response(self, response) -> BaseRoutingRule:
        rule_name = response.meta[self.META_CARRIER_CORE_RULE_NAME]
        rule = self._rule_map[rule_name]
        return rule

    def build_request_by(self, routing_request: RoutingRequest):
        request = routing_request.request
        request.meta[self.META_CARRIER_CORE_RULE_NAME] = routing_request.rule_name
        return request


class RoutingRequestQueue:

    def __init__(self):
        self._queue = []

    def add_request(self, routing_request: RoutingRequest):
        self._queue.append(routing_request)

    def get_next_request(self) -> Union[RoutingRequest, None]:
        if self._queue:
            return self._queue.pop(0)
        else:
            return None

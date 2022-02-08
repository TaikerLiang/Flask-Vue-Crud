import json
from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_e416 import LoginRoutingRule, SearchRoutingRule
from test.spiders.terminal_e416 import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_nos",
    [
        ("01_login", "ECMU8065005,UETU5115112,APHU7007894,TRHU6046630,OOLU6811996"),
    ],
)
def test_login_rule(sub, container_nos, sample_loader):
    # arrange
    json_text = sample_loader.read_file(sub, "login.json")
    token = "TOKEN"
    containers_nos = container_nos.split(",")
    option = LoginRoutingRule.build_request_option(container_nos=containers_nos)

    response = TextResponse(
        url=option.url,
        body=json_text,
        headers={"Content": "application/json", "Authorization": token},
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta={
                "container_nos": containers_nos,
            },
        ),
    )

    # action
    results = list(LoginRoutingRule().handle(response=response))

    # assert
    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,container_nos",
    [
        ("02_search", "ECMU8065005,UETU5115112,APHU7007894,TRHU6046630,OOLU6811996"),
    ],
)
def test_search_rule(sub, container_nos, sample_loader):
    # arrange
    json_text = sample_loader.read_file(sub, "resp.json")
    user_data = {}
    token = "TOKEN"
    containers_nos = container_nos.split(",")
    option = SearchRoutingRule.build_request_option(container_nos=containers_nos, user_data=user_data, token=token)

    response = TextResponse(
        url=option.url,
        body=json_text,
        headers={"Content": "application/json", "Authorization": token},
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta={
                "container_nos": containers_nos,
                "user_data": user_data,
                "token": token,
            },
        ),
    )

    # action
    results = list(SearchRoutingRule().handle(response=response))

    # assert
    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)

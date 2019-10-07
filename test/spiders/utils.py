from typing import Dict

from crawler.core_carrier.rules import RoutingRequest


def convert_formdata_to_bytes(formdata: Dict) -> bytes:
    pairs = []
    for key, value in formdata.items():
        if isinstance(value, list):
            pairs.extend([f'{key}={v}' for v in value])
        else:
            pairs.append(f'{key}={value}')

    formdata_str = '&'.join(pairs)
    return formdata_str.encode()


def extract_url_from(routing_request: RoutingRequest) -> str:
    request = routing_request.request
    return request.url

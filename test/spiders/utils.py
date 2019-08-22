from typing import Dict


def convert_formdata_to_bytes(formdata: Dict) -> bytes:
    pairs = []
    for key, value in formdata.items():
        if isinstance(value, list):
            pairs.extend([f'{key}={v}' for v in value])
        else:
            pairs.append(f'{key}={value}')

    formdata_str = '&'.join(pairs)
    return formdata_str.encode()

import json
from pathlib import Path
from queue import Queue

from crawler.spiders.carrier_sudu import VoyageSpec

PARENT_PATH = Path(__file__).parent


def get_queue_by_sub(sub: str):
    with open(PARENT_PATH / sub / 'voyage_specs.json', 'r') as fp:
        voyage_spec_dicts = json.load(fp)

    queue = Queue()

    for voyage_spec_dict in voyage_spec_dicts:
        queue.put(VoyageSpec(**voyage_spec_dict))

    return queue


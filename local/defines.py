from typing import List
from enum import IntEnum
import dataclasses


@dataclasses.dataclass
class LocalTask:
    code: str
    task_ids: List
    mbl_nos: List
    booking_nos: List
    container_nos: List


class AggregatePagingNum(IntEnum):
    CARRIER = 1
    TERMINAL = 10
    RAIL = 10

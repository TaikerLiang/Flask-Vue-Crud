from carriers import zimu
from terminals import trapac_la, trapac_oak


CARRIERS = [
    zimu.ZimuLocalCrawler,
]

CARRIER_CLASS_MAP = {c.code: c for c in CARRIERS}


TERMINALS = [trapac_la.LaTrapacLocalCrawler, trapac_oak.OakTrapacLocalCrawler]

TERMINALS_CLASS_MAP = {t.code: t for t in TERMINALS}


CRAWLER_MAP = {
    **CARRIER_CLASS_MAP,
    **TERMINALS_CLASS_MAP,
}

from carriers import zimu, whlc, cmdu
from terminals import trapac_la, trapac_oak, trapac_jax


CARRIERS = [
    zimu.ZimuLocalCrawler,
    whlc.WhlcLocalCrawler,
    cmdu.CmduLocalCrawler,
]

CARRIER_CLASS_MAP = {c.code: c for c in CARRIERS}


TERMINALS = [
    trapac_la.LaTrapacLocalCrawler,
    trapac_oak.OakTrapacLocalCrawler,
    trapac_jax.JaxTrapacLocalCrawler,
]

TERMINALS_CLASS_MAP = {t.code: t for t in TERMINALS}


CRAWLER_MAP = {
    **CARRIER_CLASS_MAP,
    **TERMINALS_CLASS_MAP,
}

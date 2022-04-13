from carriers import cmdu, eglv, hlcu, mscu, oolu, whlc, zimu
from terminals import trapac_jax, trapac_la, trapac_oak

CARRIERS = [
    zimu.ZimuLocalCrawler,
    whlc.WhlcLocalCrawler,
    eglv.EglvLocalCrawler,
    mscu.MscuLocalCrawler,
    cmdu.CmduLocalCrawler,
    oolu.OoluLocalCrawler,
    hlcu.HlcuLocalCrawler,
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

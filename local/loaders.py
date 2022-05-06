from carriers import cmdu, eglv, mscu, whlc, zimu

CARRIERS = [
    zimu.ZimuLocalCrawler,
    whlc.WhlcLocalCrawler,
    eglv.EglvLocalCrawler,
    mscu.MscuLocalCrawler,
    cmdu.CmduLocalCrawler,
]

CARRIER_CLASS_MAP = {c.code: c for c in CARRIERS}

CRAWLER_MAP = {
    **CARRIER_CLASS_MAP,
}

# 12LU

FlowChart
===
```

               START
                 |
                 ⌵
        +------------------+
        | Container Status | <--+
        +--------+----+----+    |
                 |    |         ^ page_no < total_page_no
                 |    ⌵         |
                 ⌵    +---->----+
              FINISH

```

Container Status
===
## 目的
response json 上有我們要的 container status

## 準備
page_no: 1 to total page

## Flow
如果 container statuses 太多換頁，則根據 response json data 的 total page 來重發 Container Status

```
method = 'GET'
URL = 'http://www.nbosco.com/sebusiness/ecm/ContainerMovement/selectCmContainerCurrent?t={timestamp}&blNo={mbl_no}&pageNum={page_no}&pageSize=20'
```

## requests
```
requests.get(
    url=URL,
)
```

## scrapy
```
scrapy.Request(
    url=URL
)
```


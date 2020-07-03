###### tags: `Document`

# PABV

Cookies
===
## 目的
取得 Cookies，給後面的 RoutingRule 使用

## Flow
用 Selenium 去抓 Cookies
等到 front_www_pilship_com, TS01a292b3 這兩個 cookies 存在時，取出所有的 Cookies
![](./picture/Cookies.png)


Track
===
## 目的
取得 Mbl, Vessl, Container 的資訊


## 準備
Cookies
mbl_no

```
method = 'GET'
URL = 'https://www.pilship.com/shared/ajax/?fn=get_tracktrace_bl&ref_num={mbl_no}'
```

## postman

![](./picture/Track.png)

## scrapy

```
scrapy.Request(url=URL)
```

## requests

```
requests.get(url=URL)
```

Container
===
## 目的
取得 Container Status 的資訊

## 準備
Cookies
mbl_no
container_no

```
method = 'GET'
URL = 'https://www.pilship.com/shared/ajax/?fn=get_track_container_status&search_type=bl'&search_type_no={mbl_no}&ref_num={container_id}'
```

## postman

![](./picture/Container.png)


## scrapy

```
scrapy.Request(url=URL)
```

## requests

```
requests.get(url=URL)
```
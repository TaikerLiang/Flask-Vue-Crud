# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ExportFinalData(scrapy.Item):
    pass


class ExportErrorData(scrapy.Item):
    category = scrapy.Field()
    reason = scrapy.Field()


class LocationItem(scrapy.Item):
    name = scrapy.Field()
    un_lo_code = scrapy.Field()
    firms_code = scrapy.Field()


class MblItem(scrapy.Item):
    mbl_no = scrapy.Field()
    vessel = scrapy.Field()
    voyage = scrapy.Field()
    por = scrapy.Field(serializer=LocationItem)
    pol = scrapy.Field(serializer=LocationItem)
    pod = scrapy.Field(serializer=LocationItem)
    final_dest = scrapy.Field(serializer=LocationItem)
    por_etd = scrapy.Field()
    por_atd = scrapy.Field()
    etd = scrapy.Field()
    atd = scrapy.Field()
    eta = scrapy.Field()
    ata = scrapy.Field()
    bl_type = scrapy.Field()
    deliv_eta = scrapy.Field()
    deliv_ata = scrapy.Field()
    cargo_cutoff_date = scrapy.Field()
    surrendered_status = scrapy.Field()


class VesselItem(scrapy.Item):
    vessel = scrapy.Field()
    voyage = scrapy.Field()
    pol = scrapy.Field(serializer=LocationItem)
    pod = scrapy.Field(serializer=LocationItem)
    etd = scrapy.Field()
    eta = scrapy.Field()
    atd = scrapy.Field()
    ata = scrapy.Field()

    @property
    def key(self):
        return self['vessel']


class ContainerItem(scrapy.Item):
    container_no = scrapy.Field()
    last_free_day = scrapy.Field()
    empty_pickup_date = scrapy.Field()
    empty_return_date = scrapy.Field()
    full_pickup_date = scrapy.Field()
    full_return_date = scrapy.Field()

    @property
    def key(self):
        return self['container_no']


class ContainerStatusItem(scrapy.Item):
    container_no = scrapy.Field()
    description = scrapy.Field()
    timestamp = scrapy.Field()
    location = scrapy.Field(serializer=LocationItem)
    transport = scrapy.Field()

    @property
    def key(self):
        return self['container_no']

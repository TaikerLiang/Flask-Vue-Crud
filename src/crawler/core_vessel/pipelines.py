import pprint


class VesselItemPipeline:

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        return item

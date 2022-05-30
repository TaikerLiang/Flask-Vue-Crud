import logging
import random
import string
import time
from typing import List

import scrapy
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

from crawler.core.base_new import DUMMY_URL_DICT, RESULT_STATUS_ERROR, SEARCH_TYPE_MBL
from crawler.core.exceptions_new import AccessDeniedError, SuspiciousOperationError
from crawler.core.items_new import DataNotFoundItem, EndItem
from crawler.core.selenium import ChromeContentGetter
from crawler.core_carrier.base_spiders_new import BaseMultiCarrierSpider
from crawler.core_carrier.items_new import BaseCarrierItem, DebugItem
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.spiders.carrier_zimu import MainInfoRoutingRule

logger = logging.getLogger("carrier-zimu-multi")


class CarrierZimuSpider(BaseMultiCarrierSpider):
    name = "carrier_zimu_multi"
    custom_settings = {
        **BaseMultiCarrierSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(CarrierZimuSpider, self).__init__(*args, **kwargs)

        self._content_getter = ContentGetter()

        rules = [
            MultiMainInfoRoutingRule(self._content_getter),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = MultiMainInfoRoutingRule.build_request_option(
            search_nos=self.search_nos, task_ids=self.task_ids
        )
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, (BaseCarrierItem, DataNotFoundItem, EndItem)):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                cookies=option.cookies,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
            )
        else:
            zip_list = list(zip(meta["task_ids"], meta["search_nos"]))
            raise SuspiciousOperationError(
                task_id=meta["task_ids"][0],
                search_type=self.search_type,
                reason=f"Unexpected request method: `{option.method}`, on (task_id, search_no): {zip_list}",
            )


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={"search_nos": search_nos, "task_ids": task_ids},
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        if len(search_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        search_nos = search_nos[1:]

        yield MultiMainInfoRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)


class MultiMainInfoRoutingRule(MainInfoRoutingRule):
    name = "MAIN_INFO"

    def __init__(self, content_getter):
        self._content_getter = content_getter

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def handle(self, response):
        search_nos = response.meta["search_nos"]
        task_ids = response.meta["task_ids"]
        current_search_nos = search_nos[0]
        current_task_id = task_ids[0]
        info_pack = {
            "task_id": current_task_id,
            "search_no": current_search_nos,
            "search_type": SEARCH_TYPE_MBL,
        }

        response_text = self._content_getter.search_and_return(mbl_no=current_search_nos)
        response_selector = scrapy.Selector(text=response_text)

        if self._content_getter.check_denied():
            raise AccessDeniedError(**info_pack, reason="Blocked during searching")

        if self._is_not_found(response_selector):
            yield DataNotFoundItem(
                **info_pack,
                status=RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
            yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
            return

        for item in self._handle_item(response=response_selector, info_pack=info_pack):
            yield item

        yield EndItem(task_id=current_task_id)

        yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)


class ContentGetter(ChromeContentGetter):
    def __init__(self):
        super().__init__()

    def _accept_cookie(self):
        accept_btn_css = "#onetrust-accept-btn-handler"
        try:
            cookie_btn = self._driver.find_element_by_css_selector(accept_btn_css)
            cookie_btn.click()
        except (TimeoutException, NoSuchElementException):
            pass

    def check_denied(self):
        response = scrapy.Selector(text=self._driver.page_source)

        alter_msg = response.xpath("/html/body/h1")
        if alter_msg:
            return True
        return False

    def randomize(self, random_count):
        probabilities = [
            0.3,  # typing
            0.1,  # mouse movement
            0.2,  # click
        ]

        if self._driver.current_url != "https://www.zim.com/tools/track-a-shipment":
            self._driver.get("https://www.zim.com/tools/track-a-shipment")

        for i in range(random_count):
            self.resting_mouse(end=[random.randint(10, 1900), random.randint(200, 1060)])
            if random.random() < probabilities[0]:
                search_bar = self._driver.find_element_by_css_selector("input[name='consnumber']")
                self.slow_type(search_bar, self.get_random_string())
                search_bar.send_keys(Keys.RETURN)
                time.sleep(2)
                search_bar = self._driver.find_element_by_css_selector("input[name='consnumber']")
                for _ in range(random.randint(6, 9)):
                    search_bar.send_keys(Keys.BACKSPACE)
                    time.sleep(float(random.uniform(0.05, 0.3)))

            if random.random() < probabilities[1]:
                self.resting_mouse(end=[random.randint(10, 1900), random.randint(200, 1060)])

            if random.random() < probabilities[2]:
                self.click_mouse()
                time.sleep(2)

            if self._driver.current_url != "https://www.zim.com/tools/track-a-shipment":
                self._driver.back()

    def search(self, mbl_no: str):
        self._driver.get("https://www.zim.com/tools/track-a-shipment")
        if self.check_denied():
            return

        self.randomize(random.randint(1, 3))
        self._accept_cookie()
        self.close_questionnaire()
        try:
            self._driver.find_element_by_xpath('//*[@id="popup_module"]/div/div/button/span').click()
        except NoSuchElementException:
            pass

        self.randomize(random.randint(1, 3))

        try:
            search_bar = self._driver.find_element_by_css_selector("input[name='consnumber']")
            ActionChains(self._driver).move_to_element(search_bar).click().perform()
            self.slow_type(search_bar, mbl_no)
            search_bar.send_keys(Keys.RETURN)
            time.sleep(2)
        except (NoSuchElementException, StaleElementReferenceException):
            self.retry(mbl_no)

        self.close_questionnaire()

        try:
            self._driver.find_element_by_xpath('//*[@id="popup_module"]/div/div/button/span').click()
        except NoSuchElementException:
            pass

        return self._driver.page_source

    def get_random_string(self):
        return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(3, 5)))

    def close_questionnaire(self):
        try:
            self._driver.find_element_by_xpath('//*[@id="error-modal-newsletter-popup"]/div/div/button[1]').click()
        except:  # noqa: E722
            pass

    def retry(self, mbl_no: str):
        logger.info(f"retry {self._driver.current_url}")
        if self._driver.current_url != "chrome://welcome/":
            self._driver.back()
        if self._driver.current_url != "https://www.zim.com/tools/track-a-shipment":
            self._driver.get("https://www.zim.com/tools/track-a-shipment")

        if self.check_denied():
            return

        self.randomize(random.randint(1, 3))
        self._accept_cookie()
        self.close_questionnaire()

        if random.randint(1, 6) > 4:
            icon = self._driver.find_element_by_xpath("/html/body/div[4]/header/div[3]/div/div[1]/a/img")
            ActionChains(self._driver).move_to_element(icon).click().perform()
            self._driver.back()
            self.randomize(random.randint(1, 3))

        if random.randint(1, 6) > 4:
            small_icon = self._driver.find_element_by_xpath(
                '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div/div[2]/button'
            )
            ActionChains(self._driver).move_to_element(small_icon).click().perform()
            self.randomize(random.randint(1, 3))

        if random.randint(1, 6) > 4:
            contact_us = self._driver.find_element_by_xpath("/html/body/div[4]/header/div[2]/ul/li[1]/ul/li[2]/a")
            ActionChains(self._driver).move_to_element(contact_us).click().perform()
            self._driver.back()
            self.scroll_down(wait=False)
            self.randomize(random.randint(1, 3))

        self.resting_mouse(end=[random.randint(1600, 1750), random.randint(400, 850)])
        search_bar = self._driver.find_element_by_css_selector("input[name='consnumber']")

        if random.randint(1, 6) > 4:
            for _ in range(random.randint(15, 20)):
                search_bar.send_keys(Keys.BACKSPACE)
                time.sleep(float(random.uniform(0.05, 0.15)))
            self.slow_type(search_bar, self.get_random_string())
            search_bar.send_keys(Keys.RETURN)
            time.sleep(2)
            for _ in range(random.randint(6, 9)):
                search_bar.send_keys(Keys.BACKSPACE)
                time.sleep(float(random.uniform(0.05, 0.3)))

        if search_bar.get_attribute("value") != mbl_no:
            now_str = search_bar.get_attribute("value")
            for _ in range(random.randint(len(now_str), len(now_str) + 3)):
                search_bar.send_keys(Keys.BACKSPACE)
                time.sleep(float(random.uniform(0.05, 0.15)))
            self.slow_type(search_bar, mbl_no)

        self.close_questionnaire()
        search_bar.send_keys(Keys.RETURN)
        time.sleep(2)
        self.close_questionnaire()

    def search_and_return(self, mbl_no: str):
        # 10% chance to retry to increase chaos
        if random.random() < 0.1:
            self.retry(mbl_no)
        else:
            self.search(mbl_no=mbl_no)

        if self.check_denied():
            try:
                self.retry(mbl_no)
            finally:
                if self.check_denied():
                    return ""

        rnd = random.randint(1, 8)
        if rnd > 6:
            try:
                new_icon = self._driver.find_element_by_xpath(
                    '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div[2]/div[1]/div/dl[1]/dt[2]/a/span'
                )
                ActionChains(self._driver).move_to_element(new_icon).click().perform()
            except NoSuchElementException:
                self.retry(mbl_no)
        elif rnd > 3:
            try:
                bus_icon = self._driver.find_element_by_xpath(
                    '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div[2]/div[1]/div/dl[2]/dd/a'
                )
                ActionChains(self._driver).move_to_element(bus_icon).click().perform()
                windows = self._driver.window_handles
                if len(windows) > 1:
                    self._driver.switch_to.window(windows[1])
                    self._driver.close()
                    self._driver.switch_to.window(windows[0])
            except NoSuchElementException:
                self.retry(mbl_no)

        self.resting_mouse(end=[random.randint(1600, 1750), random.randint(400, 850)])
        self.scroll_down(wait=False)

        return self._driver.page_source

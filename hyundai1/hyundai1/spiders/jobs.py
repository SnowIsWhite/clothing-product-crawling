# -*- coding: utf-8 -*-
import scrapy
import os
import sys
import time
import random
import urllib.parse
from time import gmtime, strftime
from scrapy import Request
from scrapy.utils.python import to_native_str
from six.moves.urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains as chains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException

DELAY_TIME = 1
WHILE_TRIAL = 10
# PROGRESS_DIR = './hyundai1_progress.txt'
# RESULT_DIR = './hyundai1_result.txt'
# CHROME_DRIVER = '/Users/jaeickbae/Documents/projects/Web_Crawl/selenium_drivers/chromedriver'
PROGRESS_DIR = '/home/ubuntu/projects/crawling/progress/ssense_progress.txt'
RESULT_DIR = '/home/ubuntu/projects/crawling/result/ssense_result.txt'
CHROME_DRIVER = '/usr/local/bin/chromedriver'

def __delay_time__():
    print("Waiting for a delay...\n")
    delay = DELAY_TIME + random.random()
    time.sleep(delay)
    return

def __get_curr_time__():
    return strftime("%Y-%m-%d %H:%M:%S", gmtime())

# write progress
def __record_progress__(url):
    print("\n\nWrite progress\n\n")
    with open(PROGRESS_DIR, 'a') as f:
        f.write(url)
        f.write('\n')

def __read_progress__():
    with open(PROGRESS_DIR, 'r') as f:
        progress = f.readlines()
    read = []
    for p in progress:
        read.append(p.strip())
    return read

def __record_data__(url, cat, brand, name, price, prod_num, prod_desc, color):
    dat = {'url': url, 'category': cat, 'brand': brand, 'name': name, 'price': price, \
    'prod_num': prod_num, 'prod_desc': prod_desc, 'color': color}

    with open(RESULT_DIR, 'a') as f:
        f.write(str(dat)+'\n')

class JobsSpider(scrapy.Spider):
    name = 'jobs'
    rotate_user_agent = True
    allowed_domains = ['www.thehyundai.com/front/dpa/searchSectItem.thd?sectId=2005&MainpageGroup=Category&GroupbannerName=manf']
    start_urls = ['http://www.thehyundai.com/front/dpa/searchSectItem.thd?sectId=2005&MainpageGroup=Category&GroupbannerName=manf']

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
        self.driver = webdriver.Chrome(CHROME_DRIVER, chrome_options=options)
        print("Waiting for a webdriver...\n")
        self.driver.implicitly_wait(3)
        self.progress = __read_progress__()

    def __scroll_element_into_view__(self, element):
        """Scroll element into view"""
        y = element.location['y']
        self.driver.execute_script('window.scrollTo(0, {0})'.format(y))

    def parse(self, response):
        self.driver.get(response.url)
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5];},});")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})")
        self.driver.execute_script("const getParameter = WebGLRenderingContext.getParameter;WebGLRenderingContext.prototype.getParameter = function(parameter) {if (parameter === 37445) {return 'NVIDIA Corporation'} if (parameter === 37446) {return 'NVIDIA GeForce GTX 980 Ti OpenGL Engine';}return getParameter(parameter);};")

        self.sel = scrapy.Selector(text = self.driver.page_source)

        caturls = self.sel.xpath('//ul[@class="cmenu"]/li/ul/li/a/@href').extract()
        catlist = self.sel.xpath('//ul[@class="cmenu"]/li/ul/li/a/text()').extract()
        for catidx, cat in enumerate(catlist):
            category = cat.strip()
            url = urljoin('http://www.thehyundai.com/', caturls[catidx])
            self.driver.get(url)
            __delay_time__()
            self.sel = scrapy.Selector(text = self.driver.page_source)

            print("\n\n{} clicked\n\n".format(category))

            # brands
            brand_lists = self.sel.xpath('//ul[@class="brand-list-wrap"]/li/a/text()').extract()
            for brandidx, brand in enumerate(brand_lists):
                brand = brand.strip().split("(")[0].strip()

                # check if 'load more' element exists
                elment_exists = False
                try:
                    xpath = '//a[@class="btn-more-tog"]'
                    self.driver.find_element_by_xpath(xpath)
                    element_exists = True
                except NoSuchElementException:
                    element_exists = False

                if element_exists == True:
                    load_more_text = self.sel.xpath('//a[@class="btn-more-tog"]/text()').extract_first()
                    if load_more_text == '더보기':
                        element_exists = True
                    else:
                        element_exists = False

                if element_exists == True:
                    # click
                    try:
                        actions = chains(self.driver)
                        xpath = '//a[@class="btn-more-tog"]'
                        load_more = self.driver.find_element_by_xpath(xpath)
                        actions.move_to_element(load_more).perform()
                        to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    except TimeoutException:
                        print("\n\nTimeoutExceptoin while clicking {} load more".format(category))
                        continue
                    self.driver.execute_script('arguments[0].click()', to_be_clicked)
                    __delay_time__()
                    self.sel = scrapy.Selector(text = self.driver.page_source)
                    print('\n\n {} load more clicked\n\n'.format(category))

                # click brand
                try:
                    actions = chains(self.driver)
                    if element_exists:
                        xpath = '//ul[@class="brand-list-wrap open"]/li[{}]/a'.format(str(brandidx+1))
                    else:
                        xpath = '//ul[@class="brand-list-wrap"]/li[{}]/a'.format(str(brandidx+1))
                    brand_click = self.driver.find_element_by_xpath(xpath)
                    actions.move_to_element(brand_click).perform()
                    to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                except TimeoutException:
                    print("\n\nTimeoutExceptoin while clicking {} ".format(brand))
                    continue
                self.driver.execute_script('arguments[0].click()', to_be_clicked)
                __delay_time__()
                self.sel = scrapy.Selector(text = self.driver.page_source)
                print('\n\n {} clicked\n\n'.format(brand))

                curr_page_num = 1
                while True:
                    # fetch product data
                    prod_urls = self.sel.xpath('//ul[@class="product-list type1"]/li/div/div[1]/a/@href').extract()
                    names = self.sel.xpath('//ul[@class="product-list type1"]/li/div/div[1]/a/img/@alt').extract()
                    imgs = self.sel.xpath('//ul[@class="product-list type1"]/li/div/div[1]/a/img/@src').extract()
                    prices = self.sel.xpath('//ul[@class="product-list type1"]/li/div/div[2]/div/span[1]/text()').extract()
                    for prod_idx, produ in enumerate(prod_urls):
                        prod_url = urljoin('https://www.thehyundai.com/', produ)
                        name = names[prod_idx]
                        img = imgs[prod_idx]
                        prod_desc = ''
                        prod_num = ''
                        price = prices[prod_idx]
                        color = {}
                        c = ''
                        color[c] = {'img_url': img, 'size': '', 'rel': []}

                        # write progress
                        __record_progress__(prod_url)
                        # write data
                        __record_data__(prod_url, category, brand, name, price, prod_num, prod_desc, color)

                    # next page
                    page_list = self.sel.xpath('//*[@id="container"]/div[2]/div/div[2]/ul/li/a/text()').extract()
                    next_page_num = curr_page_num + 1
                    if str(next_page_num) not in page_list:
                        next_button_exists = False
                        try:
                            xpath = '//*[@id="container"]/div[2]/div/div[2]/ul/li/a[@class="direction next_1"]'
                            self.driver.find_element_by_xpath(xpath)
                            next_button_exists = True
                        except NoSuchElementException:
                            next_button_exists = False
                        if next_button_exists:
                            # click next button
                            prev_page_item = self.sel.xpath('//*[@id="product-list"]/li[1]/div/div[2]/a/text()').extract_first()
                            while True:
                                xpath = '//*[@id="container"]/div[2]/div/div[2]/ul/li/a[@class="direction next_1"]'
                                try:
                                    to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                                except TimeoutException:
                                    print("\n\nERROR WHILE CILCKING Next Button after {}".format(str(curr_page_num)))
                                    continue
                                self.driver.execute_script('arguments[0].click()', to_be_clicked)
                                __delay_time__()
                                self.sel = scrapy.Selector(text = self.driver.page_source)
                                curr_item = self.sel.xpath('//*[@id="product-list"]/li[1]/div/div[2]/a/text()').extract_first()
                                if prev_page_item != curr_item:
                                    print("\n\nNEXT BUTTON CLICKED: page now {}\n\n".format(str(curr_page_num+1)))
                                    curr_page_num += 1
                                    break
                        else:
                            # final page
                            break

                    else:
                        # click next page
                        prev_page_item = self.sel.xpath('//*[@id="product-list"]/li[1]/div/div[2]/a/text()').extract_first()
                        while True:
                            xpath = '//*[@id="container"]/div[2]/div/div[2]/ul/li/a[contains(text(), "{}")]'.format(str(next_page_num))
                            try:
                                to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            except TimeoutException:
                                print("\n\nERROR WHILE CILCKING next page")
                                continue
                            self.driver.execute_script('arguments[0].click()', to_be_clicked)
                            __delay_time__()
                            self.sel = scrapy.Selector(text = self.driver.page_source)
                            curr_item = self.sel.xpath('//*[@id="product-list"]/li[1]/div/div[2]/a/text()').extract_first()
                            if prev_page_item != curr_item:
                                print("\n\nNEXT PAGE CLICKED: page now {}\n\n".format(str(next_page_num)))
                                curr_page_num += 1
                                break

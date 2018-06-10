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

DELAY_TIME = 2
WHILE_TRIAL = 10
PROGRESS_DIR = '/home/ubuntu/progress/sivillage_progress.txt'
RESULT_DIR = '/home/ubuntu/result/sivillage_result.txt'
CHROME_DRIVER = '/usr/local/bin/chromedriver'

def __delay_time__():
    print("Waiting for a delay...\n")
    delay = DELAY_TIME + random.random()
    time.sleep(delay)
    return

def __get_curr_time__():
    return strftime("%Y-%m-%d %H:%M:%S", gmtime())

# write progress
def __record_progress__(prod_num):
    with open(PROGRESS_DIR, 'a') as f:
        f.write(prod_num)
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
    'prod_num': prod_num, 'prod_desc': 'prod_desc', 'color': color}

    with open(RESULT_DIR, 'a') as f:
        f.write(str(dat)+'\n')

class JobsSpider(scrapy.Spider):
    name = 'jobs'
    rotate_user_agent = True
    allowed_domains = ['fashion.sivillage.com/display/displayCategoryFA?rtCatNo=010000029506&dspCatNo=010000029507']
    start_urls = ['http://fashion.sivillage.com/display/displayCategoryFA?rtCatNo=010000029506&dspCatNo=010000029507']

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
        cat_list = self.sel.xpath('//*[@id="leftMenu"]/div/div/div/ul/li/a/text()').extract()
        for ci, c in enumerate(cat_list):
            cat_list[ci] = c.strip()

        for catidx, category in enumerate(cat_list):
            xpath = '//*[@id="leftMenu"]/div/div/div/ul/li[{}]/a'.format(str(catidx+1))

            # click category
            try:
                actions = chains(self.driver)
                xpath = '//*[@id="leftMenu"]/div/div/div/ul/li[{}]/a'.format(str(catidx+1))
                cat = self.driver.find_element_by_xpath(xpath)
                actions.move_to_element(cat).perform()
                to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            except TimeoutException:
                print("\n\nERROR WHILE CLICKING color")
                continue
            self.driver.execute_script('arguments[0].click()', to_be_clicked)
            __delay_time__()
            self.sel = scrapy.Selector(text = self.driver.page_source)
            print('\n\n {} clicked\n\n'.format(category))

            curr_page_num = 1
            while True:
                # crawl items
                xpath = '//*[@id="productListDiv"]/div/div/ul/li'
                item_lists = self.sel.xpath(xpath).extract()
                for li_idx in range(len(item_lists)):
                    curr_url = self.driver.current_url
                    xpath = '//*[@id="productListDiv"]/div/div/ul/li[{}]/div/div/a/@href'.format(str(li_idx+1))
                    script_res = self.sel.xpath(xpath).extract_first()
                    script_res = script_res.split("'")
                    productNo = script_res[1]
                    infwPathTp = script_res[3]
                    infwPathNo = script_res[5]
                    brand = self.sel.xpath('//*[@id="productListDiv"]/div/div/ul/li[{}]/div[2]/div[1]/span/text()'.format(str(li_idx+1))).extract_first()
                    url_string = "productNo={}&infwPathTp={}&infwPathNo={}".format(productNo,infwPathTp,infwPathNo)
                    url = 'http://fashion.sivillage.com/product/productDetail?' + url_string
                    self.driver.get(url)
                    __delay_time__()
                    self.sel = scrapy.Selector(text = self.driver.page_source)

                    # scrape page
                    name = self.sel.xpath('//*[@id="content"]/div[1]/div[2]/div[1]/div[4]/text()').extract_first().strip()
                    prod_num = self.sel.xpath('//*[@id="content"]/div[1]/div[2]/div[1]/div[2]/text()').extract_first().strip()
                    if prod_num in self.progress:
                        self.driver.get(curr_url)
                        __delay_time__()
                        self.sel = scrapy.Selector(text = self.driver.page_source)
                        continue

                    price = self.sel.xpath('//*[@id="content"]/div[1]/div[2]/div[1]/div[5]/span/text()').extract_first()
                    prod_desc = self.sel.xpath('//*[@id="content"]/div[1]/div[2]/div[6]/dl[1]/dd/div/div[1]/span[2]/text()').extract()
                    if prod_desc is None:
                        prod_desc = ''
                    else:
                        prod_desc = ' '.join(prod_desc)
                    colors = self.sel.xpath('//*[@id="content"]/div[1]/div[2]/div[4]/div/dl[1]/dd/ul/li/a/img/@alt').extract()
                    color = {}

                    for c_idx, c in enumerate(colors):
                        if c not in color:
                            color[c] = {'img_url': [], 'size': [], 'rel': []}
                        else:
                            continue

                        # click color
                        try:
                            actions = chains(self.driver)
                            xpath = '//*[@id="content"]/div[1]/div[2]/div[4]/div/dl[1]/dd/ul/li[{}]/a'.format(str(c_idx+1))
                            col = self.driver.find_element_by_xpath(xpath)
                            actions.move_to_element(col).perform()
                            to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        except TimeoutException:
                            print("\n\nERROR WHILE CLICKING color")
                            continue
                        self.driver.execute_script('arguments[0].click()', to_be_clicked)
                        __delay_time__()
                        self.sel = scrapy.Selector(text = self.driver.page_source)

                        size = self.sel.xpath('//ul[@class="size"]/li/a[not(contains(@class,"disabled"))]/text()').extract()
                        color[c]['size'] = size
                        imgs = self.sel.xpath('//*[@id="mImgDiv"]/div/a/img/@src').extract()
                        color[c]['img_url'] = imgs

                    # write progress
                    __record_progress__(prod_num)
                    # write data
                    __record_data__(url, category, brand, name, price, prod_num, prod_desc, color)
                    # go back to main page
                    self.driver.get(curr_url)
                    __delay_time__()
                    self.sel = scrapy.Selector(text = self.driver.page_source)

                # click next page
                page_list = self.sel.xpath('//div[@class="paging"]/a/text()').extract()
                print(page_list)
                next_page_num = curr_page_num + 1
                if str(next_page_num) not in page_list:
                    if 'Next' in page_list:
                        # click next button
                        xpath = '//*[@id="productListDiv"]/div/div/ul/li[1]/div/div/a/@data-prod-no'
                        prev_page_item = self.sel.xpath(xpath).extract_first()
                        while True:
                            xpath = '//div[@class="paging"]/a[contains(text(), "Next")]'
                            try:
                                to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            except TimeoutException:
                                print("\n\nERROR WHILE CILCKING Next Button")
                                continue
                            self.driver.execute_script('arguments[0].click()', to_be_clicked)
                            __delay_time__()
                            self.sel = scrapy.Selector(text = self.driver.page_source)
                            xpath = '//*[@id="productListDiv"]/div/div/ul/li[1]/div/div/a/@data-prod-no'
                            curr_item = self.sel.xpath(xpath).extract_first()
                            if prev_page_item != curr_item:
                                print("\n\nNEXT BUTTON CLICKED: page now {}\n\n".format(str(curr_page_num+1)))
                                curr_page_num += 1
                                break
                    else:
                        # final page
                        break
                else:
                    # click next_page
                    xpath = '//*[@id="productListDiv"]/div/div/ul/li[1]/div/div/a/@data-prod-no'
                    prev_page_item = self.sel.xpath(xpath).extract_first()
                    while True:
                        xpath = '//div[@class="paging"]/a[contains(text(), "{}")]'.format(str(next_page_num))
                        try:
                            to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        except TimeoutException:
                            print("\n\nERROR WHILE CILCKING next page")
                            continue
                        self.driver.execute_script('arguments[0].click()', to_be_clicked)
                        __delay_time__()
                        self.sel = scrapy.Selector(text = self.driver.page_source)
                        xpath = '//*[@id="productListDiv"]/div/div/ul/li[1]/div/div/a/@data-prod-no'
                        curr_item = self.sel.xpath(xpath).extract_first()
                        if prev_page_item != curr_item:
                            print("\n\nNEXT PAGE CLICKED: page now {}\n\n".format(str(curr_page_num+1)))
                            curr_page_num += 1
                            break

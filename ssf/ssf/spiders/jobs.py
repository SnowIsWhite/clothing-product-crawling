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
# PROGRESS_DIR = './ssf_progress.txt'
# RESULT_DIR = './ssf_result.txt'
# CHROME_DRIVER = '/Users/jaeickbae/Documents/projects/Web_Crawl/selenium_drivers/chromedriver'
PROGRESS_DIR = '/home/ubuntu/projects/crawling/progress/ssf_progress.txt'
RESULT_DIR = '/home/ubuntu/projects/crawling/result/ssf_result.txt'
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
    'prod_num': prod_num, 'prod_desc': prod_desc, 'color': color}

    with open(RESULT_DIR, 'a') as f:
        f.write(str(dat)+'\n')

class JobsSpider(scrapy.Spider):
    name = 'jobs'
    rotate_user_agent = True
    allowed_domains = ['www.ssfshop.com/Men/list?dspCtgryNo=SFMA42&brandShopNo=&brndShopId=&etcCtgryNo=&ctgrySectCd=&keyword=&leftBrandNM=']
    start_urls = ['http://www.ssfshop.com/Men/list?dspCtgryNo=SFMA42&brandShopNo=&brndShopId=&etcCtgryNo=&ctgrySectCd=&keyword=&leftBrandNM=']

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
        self.driver.set_page_load_timeout(600)

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
        cat_list = self.sel.xpath('/html/body/div[3]/nav/ul[1]/li[2]/ul/li/a/text()').extract()

        for catidx, category in enumerate(cat_list):
            if catidx < 9:
                # skip 'All'
                continue
            # click category
            try:
                actions = chains(self.driver)
                xpath = '/html/body/div[3]/nav/ul[1]/li[2]/ul/li[{}]/a'.format(str(catidx+1))
                cat = self.driver.find_element_by_xpath(xpath)
                actions.move_to_element(cat).perform()
                to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            except TimeoutException:
                print("\n\nTimeoutExceptoin while clicking category {}".format(category))
                continue
            self.driver.execute_script('arguments[0].click()', to_be_clicked)
            __delay_time__()
            self.sel = scrapy.Selector(text = self.driver.page_source)
            print('\n\n {} clicked\n\n'.format(category))

            curr_page_num = 1
            while True:
                # crawl items
                item_lists = self.sel.xpath('//*[@id="dspGood"]/li/@data-prdno').extract()
                for li_idx, prod_num in enumerate(item_lists):
                    curr_url = self.driver.current_url
                    xpath = '//*[@id="dspGood"]/li[{}]/a/@onclick'.format(str(li_idx+1))
                    script_res = self.sel.xpath(xpath).extract_first().split("'")
                    brand = script_res[1]
                    prod_num = script_res[3]
                    if prod_num in self.progress:
                        continue
                    url = "http://www.ssfshop.com/{}/{}/good?dspCtgryNo=&brandShopNo=&brndShopId=".format(brand, prod_num)
                    print('\n\n\n\n{}\n\n\n\n'.format(url))
                    while True:
                        try:
                            self.driver.get(url)
                            break
                        except TimeoutException:
                            print(curr_url)
                            try:
                                self.driver.get(curr_url)
                                break
                            except TimeoutException:
                                continue
                    __delay_time__()
                    self.sel = scrapy.Selector(text = self.driver.page_source)

                    # scrape page
                    brand = self.sel.xpath('/html/body/div[3]/div[1]/section[2]/div[1]/div[2]/h3/a/text()').extract_first().strip().split('\xa0')[0]
                    name = self.sel.xpath('/html/body/div[3]/div[1]/section[2]/div[1]/div[2]/h1/text()').extract()[-1].strip()
                    price = self.sel.xpath('/html/body/div[3]/div[1]/section[2]/div[1]/div[2]/div[1]/em/text()').extract_first()
                    if '\xa0' in price:
                        price = price.strip('\xa0')
                    prod_desc = self.sel.xpath('//*[@id="about"]/div/text()').extract()
                    if prod_desc is None:
                        prod_desc = ''
                    else:
                        prod_desc = (' '.join(prod_desc)).strip()
                    color = {}
                    c = ''
                    color[c] = {'img_url': [], 'size': [], 'rel': []}
                    size_list = self.sel.xpath('//div[@class="option"]/ul/li/a/em/text()').extract()
                    size = []
                    for idx, s in enumerate(size_list):
                        if '(' in s.strip() or ')' in s.strip():
                            continue
                        size.append(s.strip().strip('/').strip())
                    img_script_list = self.sel.xpath('/html/body/div[3]/div[1]/section[2]/div[1]/div[1]/script/text()').extract()
                    imgs = []
                    for img_script in img_script_list:
                        temp = img_script.split('\\"')
                        if len(temp) == 1:
                            continue
                        else:
                            imgs.append(temp[1])
                    color[c]['img_url'] = imgs
                    color[c]['size'] = size

                    # write progress
                    __record_progress__(prod_num)
                    # write data
                    __record_data__(url, category, brand, name, price, prod_num, prod_desc, color)
                    # go back to main page
                    self.driver.get(curr_url)
                    __delay_time__()
                    self.sel = scrapy.Selector(text = self.driver.page_source)

                # click next page
                page_list = self.sel.xpath('//div[@id="pagingArea"]/a/text()').extract()
                next_page_num = curr_page_num + 1
                if str(next_page_num) not in page_list:
                    next_btns_list = self.sel.xpath('//div[@id="pagingArea"]/a/@alt').extract()
                    if '다음페이지' in next_btns_list:
                        # click next button
                        prev_page_item = self.sel.xpath('//*[@id="dspGood"]/li[1]/a/img/@src').extract_first()
                        while True:
                            xpath = '//div[@id="pagingArea"]/a[contains(@alt, "{}")]'.format('다음페이지')
                            try:
                                to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            except TimeoutException:
                                print("\n\nERROR WHILE CILCKING Next Button")
                                continue
                            self.driver.execute_script('arguments[0].click()', to_be_clicked)
                            __delay_time__()
                            self.sel = scrapy.Selector(text = self.driver.page_source)
                            curr_item = self.sel.xpath('//div[@id="pagingArea"]/a/text()').extract_first()
                            if prev_page_item != curr_item:
                                print("\n\n\n\n\nNEXT BUTTON CLICKED: page now {}\n\n".format(str(curr_page_num+1)))
                                curr_page_num += 1
                                break
                    else:
                        # final page
                        break

                else:
                    # click next page
                    prev_page_item = self.sel.xpath('//*[@id="dspGood"]/li[1]/a/img/@src').extract_first()
                    while True:
                        xpath = '//div[@id="pagingArea"]/a[contains(text(), "{}")]'.format(str(next_page_num))
                        try:
                            to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        except TimeoutException:
                            print("\n\nERROR WHILE CILCKING next page")
                            continue
                        self.driver.execute_script('arguments[0].click()', to_be_clicked)
                        __delay_time__()
                        self.sel = scrapy.Selector(text = self.driver.page_source)
                        curr_item = self.sel.xpath('//*[@id="dspGood"]/li[1]/a/img/@src').extract_first()
                        if prev_page_item != curr_item:
                            print("\n\n\n\n\nNEXT PAGE CLICKED: page now {}\n\n".format(str(next_page_num)))
                            curr_page_num += 1
                            break

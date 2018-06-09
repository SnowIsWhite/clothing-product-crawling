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
PROGRESS_DIR = '/home/ubuntu/progress/handsome_progress.txt'
RESULT_DIR = '/home/ubuntu/result/handsome_result.txt'
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
    allowed_domains = ['www.thehandsome.com/ko/item/me']
    start_urls = ['http://www.thehandsome.com/ko/item/me/']

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

        upper_class_index = [3,4,5,6,7]

        for upidx in upper_class_index:
            subclass_xpath = '//*[@id="cate_m_main"]/li[3]/div/div/ul/li[{}]/ul/li/a/text()'.format(str(upidx))
            subclass_lists = response.xpath(subclass_xpath).extract()

            for subidx, subclass in enumerate(subclass_lists):
                xpath = '//*[@id="cate_m_main"]/li[3]/div/div/ul/li[{}]/ul/li[{}]/a'.format(str(upidx), str(subidx+1))

                # click sub category
                while True:
                    # click sub category
                    try:
                        actions = chains(self.driver)
                        man = self.driver.find_element_by_xpath('//*[@id="cate_m_main"]/li[3]/a[@href="/ko/item/me"]')
                        actions.move_to_element(man).perform()
                        to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    except TimeoutException:
                        print("\n\nERROR WHILE CLICKING {}".format(subclass))
                        continue
                    self.driver.execute_script('arguments[0].click()', to_be_clicked)
                    __delay_time__()
                    self.sel = scrapy.Selector(text = self.driver.page_source)
                    xpath = '//*[@id="bodyWrap"]/h3/span/a[3]/text()'
                    check = self.sel.xpath(xpath).extract_first()
                    if check == subclass:
                        break
                print(subclass + ' clicked\n')

                last_page = False
                urls = []
                while True:
                    xpath = '//*[@id="listBody"]/li'
                    lists= self.sel.xpath(xpath).extract()
                    for li_idx in range(len(lists)):
                        curr_url = self.driver.current_url
                        xpath = '//*[@id="listBody"]/li[{}]/div/a[1]/@href'.format(str(li_idx+1))
                        rel_url = self.sel.xpath(xpath).extract_first()
                        url = urllib.parse.urljoin('http://www.thehandsome.com/', rel_url)
                        self.driver.get(url)
                        __delay_time__()
                        self.sel = scrapy.Selector(text = self.driver.page_source)
                        # check page_source changes
                        #scrape page
                        # category, brand, name, price, prod_num, prod_desc, color, size, img, url
                        category = subclass
                        brand = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[1]/h4/a/span/span/text()').extract_first()
                        name = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[1]/h4/span/text()').extract_first().strip()
                        price = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[1]/p[1]/span/text()').extract_first()[1:]
                        prod_num = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[1]/p[2]/text()').extract_first().strip()
                        if prod_num in self.progress:
                            self.driver.get(curr_url)
                            __delay_time__()
                            self.sel = scrapy.Selector(text = self.driver.page_source)
                            continue
                        
                        xpath = '//*[@id="contentDiv"]/div[1]/div[1]/p[3]/text()'
                        prod_desc = self.sel.xpath(xpath).extract_first()
                        if prod_desc is None:
                            prod_desc = ''
                        else:
                            prod_desc = prod_desc.strip()
                        colors = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[3]/ul/li[1]/div/ul/li/a/@onmouseover').extract()
                        color = {}
                        # {'brand', 'name', 'product_num'}

                        for c_idx, c in enumerate(colors):
                            c = c.split("'")[1]
                            if c not in color:
                                color[c] = {'img_url': [], 'size': [], 'rel': []}
                            else:
                                continue
                            # click color
                            try:
                                actions = chains(self.driver)
                                xpath = '//*[@id="contentDiv"]/div[1]/div[3]/ul/li[1]/div/ul/li[{}]/a'.format(str(c_idx+1))
                                col = self.driver.find_element_by_xpath(xpath)
                                actions.move_to_element(col).perform()
                                to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            except TimeoutException:
                                print("\n\nERROR WHILE CLICKING color")
                                continue
                            self.driver.execute_script('arguments[0].click()', to_be_clicked)
                            __delay_time__()
                            self.sel = scrapy.Selector(text = self.driver.page_source)

                            # size and img by each color
                            size = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[3]/ul/li[2]/span[2]/ul/li/a[not(@class)]/text()').extract()
                            color[c]['size'] = size
                            imgs = self.sel.xpath('//*[@id="imageDiv"]/ul/li/img/@src').extract()
                            color[c]['img_url'] = imgs

                            # check existance of relevant item
                            try:
                                xpath = '//div[@class="related_evt"]'
                                self.driver.find_element_by_xpath(xpath)
                            except NoSuchElementException:
                                # continue to next color
                                continue

                            # go to relevant item
                            item_li = self.sel.xpath('//*[@id="referencesListContent"]/ul').extract()
                            for itemidx in range(len(item_li)):
                                try:
                                    actions = chains(self.driver)
                                    xpath = '//*[@id="referencesListContent"]/ul/li[{}]/a'.format(str(itemidx+1))
                                    item = self.driver.find_element_by_xpath(xpath)
                                    actions.move_to_element(item).perform()
                                    to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                                except NoSuchElementException:
                                    print("\n\nERROR WHILE CLICKING relevant item")
                                    continue
                                self.driver.execute_script('arguments[0].click()', to_be_clicked)
                                __delay_time__()
                                self.sel = scrapy.Selector(text = self.driver.page_source)

                                # get brand, name, product_num
                                rel_brand = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[1]/h4/a/span/span/text()').extract_first()
                                rel_name = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[1]/h4/span/text()').extract_first().strip()
                                rel_prod_num = self.sel.xpath('//*[@id="contentDiv"]/div[1]/div[1]/p[2]/text()').extract_first().strip()
                                color[c]['rel'].append({'rel_brand': rel_brand, 'rel_name': rel_name, 'rel_prod_num': rel_prod_num})
                                # go back to original item
                                self.driver.get(url)
                                __delay_time__()
                                self.sel = scrapy.Selector(text = self.driver.page_source)

                        # write progress
                        __record_progress__(prod_num)
                        # write data
                        __record_data__(url, category, brand, name, price, prod_num, prod_desc, color)
                        # go back to main page
                        self.driver.get(curr_url)
                        __delay_time__()
                        self.sel = scrapy.Selector(text = self.driver.page_source)

                    # click next page
                    xpath = '//*[@id="listBody"]/li[1]/div/a[1]/span[1]/img/@src'
                    prev_page = self.sel.xpath(xpath).extract_first()
                    cnt = 0
                    while True:
                        xpath = '//*[@id="bodyWrap"]/div[1]/div[2]/a[3]'
                        try:
                            to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        except TimeoutException:
                            print("\n\nERROR WHILE CILCKING next page")
                            continue
                        self.driver.execute_script('arguments[0].click()', to_be_clicked)
                        __delay_time__()

                        self.sel = scrapy.Selector(text = self.driver.page_source)
                        xpath = '//*[@id="listBody"]/li[1]/div/a[1]/span[1]/img/@src'
                        check = self.sel.xpath(xpath).extract_first()
                        if prev_page != check:
                            break
                        cnt += 1
                        if cnt > 4:
                            last_page = True
                            break
                    print("NEXT PAGE CLICKED\n\n")
                    if last_page == True:
                        break

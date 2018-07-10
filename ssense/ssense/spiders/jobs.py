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
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

DELAY_TIME = 1
WHILE_TRIAL = 10
# PROGRESS_DIR = './ssense_progress.txt'
# RESULT_DIR = './ssense_result.txt'
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
    print("Write progress...")
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
    allowed_domains = ['www.ssense.com/en-kr/men']
    start_urls = ['https://www.ssense.com/en-kr/men/']

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

        for i in range(2):
            target_idx = str(i+4)
            try:
                actions = chains(self.driver)
                xpath = '//*[@id="category-list"]/li[{}]/a'.format(target_idx)
                upper_cat = self.driver.find_element_by_xpath(xpath)
                actions.move_to_element(upper_cat).perform()
                to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            except TimeoutException:
                print("\n\nTimeoutExceptoin while clicking upper category {}".format(target_idx))
                continue
            self.driver.execute_script('arguments[0].click()', to_be_clicked)
            __delay_time__()
            self.sel = scrapy.Selector(text = self.driver.page_source)
            print('\n\n upper category {} clicked\n\n'.format(target_idx))

            cat_list = self.sel.xpath('//*[@id="category-list"]/li[{}]/ul/li/a/text()'.format(target_idx)).extract()
            cat_list = [cat.strip() for cat in cat_list]

            for catidx, cat in enumerate(cat_list):
                # if catidx == 0:
                #     # jacket is done
                #     continue
                try:
                    actions = chains(self.driver)
                    xpath = '//*[@id="category-list"]/li[{}]/ul/li[{}]/a'.format(target_idx, str(catidx+1))
                    category = self.driver.find_element_by_xpath(xpath)
                    actions.move_to_element(category).perform()
                    to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                except TimeoutException:
                    print("\n\nTimeoutExceptoin while clicking category {}".format(cat))
                    continue
                self.driver.execute_script('arguments[0].click()', to_be_clicked)
                __delay_time__()
                self.sel = scrapy.Selector(text = self.driver.page_source)
                print('\n\n category {} clicked\n\n'.format(cat))

                curr_page_num = 1
                while True:
                    # crawl items
                    prod_list = self.sel.xpath('//*[@id="wrap"]/div/div[1]/section/div[1]/div/figure/a/@href').extract()
                    main_prod_page_url = self.driver.current_url
                    for prod in prod_list:
                        url = urljoin('https://www.ssense.com/', prod)
                        if url in self.progress:
                            print("\n\nProduct already in progress {}\n\n".format(url))
                            continue
                        self.driver.get(url)
                        __delay_time__()
                        self.sel = scrapy.Selector(text = self.driver.page_source)

                        # prod page
                        prod_num = self.sel.xpath('//span[@class="product-sku"]/text()').extract_first()
                        if prod_num is None:
                            prod_num = ''
                        brand = self.sel.xpath('//h1[@class="product-brand"]/a/text()').extract_first()
                        name = self.sel.xpath('//h2[@class="product-name"]/text()').extract_first()
                        price = self.sel.xpath('//span[@class="price"]/text()').extract_first()
                        prod_desc = self.sel.xpath('//p[@class="vspace1 product-description-text"]/span/text()').extract()
                        prod_desc = ' '.join(prod_desc)
                        prod_desc = prod_desc.replace("'", "")
                        prod_desc = prod_desc.replace('"', '')
                        color = {}
                        c = ''
                        imgs = self.sel.xpath('//div[@class="product-images-container"]/div/div/div').extract()
                        imgs = [im.split('"')[5] for im in imgs]

                        size = self.sel.xpath('//*[@id="size"]/option/text()').extract()
                        size = [s.strip() for s in size][1:]
                        size = [s.split()[0] for s in size]

                        color[c] = {'img_url': imgs, 'size': size, 'rel': []}

                        # rel page
                        indicator = self.sel.xpath('//div[@class="related-product-tab inline-block smartphone-portrait-narrow-full-width"]/a/span[1]/text()').extract_first()
                        if indicator == 'Styled with':
                            rels = self.sel.xpath('//div[@class="related-product-container tab-container"]/div[2]/div/div/div/div/a/@href').extract()
                            for rel_url in rels:
                                rel_result = {}
                                rel_url = urljoin('https://www.ssense.com/', rel_url)
                                self.driver.get(rel_url)
                                __delay_time__()
                                self.sel = scrapy.Selector(text = self.driver.page_source)

                                # rel prod page
                                rel_result['rel_brand'] = self.sel.xpath('//h1[@class="product-brand"]/a/text()').extract_first()
                                rel_result['rel_name'] = self.sel.xpath('//h2[@class="product-name"]/text()').extract_first()
                                rel_prod_num = self.sel.xpath('//span[@class="product-sku"]/text()').extract_first()
                                if rel_prod_num is None:
                                    rel_prod_num = ''
                                rel_result['rel_prod_num'] = rel_prod_num
                                rel_prod_desc = self.sel.xpath('//p[@class="vspace1 product-description-text"]/span/text()').extract()
                                rel_prod_desc = ' '.join(rel_prod_desc)
                                rel_prod_desc = rel_prod_desc.replace('"', '')
                                rel_prod_desc = rel_prod_desc.replace("'", "")
                                rel_result['rel_prod_desc'] = rel_prod_desc

                                color[c]['rel'].append(rel_result)

                        # write progress
                        __record_progress__(url)
                        # write data
                        __record_data__(url, cat, brand, name, price, prod_num, prod_desc, color)

                    # go back to main page
                    self.driver.get(main_prod_page_url)
                    __delay_time__()
                    self.sel = scrapy.Selector(text = self.driver.page_source)

                    # click next page
                    page_list = self.sel.xpath('//div[@class="span16 text-center"]/nav/ul/li/a/text()').extract()
                    next_page_num = curr_page_num + 1
                    if str(next_page_num) not in page_list:
                        # final page
                        print("\n\nFinal Page\n\n")
                        break
                    else:
                        # click next page
                        prev_page_item = self.sel.xpath('//*[@id="wrap"]/div/div[1]/section/div[1]/div/figure/a/@href').extract_first()
                        break_item = False
                        while True:
                            xpath = '//div[@class="span16 text-center"]/nav/ul/li/a[contains(text(), "{}")]'.format(str(next_page_num))
                            try:
                                element_visible = True
                                actions = chains(self.driver)
                                visible_cnt = 0
                                while True:
                                    try:
                                        clickable = self.driver.find_element_by_xpath(xpath)
                                        break
                                    except NoSuchElementException:
                                        try:
                                            WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.XPATH, xpath)))
                                            continue
                                        except TimeoutException:
                                            print("\n\nElement Not Visible.\n\n")
                                            if visible_cnt < 3:
                                                visible_cnt += 1
                                                continue
                                            else:
                                                element_visible = False
                                                break
                                if not element_visible:
                                    break_item = True
                                    print("\n\nMove on to Next Item...\n\n")
                                    break
                                actions.move_to_element(clickable).perform()
                                to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            except TimeoutException:
                                print("\n\nERROR WHILE CILCKING next page")
                                continue
                            while True:
                                try:
                                    self.driver.execute_script('arguments[0].click()', to_be_clicked)
                                    break
                                except StaleElementReferenceException:
                                    to_be_clicked = WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                                    continue
                            __delay_time__()
                            self.sel = scrapy.Selector(text = self.driver.page_source)
                            curr_item = self.sel.xpath('//*[@id="wrap"]/div/div[1]/section/div[1]/div/figure/a/@href').extract_first()
                            print('\n\n{}\n\n'.format(curr_item))
                            if prev_page_item != curr_item:
                                print("\n\nNEXT PAGE CLICKED: page now {}\n\n".format(str(next_page_num)))
                                curr_page_num += 1
                                break
                        if break_item:
                            break

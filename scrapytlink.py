#Selenium items
from selenium import webdriver #webdriver to control activities
from selenium.webdriver.common.by import By #types of navigation
from selenium.webdriver.support.ui import WebDriverWait #waiting
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

#webscraping essentials
from dotenv import load_dotenv #load my secret text
from bs4 import BeautifulSoup #navigate html
import urllib
import requests # native python HTTP interaction
import pandas as pd #manipulate extracted content
import re #regular expressions, manipulate text
import shutil #to save content

#other nice to have basics
import os #connect with operating system
import time #get time
import numpy as np
import scipy.interpolate as si

#load hidden credentials and values
load_dotenv() 

#set current working directory to where this file is saved
thisdir = os.path.dirname(os.path.abspath(__file__)) + "\\" 
os.chdir(thisdir)

def start_driver(chrome_dr, firstpagetoclick, firstclick, runheadless = False):
    """Initialize a Chrome webdriver with which for Selenium to act. """
    #set Chromedriver options to work smoothly
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized") # open Browser in maximized mode
    options.add_argument("disable-infobars") # disabling infobars
    options.add_argument("--disable-extensions") # disabling extensions
    options.add_argument("--disable-gpu") # applicable to windows os only
    options.add_argument("--disable-dev-shm-usage") # overcome limited resource problems
    options.add_argument("--no-sandbox") # Bypass OS security model  
    if runheadless:
        options.add_argument("--headless")  
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    driver = webdriver.Chrome(options=options,executable_path=chrome_dr)
    driver.implicitly_wait(10) # seconds
    
    driver.get(firstpagetoclick) #open the given URL
    #driver.manage().timeouts().implicitlyWait(10, TimeUnit.SECONDS);
    #time.sleep(10) #wait for everything to load
    return driver


def overview_collect(driver):
    # First, go to your start point or Element:
    action =  ActionChains(driver)
    startElement = driver.find_element_by_id('__next')
    action.move_to_element(startElement)
    action.perform()

    # try:
    clicks = [
        r"""//*[@id="__next"]/div[1]/div[1]/div[4]/div/div/div/section/div/div[1]/div[1]/div/div/label[5]""", 
        r"""//div[starts-with(@class, 'Checkbox__IconContainer')]""",
        r"""//div[starts-with(@class, 'BrowsePreferencesModal__Container')]/button""",
        r"""//div[starts-with(@class, 'Pagination__Buttons')]"""
        ]

    #click first opening button to access the page 
    driver.find_element(By.XPATH, clicks[0]).click()
    chks = driver.find_elements_by_xpath(clicks[1])
    for c in chks[1:]: #first one is checked by default
        c.click()
    #finally gain access
    driver.find_element(By.XPATH, clicks[2]).click()

    user_data = []

    ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,)

    istrue = True 
    counter = 0
    while istrue:

        #act on the page
        content = driver.page_source
        soup = BeautifulSoup(content, "html.parser")
        user_contents = soup.find_all("div", class_="info")
        for uc in user_contents:
            itemset = [uc.parent['href']]
            itemset += list(uc.stripped_strings)
            user_data.append(itemset)
        print(user_data[-1])

        nextclick = clicks[3]
        if counter > 0:
            nextclick += r"/a[2]"

        time.sleep(3) #wait for everything to load
        WebDriverWait(driver, 2,ignored_exceptions=ignored_exceptions)\
                                .until(expected_conditions.presence_of_element_located((By.XPATH, nextclick)))\
                                .click()

        #driver.find_element(By.XPATH, nextclick).click()
        #your_element.click()

        counter += 1

    return user_data

def userpage_collect(driver, usr_url):
    driver.get(usr_url) #open the given URL

    #xpaths
    get_xpaths = {
        'unm': """//*[@id="__next"]/div[1]/div[1]/div[1]/div/div/a/h1""",
        'profile_deets':"""//*[@id="__next"]/div[1]/div[1]/div[2]/div[1]/ul""",
        'self_descr': """//*[@id="__next"]/div[1]/div[1]/div[2]/div[2]""",
        'rates': """//*[@id="__next"]/div[1]/div[1]/div[4]/div""",
        'avail': """//*[@id="__next"]/div[1]/div[1]/div[5]/div""",
        'cont': """//*[@id="__next"]/div[1]/div[1]/div[6]/div"""
    }
    pic_list = """//*[@id="photos"]"""


if __name__ == "__main__":
    ############################
    #Section 1: Starting Conditions

    start_time = time.perf_counter()
    #savepicshere = thisdir + r"images\\"
    savefileshere = thisdir + r"data\\"
    location_data = savefileshere + "locations.csv"
    save_user_page_urls_here = savefileshere + "tl_user_page_urls.csv"
    save_user_page_content_here = savefileshere + "tl_user_ad_content.csv"

    #get secret source content
    baseURL = os.getenv("t_url") #base page URL
    testpage = os.getenv("t_testpage") #user test page URL
    chrome_dr = os.getenv("chrome_dr") #chrome driver filepath
    firstclick = os.getenv("t_firstclick")
    
    #start driver
    print("starting chrome driver")
    chrome_driver = start_driver(chrome_dr, \
        baseURL, firstclick, runheadless = False)

    udat = overview_collect(chrome_driver)
    df = pd.DataFrame(udat)
    #df.to_csv("first_try.csv")

    # udata = []
    # for u in ulist:
    #     thisu = userpage_collect(chrome_driver, u)
    #     udata.append(thisu)
    
    # df2 = pd.DataFrame(udata)
    # df2.to_csv("second_try.csv")

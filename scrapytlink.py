#Selenium items
from selenium import webdriver #webdriver to control activities
from selenium.webdriver.common.by import By #types of navigation
from selenium.webdriver.support.ui import WebDriverWait #waiting
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.proxy import Proxy, ProxyType
#from selenium.webdriver.firefox.options import Options

#webscraping essentials
from dotenv import load_dotenv #load my secret text
from bs4 import BeautifulSoup #navigate html
import urllib
from datetime import datetime
import requests # native python HTTP interaction
import pandas as pd #manipulate extracted content
import re #regular expressions, manipulate text
import shutil #to save content

#other nice to have basics
import os #connect with operating system
import time #get time
import numpy as np
import scipy.interpolate as si
from itertools import cycle
from itertools import product as iterprod
from collections import defaultdict, OrderedDict
import random
from pprint import pprint

#load hidden credentials and values
load_dotenv() 

#set current working directory to where this file is saved
thisdir = os.path.dirname(os.path.abspath(__file__)) + "\\" 
os.chdir(thisdir)

def stabilize_access(driver):
    action =  ActionChains(driver)
    startElement = driver.find_element_by_id('__next')
    action.move_to_element(startElement)
    action.perform()

    # try:
    clicks = [
        r"""//*[@id="__next"]/div[1]/div[1]/div[4]/div/div/div/section/div/div[1]/div[1]/div/div/label[5]""", 
        r"""//div[starts-with(@class, 'Checkbox__IconContainer')]""",
        r"""//div[starts-with(@class, 'BrowsePreferencesModal__Container')]/button"""
        ]

    #click first opening button to access the page 
    try:
        driver.find_element(By.XPATH, clicks[0]).click()
        chks = driver.find_elements_by_xpath(clicks[1])
        for c in chks[1:]: #first one is checked by default
            c.click()
        #finally gain access
        driver.find_element(By.XPATH, clicks[2]).click()
    except:
        pass

def start_driver(exec_path, firstpagetoclick, \
        runheadless = False, myProxy = None):
    """Initialize a Chrome webdriver with which for Selenium to act. 
        Accepts - [chrome_dr] executable path for chromedriver
            - [firstpagetoclick] URL to open as initialization
            - [runheadless] True/False option to not display action on screen
            - [proxy] ip:port to act using alternative proxy addresses"""

    if "gecko" in exec_path:
        wd_type = "firefox"
    else:
        wd_type = "chrome"

    # set webdriver options to work smoothly
    if wd_type == "firefox":
        options = webdriver.FirefoxOptions()
        #options.profile = fp
        #firefox_capabilities = DesiredCapabilities.FIREFOX
        #firefox_capabilities['marionette'] = True
    elif wd_type == "chrome":
        options = webdriver.ChromeOptions()

    options.add_argument("start-maximized") # open Browser in maximized mode
    options.add_argument("disable-infobars") # disabling infobars
    options.add_argument("--disable-extensions") # disabling extensions
    options.add_argument("--disable-gpu") # applicable to windows os only
    options.add_argument("--disable-dev-shm-usage") # overcome limited resource problems
    options.add_argument("--no-sandbox") # Bypass OS security model  
    if runheadless:
        #allow the option to run headless, will not show actions on screen
        options.add_argument("--headless")  
    if myProxy:
        #allow option to add proxy to access pages using alternative packaging
        #for some reason, kind of complicated with Chromedriver,
        #must copy attributes from pre-driver hierarchy and add back in
        if wd_type == "chrome":
            desired_capabilities = webdriver.DesiredCapabilities.CHROME.copy()
            desired_capabilities['proxy'] = {
                "httpProxy": myProxy,
                "ftpProxy": myProxy,
                "sslProxy": myProxy,
                "noProxy": None,
                "proxyType": "MANUAL",
                "class": "org.openqa.selenium.Proxy",
                "autodetect": True
            }
            webdriver.DesiredCapabilities.CHROME = desired_capabilities
    
    #options.add_argument("--remote-debugging-port=9222")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")

    if wd_type == "chrome":
        #create instance of chrome webdriver, apply all arguments above
        driver = webdriver.Chrome(options=options,executable_path=exec_path)
    elif wd_type == "firefox" and not myProxy:
        driver = webdriver.Firefox(options=options,executable_path=exec_path)
    elif wd_type == "firefox" and myProxy:
        firefox_capabilities = webdriver.DesiredCapabilities.FIREFOX
        firefox_capabilities['marionette'] = True
        firefox_capabilities['proxy'] = {
            "proxyType": "MANUAL",
            "httpProxy": myProxy,
            "ftpProxy": myProxy,
            "sslProxy": myProxy
        }
        # proxytime = Proxy({
        #     'proxyType': ProxyType.MANUAL,
        #     'httpProxy': myProxy,
        #     'ftpProxy': myProxy,
        #     'sslProxy': myProxy,
        #     'noProxy': '' # set this value as desired
        #     })

        driver = webdriver.Firefox(options=options,
            capabilities=firefox_capabilities,
            executable_path=exec_path) #,
            #firefox_binary=exec_path,
            #proxy=proxytime)

    #the site may not have https, that should be ok
    driver.desired_capabilities['acceptInsecureCerts'] = True
    driver.implicitly_wait(15) # seconds to allow page to open

    #open the given first URL
    driver.get(firstpagetoclick) 

    stabilize_access(driver)

    return driver

def overview_collect(exec_driver, t_us_base, search_src):
    """Using [driver], given [i_col_start] starting URL,
    and [i_col_url] beginning data access page, 
    gather card data from successive pages leading to sub-pages.
    In order to subdivide page sets, loop through eye colors.
    Returns pandas dataframe of all card data."""
    print("accessing base page, saving use card info")

    #start driver
    print("starting web driver")

    driver = start_driver(exec_driver, \
                baseURL + generalURL, \
                runheadless = False)

    user_data = []

    #establish acceptable exceptions, don't stop
    ignored_exceptions=(NoSuchElementException,\
        StaleElementReferenceException,\
        TimeoutException)
        
    counter = 0

    #for each eye color in given list
    for grp, thisurl in zip(search_src.keys(), search_src.values()):
        print(grp, thisurl[78:])
        try:
            time.sleep(5)

            #access page
            driver.get(thisurl)
            #get html and make soup
            content = driver.page_source
            soup = BeautifulSoup(content, "html.parser")
            #find each card's "info" tag container
            user_contents = soup.find_all("div", class_="info")
            istrue = bool(user_contents)

            while istrue:
                
                #wait for everything to load
                # wait time = random integer between 1 and 10
                time.sleep(random.randint(3,10)) 
                
                #get html and make soup
                content = driver.page_source
                soup = BeautifulSoup(content, "html.parser")
                #find each card's "info" tag container
                user_contents = soup.find_all("div", class_="info")
                
                #for each card
                for uc in user_contents:
                    #start accumulating dict
                    #labels = dict(zip(tag_names, x))
                    itemset = {"grp": grp,
                        "baseurl": thisurl,
                        "url": uc.parent['href'],
                        "page_counter": counter
                        }
                    #itemset.update(labels)

                    name_lookup = {
                        "h3": "name",
                        "small": "subtitle",
                        "aside": "description"
                    }
                    #for each enumerated tag above, find and collect
                    for child_tag in uc.children:
                        if child_tag.name in name_lookup.keys():
                            itemset[name_lookup[child_tag.name]] = \
                                child_tag.text.strip()
                        elif hasattr(child_tag, "class") and \
                            child_tag['class'] == ["badges"]:
                            for i, subchild in enumerate(child_tag):
                                if i==0:
                                    itemset['label'] = subchild.text 
                                elif "photos" in subchild.text:
                                    itemset["photo_count"] = \
                                        subchild.text.replace(" photos", "")
                                elif "/hr" in subchild.text:
                                    itemset["rate_per_hour"] = \
                                        subchild.text.replace("/hr", "")
                        elif "Active" in child_tag.text or \
                            "Available" in child_tag.text:
                            itemset['availability'] = \
                                child_tag.text.replace("Active ", "").\
                                    replace("Available now!", "currently")
                        else:
                            texts = list(child_tag.stripped_strings)
                            if len(texts) == 1:
                                itemset["location"] = texts[0]
                            else:
                                itemset["loc_temp_period"] = texts[0]
                                itemset["loc_temp"] = texts[-1]
                    user_data.append(itemset)
                #keep track of how many have been accessed and in what order
                counter += 1

                #find pagination button
                nextclick = r"""//div[starts-with(@class, 'Pagination__Buttons')]"""

                #find the page count
                pgx = soup.find(text=re.compile( \
                    r'Found \d+ profiles, page \d+ of \d+'))
                #extract the numbers
                xofx = [int(x) for x in \
                    list(re.findall(r"page (\d+) of (\d+)", pgx)[0])]
                print(xofx)
                
                if xofx[0] > 1:
                    nextclick += r"/a[2]"
                if xofx[0] == xofx[1]:
                    istrue = False
                
                # if not last instance of pageset
                # get next page
                if istrue:
                    nextbutton = driver.find_element(By.XPATH, nextclick)
                    nextbutton.click()
                #istrue = False
        except:
            pass
    #convert list of dictionaries to dataframe
    ud_df = pd.DataFrame(user_data)
    #return dataframe
    return ud_df

def get_li_dict(soup, h2_id, preface="", enum=False):
    """Based on standardized html table formatting, 
    accept a bs4 [soup] object, 
    and relevant [h2_id] value for <h2 id="x">,
    return a dictionary of content within. 
    If there are multiple instances, optional [preface] tag
    to go before enumerated list instances. 
    In specific instances needing arbitrary enumeration,
    set [enum] = True. 
     """
    tmpdict = {}
    #find the given header id tag
    head = soup.find("h2", id=h2_id)
    #gather all list items
    lis = head.parent.find_all("li")
    #i = 0
    #for each list item
    for i,li in enumerate(lis):
        #find all the children, extract label contents with next()
        lic = li.children
        lbl = next(lic).text
        nlbl = next(lic).text
        #if needing to enumerate, attach index to preface
        if enum:
            if not preface:
                preface = h2_id + "_"
            key = preface + str(i)
            value = lbl + "|" + nlbl
        else:
            #otherwise, don't add enumeration index
            key = preface + lbl
            value = nlbl
        #create dictionary entry
        tmpdict[key] = value
        #i += 1
    #return the dictionary, not a list or df
    return tmpdict

def press_show_buttons(driver):
    """Using current state of [driver], click on "show"
    button for specific contact details. 
    Return a dictionary of contact information."""
    checkus = ["Email", "Mobile", "WhatsApp", "Email"]

    time.sleep(2)
    for cu in checkus:
        #//*[@id="__next"]/div[1]/div[1]/div[6]/div/div[2]/ul/li[1]
        pm = f"//*[@data-row-title=\"{cu}\"]/div[2]/button"
        try:
            el = driver.find_element(By.XPATH, pm)
            time.sleep(0.5)
            el.click()
        except:
            pass

    time.sleep(1)

    content = driver.page_source
    soup = BeautifulSoup(content, "html.parser")
    cont_dict = get_li_dict(soup, "contact")

    for cu in checkus:
        if cu in cont_dict:
            if '●' in cont_dict[cu]:
                print(f"not getting {cu}")
                #return False 
    return cont_dict

def get_proxies():
    """Using freely available content from 
    free-proxy-list.net, return a set of secure
    proxies to use while accessing pages."""
    #from https://www.scrapehero.com/how-to-rotate-proxies-and-ip-addresses-using-python-3/
    url = 'https://free-proxy-list.net/'
    #get the html page and make soup from it
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # find the first instance of a tbody tag, 
    # then all table rows within with "tr" tags
    tags = soup.find('tbody').find_all('tr')
    #create a list of lists
    ss = [list(x.stripped_strings) for x in tags]
    #delimit IP and port with : in a list unless not secure
    proxies = [":".join(x[:2]) for x in ss if x[6]=="no"]
    return set(proxies)

def userpage_collect(driver, usr_url):
    """ Using [driver] and single page [usr_url],
    collect and return all desired datapoints 
    as a dictionary. """
    driver.get(usr_url) #open the given URL

    #wait for everything to load
    # wait time = random integer between 1 and 10
    time.sleep(random.randint(1,3)) 

    #act on the page
    content = driver.page_source
    soup = BeautifulSoup(content, "html.parser")

    #begin the accumulating page info dictionary with url
    itemset = {"url": usr_url, "collected":datetime.now()}

    #collect items in the profile section
    itemset.update(get_li_dict(soup, "profile"))

    #grab full text from "About" section
    itemset["about"] = soup.find("h2",id="about").next_sibling.text
    
    #may not exist, but if it does, collect "tours" section
    try:
        itemset.update(get_li_dict(soup, "tours", \
            preface="tour_", enum=True))
    except:
        pass

    #collect "availability" section
    #if there are multiple instances, 
    #   preface new dict entries with "av_", function will add # on end
    itemset.update(get_li_dict(soup, "availability", preface="av_"))

    #get rate data
    in_out = soup.find("h2", id="rates")

    #if there are separate groupings for rates
    #handle them
    if in_out: 
        
        #find all the rate groupings
        in_out = in_out.parent.children
        
        #for each grouping
        for child in in_out:
            #ensure it's actually data
            if child.name != "h2":
                ctype = child.h2.text
                i = 0
                for li in child.find_all("li"):
                    #add itemized values to dictionary
                    itemset[f"rate_{ctype}_{i}"] = li.contents[0].text + \
                        "|" + li.contents[1].text
                    i += 1

    #press "show" to display contact information
    #this function also tests to see if this action worked
    cont_dict = press_show_buttons(driver)
    if not cont_dict:
        #if not successful, try to press the buttons again
        cont_dict = press_show_buttons(driver)
        
    itemset.update(cont_dict)
        
    return itemset

def collect_user_pages(baseURL, ulist, driver_dir):
    """Cycle through given list of url page extensions [ulist],
        using the webdriver at directory [driver_dir] 
        and base URL of target site [baseURL], 
        scrape each individual page and return a list of dictionaries.
        If fails to grab contact info for 3 pages, exits and returns
        current state of user dict list."""

    #start driver
    print("starting web driver")
    chr_ascii = [101,115,99,111,114,116,115]
    web_driver = start_driver(driver_dir,
                baseURL + "/" + "".join([chr(x) for x in chr_ascii]),
                runheadless = False)

    print("collecting user page data")
    udata = []
    threestrikes = ""
    for u in ulist:
        print(u)
        try:
            thisu = userpage_collect(web_driver, baseURL + u)
            udata.append(thisu)
            print("\t\t success")
        except:
            print("\t\t failure")
            if threestrikes != "XXX":
                threestrikes += "X"
                pass
            else:
                web_driver.close()
                print("\nfailure 3x, exiting process and returning state")
                return udata

    web_driver.close()

    return udata
    
def generate_searchlist(search_df, t_us_base):
    search_cond = defaultdict(str)
    search_df = search_df.query("no_go != 1").fillna('none')
    sdf_cols = search_df.columns
    sdf_cols = [x for x in sdf_cols if "_count" not in x and x != "no_go"]
    search_df = search_df[sdf_cols]
    search_df.group = search_df.group.astype(int)
    search_list = search_df.values.tolist()
    sdf_cols = sdf_cols[2:]
    for row in search_list:
        grp = str(row.pop(0))
        gnd = row.pop(0)
        #print(grp, gnd)
        tmpurl = t_us_base.replace("####", gnd)
        if tmpurl not in search_cond[grp]:
            search_cond[grp] = tmpurl
        for i, val in enumerate(row):
            addme = f"&{sdf_cols[i]}%5B%5D={val}"
            if val != "none" and addme not in search_cond[grp]:
                search_cond[grp] += addme
        #print(search_cond[grp])
    return search_cond

def collect_user_sample(chromedriver_path, baseurl, 
        user_url_ext_list, saveas=None):
    """Must input filepath of chromedriver exe file [chromedriver_path].
        Accept a [baseurl] of the chosen website, 
        and a list of url extensions for a given list of users 
        [user_url_ext_list], and a file directory to save
        the output [saveas]. Returns a pandas dataframe of 
        user records and exports the dataframe to a csv file 
        in the given directory."""
        
    start_time1 = datetime.now()
    #timetext = start_time1.strftime("%Y%m%d%H%M")
    
    udata = collect_user_pages(baseurl, \
                user_url_ext_list, \
                chromedriver_path)
    if saveas:
        mydf = pd.DataFrame(udata)
        mydf.to_csv(saveas, encoding="latin-1")

    
    print("--- %s seconds ---" % (datetime.now() - start_time1))
    return udata

if __name__ == "__main__":
    ############################
    #Section 1: Starting Conditions
    
    start_time1 = datetime.now()
    start_time = time.perf_counter()
    #savepicshere = thisdir + r"images\\"
    savefileshere = thisdir + r"data\\"
    location_data = savefileshere + "locations.csv"
    save_user_page_urls_here = savefileshere + "tl_user_page_urls.csv"
    save_user_page_content_here = savefileshere + "tl_user_ad_content.csv"

    #get secret source content
    baseURL = os.getenv("t_baseurl") #base page URL
    generalURL = os.getenv("t_url") #base first URL ext
    exec_driver = os.getenv("chrome_dr") #webdriver filepath #moz_dr
    #first_click = os.getenv("t_firstclick")
    # t_eye_col_full = os.getenv("t_eye_col_base")
    # t_eye_col_url = os.getenv("t_eye_col_url")
    t_us_base = os.getenv("t_us_base")
    search_src = os.getenv("search_src")
    search_df = pd.read_csv(search_src)
    search_cond = generate_searchlist(search_df, t_us_base)
    url_list = list(search_cond.values())

    with open("test_urlbuild.txt", "a") as f:
        f.write('\n'.join(url_list))
    
    print("collecting page contact cards")
    udat = overview_collect(exec_driver, t_us_base, search_cond)
    card_filenm = f"data_contact_cards_{start_time}.csv"
    udat.to_csv(card_filenm)

    udat = pd.read_csv(card_filenm)
    ulist = udat.url.tolist()
    udata = collect_user_pages(baseURL, \
                ulist, \
                exec_driver)

    full_df = pd.DataFrame(udata)
    full_df.to_csv(f"data_user_details_{start_time}.csv")
    print("--- %s seconds ---" % (datetime.now() - start_time1))

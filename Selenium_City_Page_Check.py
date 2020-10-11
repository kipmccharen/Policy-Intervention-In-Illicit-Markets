#Selenium items
from selenium import webdriver #webdriver to control activities
from selenium.webdriver.common.by import By #types of navigation
from selenium.webdriver.support.ui import WebDriverWait #waiting

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
    time.sleep(1) #wait for everything to load

    try:
        #click first opening button to access the page 
        driver.find_element(By.XPATH, firstclick).click()
    except:
        pass

    return driver

def extract_html_per_card_page(driver, urlstart, right_xpath):
    """Use Selenium to click buttons and act like a human 
    to scrape dynamically changing listings. """

    driver.get(urlstart) #open the given URL
    time.sleep(3) #wait for everything to load

    # if there's no right button
    try:
        rightelem = driver.find_element(By.XPATH, right_xpath) #*[@id="search-scroll-to"]
    except:
        time.sleep(2) #wait for everything to load
        #save html of current page
        content = driver.page_source
        return [content]

    #initialize boolean to loop until true
    classend_found = False
    source_yield = [] #save source files
    i = 1

    while not classend_found:

        time.sleep(2) #wait for everything to load

        #save html of current page
        content = driver.page_source
        source_yield.append(content)
        print(f"saved pg {i}")
        i += 1
        #check if we can click the next page button
        #if we can't, then end the loop
        try:
            rightelem.click()
        except:
            classend_found = True
    
    return source_yield

def soup_extract_cards(shtml, maxi):
    """Extract individual ad tiles from a given html page. """
    soup = BeautifulSoup(shtml, "lxml")
    cards = soup.find('div', id="searchresults").find_all("a")
    
    dict_list = []
    maxi = maxi
    for card in cards:
        maxi += 1
        card_dict = {"i": maxi, "urlpath": card["href"]}
        card_dict["img_url"] = card.find("img")["src"]
        card_dict["username"] = card.find("div", class_="media-content body-2").text
        cd_raw = card.find("div", class_="state-city mb-2").stripped_strings
        card_dict["state"], card_dict["city"] = cd_raw[0].strip(), cd_raw[1].strip()
        card_dict["review_count"] = card.find("div", class_="body-2 mt-4").span.text
        dict_list.append(card_dict)
        
    return dict_list, maxi

def any_list_item_in_string(testme, no_list):
    """Return true if any item in the given no_list is in testme.
    Helpful to quickly eliminate known filler text."""
    for x in no_list:
        if x.lower() in testme.lower():
            return True
    return False

def download_img(URL, filepath):
    """Download image from given URL, save as given filepath."""
    # sourced from https://towardsdatascience.com/how-to-download-an-image-using-python-38a75cfa21c
    # Open the url image, set stream to True, this will return the stream content.
    r = requests.get(URL, stream = True)

    # Check if the image was retrieved successfully
    if r.status_code == 200:
        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True
        
        # Open a local file with wb ( write binary ) permission.
        with open(filepath,'wb') as f:
            shutil.copyfileobj(r.raw, f)
        #print('Image sucessfully Downloaded: ',filename)
    else:
        print(f'Image Couldn\'t be retreived: {URL}')

def starlist_to_int(starlist):
    valdict = {"star": 1, "star_half": 0.5, "star_border": 0}
    sumint = 0
    for s in starlist:
        if s.strip().lower() in valdict.keys():
            sumint += valdict[s]
    return sumint

def scrape_user_ad_page(driver, url, savepicshere):
    
    driver.get(url) #open the given URL
    time.sleep(1) #wait for everything to load

    # Initialize dictionary to store user's data while scraping
    user_dict = {"url": url}

    ############################
    #Section 1: Extract pictures

    # Extract HTML from current selenium driver state, make soup
    content = driver.page_source
    soup = BeautifulSoup(content, "lxml")
    user_dict["location"] = soup.find("a", class_="router-link-active").text.strip()
    
    # First find user's username to identify saved pics
    # Find next page section to limit html search area
    part2 = soup.find("div", class_="layout row wrap justify-center")
    user_dict["username"] = part2.find("a", class_="title font-weight-bold").text.strip()
    # making an assumption that every username is unique and has 1 user

    # Extract pictures using Selenium and Beautifulsoup teamwork
    test_true = True #if new identifier found, end pic extract loop
    pic_names = [] #place to store pictures
    img_list = [] #store pic URLs
    i = 0 #count images

    # Open xpath to button that rotates images
    right_pics_button = os.getenv("right_pics_button")
    # Assign object to easily click for next image
    rightelem = driver.find_element(By.XPATH, right_pics_button)

    # Loop until return to image already scraped
    while test_true:
        # Save current HTML, changes as pics rotated
        content = driver.page_source
        soup = BeautifulSoup(content, "lxml")
        #find picture source tag and extract if not already in list
        pic_src = soup.find("div", class_="v-tabs__items")
        img = pic_src.find("img")["src"]
        if img not in img_list:
            img_list.append(img)
            zeropad = str(i).zfill(2)
            saveas = user_dict["username"] + f".{zeropad}.jpg"
            download_img(img, savepicshere + saveas)
            pic_names.append(saveas)
            i += 1
        else:
            test_true = False

        rightelem.click()
    
    user_dict["img_urls"] = img_list #save raw URLs
    user_dict["img_saved"] = pic_names #saved file names

    ############################
    #Section 2: user basic information, center page content

    #Extract ad title
    user_dict["title"] = soup.find("h2", \
        class_="my-5 display-1 font-weight-bold text-xs-center").text.strip()
    
    subheads = part2.find_all("div", class_="subheading") #.getText('|')
    for sh in subheads:
        split = sh.text.split(": ")
        user_dict[split[0].strip()] = split[1].strip()
    starsum = 0
    stars = part2.find_all("i",class_="v-icon v-icon--link material-icons theme--light orange--text")
    user_dict["stars"] = starlist_to_int([x.text.strip() for x in stars])

    # Get self descriptors
    descrip = part2.find("div", class_="flex xs12 sm6 px-2 mb-4").getText(';')
    descrip = iter(list(re.split("[,;\n]",descrip)))
    item = next(descrip)
    user_dict["self_descriptors"] = [item.strip()]
    while item not in ["USA", "Canada"]:
        #strip spaces and comma at end, get next item
        if item:
            user_dict["self_descriptors"].append(item)  
        item = next(descrip).strip().rstrip(",") 

    # Donation extraction
    donations = part2.find(text=re.compile(".*Donations.*")).parent.parent.text
    donations = donations.replace("Donations","") #remove donations text
    try:
        donations = donations.split("Payment types accepted: ") #split to get payment types
        user_dict["payment_types_accepted"] = donations[1].strip() #return payment types
        donations = donations[0].strip().split('\n') #everything not payment types
        user_dict["donation_options"] = []

        # Separate line items in donations
        sect = "" #initiate payment section header text 
        for x in donations:
            x = x.strip()
            if x: #if there's a value
                if bool(re.search(r'\d', x)): #if there's a number
                    x = re.split(r'[ \-\;\,\:]{2,}',x)
                    user_dict["donation_options"].append([sect] + list(x))
                else:
                    sect = x
    except:
        user_dict["donation_options"] = ';'.join(donations).strip()

    ############################
    #Section 3: Extract contact information

    # Extract Contact Information and append individually
    contactinfo = part2.find("div", class_="layout row wrap mt-4 justify-center align-center")
    # get next level div which contains contents
    contactinfo = contactinfo.contents[0].find_all("div")
    # define list of text contents that we DON'T want, skip if found
    excludelist = ["Submit a review", "Get Screened", "This is important!"]
    for x in contactinfo:
        xtxt = x.text.strip()
        if xtxt and not any_list_item_in_string(xtxt,excludelist):
            xtxt = list(x.stripped_strings)
            user_dict[xtxt[0]] = xtxt[1] #add each one as a new dict item


    ############################
    #Section 4: About tab at bottom of page

    # Extract ABOUT section
    user_dict["about"] = list(soup.find("div", class_="px-2 ql-editor view-editor").stripped_strings)

    # Extract My "No" List
    nolist = list(soup.find("div", class_="nolist").stripped_strings)
    user_dict["nolist"] = [x.strip() for x in nolist[1:] if x.strip() not in ["", ","]]

    # Extract user's attributes and append individually
    attributes = soup.find("div", class_="layout row wrap")
    attributes = attributes.findAll("div", class_="layout row")
    for attr in attributes:
        txt = attr.get_text("").split(":")
        user_dict[txt[0].strip()] = txt[1].strip()


    ############################
    #Section 5: Reviews tab at bottom

    # Extract reviews, unclear of purpose but get them
    review_strings = soup.find("div", id="view-reviews").stripped_strings
    user_dict["reviews"] = []
    starlist = []
    next_review = {}
    review_iter = iter(review_strings)
    anylist = ["Joined", "Reviewed", "Visit Date"]
    skipus = ["priority_high", "queue", "overview", "..."]
    for x in review_iter:
        x = x.strip()
        xl = x.lower()
        if not x or any_list_item_in_string(x, skipus):
            pass
        elif "read full review" in xl:
            user_dict["reviews"].append(next_review)
            next_review = {}
        elif "review by" in xl:
            x = next(review_iter)
            next_review["by"] = x.strip()
        elif "reviews" in xl:
            next_review["reviewer_reviews"] = x.strip(" ")[0]
        elif any_list_item_in_string(x,anylist):
            x = x.split(": ")
            next_review[x[0]] = x[1]
        elif "star" in xl:
            starlist.append(x)
            next_review["stars"] = starlist_to_int(starlist)
        elif "replied" in xl:
            x = next(review_iter)
            next_review["provider_replied"] = x.strip()
        else:
            next_review["review"] = x
    return user_dict

if __name__ == "__main__":
    ############################
    #Section 1: Starting Conditions

    start_time = time.perf_counter()
    savepicshere = thisdir + r"images\\"
    savefileshere = thisdir + r"data\\"
    location_data = savefileshere + "locations.csv"
    save_user_page_urls_here = savefileshere + "user_page_urls.csv"
    save_user_page_content_here = savefileshere + "user_ad_content.csv"

    #get secret source content
    baseURL = os.getenv("baseURL") #base page URL
    testpage1 = os.getenv("testpage1") #location test page URL
    testpage2 = os.getenv("testpage2") #user test page URL
    chrome_dr = os.getenv("chrome_dr") #chrome driver filepath
    firstclick = os.getenv("firstclick") #xpath of first click on site
    right_xpath = os.getenv("right_xpath") #xpath of image right button
    
    #start driver
    print("starting chrome driver")
    chrome_driver = start_driver(chrome_dr, \
        testpage1, firstclick, runheadless = True)

    # ############################
    # #Section 2: Accumulate Page URLs by location page

    # #get location-based page extensions
    # loc_df = pd.read_csv(location_data)
    # locationlist = loc_df["href"].values.tolist()
    # #locationlist = [testpage1] #test with 1 location
    # #locationlist = locationlist[:3]

    # # vessel variables to accumulate content
    # html_list = [] #html content for each scrolled page of ad cards
    # card_data = [] #card data extracted from html pages

    # max_item_num = 0
    # for itt, loc in enumerate(locationlist):
    #     print(loc)
    #     url = baseURL + loc #put base URL before page extension for full URL
    #     src_htmls = extract_html_per_card_page(chrome_driver, url, right_xpath)
    #     for html in src_htmls:
    #         sub_dict_list, new_max = soup_extract_cards(html, max_item_num)
    #         max_item_num = new_max
    #         card_data += sub_dict_list
    #         print(len(card_data), "total user page items")
        
    #     df = pd.DataFrame(card_data)
    #     df.to_csv(save_user_page_urls_here.replace(".csv", str(itt) + ".csv"), index=False) #

    #     # html_list += src_htmls
    #     # print(len(src_htmls), " new html docs")
    #     # print(len(html_list), " total html docs")

    # # #for each page of ad listings, extract the info for each listing
    # # print("extracting ad listings from html")
    # # for html in src_htmls:
    # #     sub_dict_list, new_max = soup_extract_cards(html, max_item_num)
    # #     max_item_num = new_max
    # #     card_data += sub_dict_list
    # #     print(len(card_data), "user page items")

    # # df = pd.DataFrame(card_data)
    # # print(len(df.index), " user page URLs")
    # # print(df.head())
    # # df.to_csv(save_user_page_urls_here, index=False)
    



    ############################
    #Section 3: Accumulate content for each user page

    #get location-based page extensions
    loc_df = pd.read_csv(save_user_page_urls_here)
    user_page_list = loc_df["urlpath"].values.tolist() #all pages
    #user_page_list = user_page_list[:5]
    #user_page_list = [testpage2] # testing w 1 page

    # vessel variable to accumulate content
    outputlist = []

    # For each user's page, scrape content
    for i, upl in enumerate(user_page_list):
        sub_start_time = time.perf_counter()
        try:
            # scrape an individual page
            userdict = scrape_user_ad_page(chrome_driver, \
                baseURL + upl, \
                savepicshere)

            outputlist.append(userdict)
            subtimediff = str(round(time.perf_counter() - sub_start_time, 1)).zfill(3)
            print(f"user page {i} --- {subtimediff}s sec. elapsed ---")
        except:
            print("error, did not save")

    # convert list of dictionaries to a spreadsheet and export
    df = pd.DataFrame(outputlist)
    df.to_csv(save_user_page_content_here, index=False, encoding="utf-8")

    print("--- %s sec. elapsed ---" % (time.perf_counter() - start_time))

    chrome_driver.quit()
    quit()
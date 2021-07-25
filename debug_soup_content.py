import json
import time
from bs4 import BeautifulSoup as bs
import datetime
import re
from datetime import datetime as dt
from selenium import webdriver


options=webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('allow-running-insecure-content')
options.add_argument('ignore-certificate-errors')
options.add_argument('allow-insecure-localhost')
options.add_argument('unsafely-treat-insecure-origin-as-secure')

# Opening browser session with preset options and chromedriver  in the same folder as this script "./chromedriver
browser     = webdriver.Chrome('./chromedriver', chrome_options=options)     # Browser for the main search results
#browser_sub = webdriver.Chrome('./chromedriver', chrome_options=options)    # Browser for the future multithread

browser.implicitly_wait(12)
#browser_sub.implicitly_wait(10)


tmp_url = "https://www.vrbo.com/search/keywords:lewes-beach-delaware-united-states-of-america/arrival:2021-07-17/departure:2021-07-21?filterByTotalPrice=false&adultsCount=3&childrenCount=1&petIncluded=false&ssr=tru"
    #"https://www.vrbo.com/search/keywords:lewes-beach-delaware-united-states-of-america/arrival:2021-08-18/departure:2021-08-25?adultsCount=3&childrenCount=1&petIncluded=false&filterByTotalPrice=true&ssr=true"
browser.get(tmp_url) # Current_Range["SearchUrl"])
time.sleep(10)

browser.switch_to.default_content()   # Points browser to the main page instead of later generated iframe
soup = bs(browser.page_source, 'lxml')  # Load the content for processing


#HitCollection = soup.find('div', attrs={"data-wdio": "HitCollection", "role": "list"})
#HitCollection_Childrend = HitCollection.findChildren('div', attrs={"data-wdio": re.compile("^Waypoint.")}, recursive=True)

#num = 1

#for child in HitCollection.contents:
#    print(child.attrs['data-wdio'])
    #child_res = child.find_all('div', attrs={"data-wdio": "Waypoint"+str(num)})
    #child_listitem = child_res.find('div', attrs={"role": "listitem"})
#items = soup.find_all('div', attrs={"class": "HitExperiment", "role": "listitem"})

#items = soup.find_all('div', attrs={"data-wdio": re.compile("^Waypoint.")}, recursive=True)
items = soup.findAll('div', attrs={"class":"HitExperiment" , "role": "listitem"}, recursive=True, limit=None)
print("the end")
#listitems = items.find_all('div', attrs={"role": "listitem"}, recursive=True)

#for item in items:
    #z1 = item.find_all('div', attrs={"class": "HitExperiment", "role": "listitem"})
    #z = item.find('div', attrs={"role": "listitem"})
#    if z:
#        print(z[0].contents[2].contents[0].contents[0].text)
          #z[0].contents[2].contents[0].contents[1].text,z[0].contents[2].contents[0].contents[2].text)
        #, re.compile("^Waypoint.")

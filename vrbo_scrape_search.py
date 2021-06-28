import json
import time
from bs4 import BeautifulSoup as bs
import datetime
import re
from datetime import datetime as dt
from selenium import webdriver
#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC


'''
Userful searches:

1. Find properties in specific locaiton(s) for the duration of X days within specified date period
    VA Beach, 10 days June, July, August 2021

'''

'''
{
    'Period_Start' : '2021-06-01',
    'Period_End'   : '2021-08-31',
    'Durations'    : 5, 10
    'Results'      :
        { 
            'duration'  : 5,
            'dates'     : [
                            {'Start':'2021-06-01' , 'End':'2021-06-05'},
                            {'Start':'2021-06-02' , 'End':'2021-06-06'},
                            ...
                            {'Start':'2021-08-31' , 'End':'2021-08-04'}
                          ],

            'duration'  : 10,
            'dates'     : [
                            {'Start':'2021-06-01' , 'End':'2021-06-10'},
                            {'Start':'2021-06-02' , 'End':'2021-06-11'},
                            ...
                            {'Start':'2021-08-31' , 'End':'2021-09-09'}
                          ]
        }
}
'''
def Get_UrlInfo(p_item):
    # Read property detail Url
    tag = p_item.find("a", "media-flex__content")
    return tag.get("href") if tag else ""

def Get_Type(p_item):
    # Read Property Tyoe. Ex: Condo, House, etc.
    tag = p_item.find("div", "HitExperimentInfo__content")
    if tag:
        tag = tag.find(class_="HitExperimentInfo__type-place-details")
        if tag:
            tag = ' '.join(val.get_text(strip=True) for val in tag.findAll("span"))  # Merge text of multiple <SPAN>
    return tag if tag else ""

def Get_Headline(p_item):
    # Read headline. Ex: Adorable Cottage
    tag = p_item.find("div", "HitExperimentInfo__content")
    if tag:
        tag = tag.find(class_="HitExperimentInfo__headline")
    return tag.text if tag else ""

def Get_Sleeps(p_item):
    # Read Sleep and Bed info. Ex: Sleeps 4 1 bedroom 2 beds
    tag = p_item.find("div", "HitExperimentInfo__content")
    if tag:
        tag = tag.find(class_="HitExperimentInfo__room-beds-details").findAll("span")
        if tag:
            tag = ' | '.join(val.get_text(strip=True) for val in tag)                # Merge text of multiple <SPAN>
    return tag if tag else ""

def Get_Rating(p_item):
    # Read Rating. Ex: Wonderful! 4.9/5()
    tag = p_item.find("footer", "media-flex__footer")
    if tag:
        tag = tag.find(class_="HitExperimentInfo__superlative")
    return tag.text if tag else ""

def Get_Reviews(p_item):
    # Read star rating. Ex: 4.9(131)
    tag = p_item.find("footer", "media-flex__footer")
    if tag:
        tag = tag.find(class_="HitExperimentInfo__starRating")
        if tag:
            tag = tag.find(class_="Rating__label")
    return tag.text if tag else ""

def Get_PriceAmount(p_item):
    # Read price. Ex: $215
    tag = p_item.find("footer", "media-flex__footer")
    if tag:
        tag = tag.find(class_="DualPrice__amount")
    return tag.text if tag else ""

def Get_Price_Period(p_item):
    # Read price period. Ex: avg/night
    tag = p_item.find("footer", "media-flex__footer")
    if tag:
        tag = tag.find(class_="DualPrice__period")
    return tag.text if tag else ""

def Get_Cancellation(p_item):
    # >>> item.contents[2].contents[0].contents[3].text               # Free cancellation
    return ""


def get_dates(p_start, p_end, p_days, url_tmp):
    # generates dates for a single provided duration

    DATE_FORMAT = "%Y-%m-%d"

    intervals = []
    date_set = {}

    start_date = dt.strptime(p_start, DATE_FORMAT)
    end_date   = dt.strptime(p_end, DATE_FORMAT)

    # Substracting one day because first day counts as well
    delta = datetime.timedelta(days=p_days-1)

    while start_date <= end_date:
        date_set["Duration"]    = p_days
        date_set["Start"]       = start_date.date().isoformat()
        date_set["End"]         = (start_date + delta).date().isoformat()
        date_set["SearchUrl"]   = url_tmp.replace("ARRIVAL_DATE",date_set["Start"]).replace("DEPARTURE_DATE", date_set["End"])

        intervals.append(date_set.copy())

        start_date += datetime.timedelta(days=1)

    return {"results": intervals}


def get_multiple_duration_dates(p_start, p_end, p_days, url_tmp):
    # generates dates for multiple durations

    all_durations = (p_days if type(p_days) is list else [p_days])
    res_dates = []

    for dur in all_durations:
        res_dates.append(get_dates(p_start, p_end, dur, url_tmp))

    return res_dates

# Main code

# VRBO URL TEMPLATE
base_url        = "https://www.vrbo.com"
#location        = "virginia-beach-virginia-united-states-of-america"
location        = "lewes-beach-delaware-united-states-of-america"
arrival         = "ARRIVAL_DATE"    # 2021-12-31
departure       = "DEPARTURE_DATE"  # 2021-12-31
minNightlyPrice = "0"               # str int
maxNightlyPrice = "200"             # str int
adultsCount     = "3"               # str int
childrenCount   = "1"               # str int

Url_Template = base_url + "/search/keywords:" + location +\
           "/arrival:" + arrival +\
           "/departure:" + departure + \
           "?" + "filterByTotalPrice=false" + "&"\
           "adultsCount=" + adultsCount + "&" + \
           "childrenCount=" + childrenCount + "&" + \
           "petIncluded=false&ssr=true"

#            "/minNightlyPrice/" + minNightlyPrice + \
#            "/maxNightlyPrice/" + maxNightlyPrice + \

# Testing date generator
start_str = "2021-07-15"
end_str   = "2021-08-15"
durations = [3,5]

UrlCollection = {"Period_Start" : start_str,
                 "Perfio_Ends"  : end_str,
                 "Durations"    : durations,
                 "Results"      : get_multiple_duration_dates(start_str, end_str, durations, Url_Template)}


# TODO: Research how to iterate many link without looking like DDoS. User delay?
# TODO: Collect VRBO data in dict JSON format

# Setting Chomedriver options:
# 'headless' to keep broser windows from popping up
# all other to ignore any cert warnings and/or prompts
options=webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('allow-running-insecure-content')
options.add_argument('ignore-certificate-errors')
options.add_argument('allow-insecure-localhost')
options.add_argument('unsafely-treat-insecure-origin-as-secure')

# Opening browser session with preset options and chromedriver  in the same folder as this script "./chromedriver
browser     = webdriver.Chrome('./chromedriver', chrome_options=options)     # Browser for the main search results
#browser_sub = webdriver.Chrome('./chromedriver', chrome_options=options)    # Browser for the subpages

browser.implicitly_wait(10)
#browser_sub.implicitly_wait(10)


for Current_Url in UrlCollection["Results"]:

    for Current_Range in Current_Url["results"]:
        print("    Duration   :", Current_Range["Duration"])
        print("    Start      :", Current_Range["Start"])
        print("    End        :", Current_Range["End"])
        print("    Search Url :", Current_Range["SearchUrl"])

        # Load URL
        browser.get(Current_Range["SearchUrl"])
        time.sleep(10)

        browser.switch_to.default_content()   # Points browser to the main page instead of later generated iframe
        soup = bs(browser.page_source, 'html.parser')  # Load the content for processing

        items = soup.find_all('div', {"data-wdio": re.compile('Waypoint*')})

        vrbo_record, vrbo_records = {}, []

        Current_Range["SearchResults"] = []

        for item in items:

            vrbo_record["InfoUrl"]      = base_url + Get_UrlInfo(item)
            vrbo_record["Type"]         = Get_Type(item)
            vrbo_record["Headline"]     = Get_Headline(item)
            vrbo_record["Sleeps"]       = Get_Sleeps(item)
            vrbo_record["Rating"]       = Get_Rating(item)
            vrbo_record["Reviews"]      = Get_Reviews(item)
            vrbo_record["Price_Amount"] = Get_PriceAmount(item)
            vrbo_record["Price_Period"] = Get_Price_Period(item)
            #vrbo_record["Cancellation"] = Get_Cancellation(item)

            Current_Range["SearchResults"].append(vrbo_record.copy())

        print("    Found      :", len(Current_Range["SearchResults"]))
        print("")

browser.close()
browser.quit()

print("The End!")

with open('data.json', 'w') as fp:
    json.dump(UrlCollection, fp)



'''
Unused code
    #vrbo_record["Sleeps"] = item.find("div", "HitExperimentInfo__content")\
    #    .find(class_="HitExperimentInfo__room-beds-details")\
    #    .find("span",text=lambda val: val and val.startswith("Sleeps")).text
    #Returns: Sleeps 4

'''

# TODO: Filter price in the data set because VRBO Site does not support ULR based max price filtering

'''
/arrival:2021-06-27/departure:2021-07-03/minNightlyPrice/0?filterByTotalPrice=false&petIncluded=false&ssr=true&adultsCount=3&childrenCount=1
/arrival:2021-06-23/departure:2021-06-26/minNightlyPrice/60/maxNightlyPrice/770?filterByTotalPrice=false&petIncluded=false&ssr=true&adultsCount=3&childrenCount=1

/arrival:2021-06-23/departure:2021-06-29/minNightlyPrice/0/maxNightlyPrice/300
?filterByTotalPrice=false&petIncluded=false&ssr=true&adultsCount=3&childrenCount=1

/arrival:2021-06-23/departure:2021-06-29/minNightlyPrice/0/maxNightlyPrice/310?filterByTotalPrice=false
&petIncluded=false&ssr=true&adultsCount=3&childrenCount=1


#URL with dates
https://www.vrbo.com/search/keywords:virginia-beach-virginia-united-states-of-america/arrival:2021-06-27/departure:2021-07-03/minNightlyPrice/0?filterByTotalPrice=false&petIncluded=false&ssr=true&adultsCount=3&childrenCount=1
https://www.vrbo.com/search/
   keywords:
       virginia-beach-virginia-united-states-of-america/
       arrival:2021-06-27/
       departure:2021-07-03/
       minNightlyPrice/0?filterByTotalPrice=false&petIncluded=false&ssr=true&adultsCount=3&childrenCount=1


VRBO Locations:
    virginia-beach-virginia-united-states-of-america
'''

# Wait for the data to populate
'''
try:
    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "Results"))
    )
finally:
    browser.quit()
'''

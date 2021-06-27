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


def get_dates(p_start, p_end, p_days, url_tmp):
    # generates dates for a single provided duration

    DATE_FORMAT = "%Y-%m-%d"

    intervals = []
    date_set = {}

    start_date = dt.strptime(p_start, DATE_FORMAT)
    end_date = dt.strptime(p_end, DATE_FORMAT)

    # Substracting one day because first day counts too
    delta = datetime.timedelta(days=p_days-1)

    while start_date < end_date:
        date_set["Start"]       = start_date.date().isoformat()
        date_set["End"]         = (start_date + delta).date().isoformat()
        date_set["SearchUrl"]   = url_tmp.replace("ARRIVAL_DATE",date_set["Start"]).replace("DEPARTURE_DATE", date_set["End"])

        intervals.append(date_set.copy())

        start_date += datetime.timedelta(days=1)

    # returns duration and list of matching dates
    res = {"duration": p_days, "dates": intervals}

    return res


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
location        = "virginia-beach-virginia-united-states-of-america"
arrival         = "ARRIVAL_DATE"    # 2021-12-31
departure       = "DEPARTURE_DATE"  # 2021-12-31
minNightlyPrice = "0"               # str int
maxNightlyPrice = "300"             # str int
adultsCount     = "3"               # str int
childrenCount   = "1"               # str int

Url_Template = base_url + "/search/keywords:" + location +\
           "/arrival:" + arrival +\
           "/departure:" + departure + \
           "/minNightlyPrice/" + minNightlyPrice + \
           "/maxNightlyPrice/" + maxNightlyPrice + \
           "?" + "filterByTotalPrice=false" + "&"\
           "adultsCount=" + adultsCount + "&" + \
           "childrenCount=" + childrenCount + "&" + \
           "petIncluded=false&ssr=true"


# Testing date generator
start_str = "2021-07-01"
end_str   = "2021-08-31"
durations = [7,10]

UrlCollection = {"Period_Start": "2021-07-01",
                 "Perfio_Ends" : "2021-08-31",
                 "Durations": [7, 10],
                 "Results": get_multiple_duration_dates(start_str, end_str, durations, Url_Template)}


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

    print("Duration :", Current_Url["duration"])
    print("")

    for Current_Range in Current_Url["dates"]:
        print("    Start      :", Current_Range["Start"])
        print("    End        :", Current_Range["End"])
        print("    Search Url :", Current_Range["SearchUrl"])
        print("")

        Current_Range["SearchResults"] = []
        ### Process VRBO Website

        # Load URL
        # TODO: Remove this temp list refference with the loop
        browser.get(Current_Range["SearchUrl"])
        time.sleep(10)

        # Points browser to the main page and prevents pointing to the later generated iframe
        browser.switch_to.default_content()

        soup = bs(browser.page_source, 'html.parser')  #'lxml')  # Load the content for processing

        #items = soup.find_all(role="listitem")
        #items = soup.find_all('div', class_='HitExperiment')
        items = soup.find_all('div', {"data-wdio": re.compile('Waypoint*')})

        vrbo_records = []
        vrbo_record = {}

        for item in items:

            # Read property detail Url
            CurrentTag = item.find("a","media-flex__content")
            #item.find("a").get('href')
            if CurrentTag:
                vrbo_record["InfoUrl"]   = base_url + CurrentTag.get("href")

            # Merge text of multiple span tags. Ex: Condo, House, etc.
            CurrentTag = item.find("div", "HitExperimentInfo__content")
            if CurrentTag:
                CurrentTag = CurrentTag.find(class_="HitExperimentInfo__type-place-details")
            if CurrentTag:
                vrbo_record["Type"] = ' '.join(val.get_text(strip=True) for val in CurrentTag.findAll("span"))

            # Read headline. Ex: Adorable Cottage
            CurrentTag = item.find("div", "HitExperimentInfo__content")
            if CurrentTag:
                Current_Tag = CurrentTag.find(class_="HitExperimentInfo__headline")
            if CurrentTag:
                vrbo_record["Headline"] = CurrentTag.text

            # Read Sleep and Bed info. Merge text of multiple span tags. Ex: Sleeps 4 1 bedroom 2 beds
            CurrentTag = item.find("div", "HitExperimentInfo__content")

            if CurrentTag:
                CurrentTag = CurrentTag.find(class_="HitExperimentInfo__room-beds-details").findAll("span")
            if CurrentTag:
                vrbo_record["Sleeps"] = ' | '.join(val.get_text(strip=True) for val in CurrentTag)

            # Read Rating. Ex: Wonderful! 4.9/5()
            CurrentTag = item.find("footer", "media-flex__footer")
            if CurrentTag:
                CurrentTag = CurrentTag.find(class_="HitExperimentInfo__superlative")
            if CurrentTag:
                vrbo_record["Rating"] = CurrentTag.text

            # Read star rating. Ex: 4.9(131)
            CurrentTag = item.find("footer", "media-flex__footer")
            if CurrentTag:
                CurrentTag = CurrentTag.find(class_="HitExperimentInfo__starRating")
                if CurrentTag:
                    CurrentTag = CurrentTag.find(class_="Rating__label")
            if CurrentTag:
                vrbo_record["Reviews"] = CurrentTag.text

            # Read price. Ex: $215
            CurrentTag = item.find("footer", "media-flex__footer")
            if CurrentTag:
                CurrentTag = CurrentTag.find(class_="DualPrice__amount")
            vrbo_record["Price_Amount"] = CurrentTag.text

            # Read price period. Ex: avg/night
            CurrentTag = item.find("footer", "media-flex__footer")
            if CurrentTag:
                CurrentTag = CurrentTag.find(class_="DualPrice__period")
            vrbo_record["Price_Period"] = CurrentTag.text

            #vrbo_record["CancelMsg"] = item.contents[2].contents[0].contents[3].text                         # Free cancellation

            #vrbo_records.append(vrbo_record.copy())
            Current_Range["SearchResults"].append(vrbo_record.copy())
            # Get Availability Dates
            #sub_url = base_url+Url
            #browser_sub.get(sub_url)
            #browser_sub.switch_to.default_content()

print("The End!")

browser.close()
browser.quit()

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

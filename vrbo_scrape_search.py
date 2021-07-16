import json
import time
from bs4 import BeautifulSoup as bs
import datetime
import re
from datetime import datetime as dt
from selenium import webdriver
# import html_template
#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC

# JSON Explorer
# http://jsonviewer.stack.hu/

'''
Userful searches:

1. Find properties in specific locaiton(s) for the duration of X days within specified date period
    VA Beach, 10 days June, July, August 2021

2. Ex: 
    Are there any properties avalable for 5-9 days rental at these 3 specific locations between June 10 - August 20
'''

# TODO:  [x] Change type fo parameters of get_dat and  get_multiple_duration_dates to DICT to make more flex
# TODO:  [ ] Add ability to specify few not contiguous ranges, Ex: 7/10/21-07/15/21, 8/3/21-8/11/21
# TODO:  [ ] Ability to Exclude certain dates and or ranges
# TODO:  [ ] Add serch for multiple locations
# TODO:  [ ] Add other filters like property type and availability of pool etc.
# TODO:  [ ] Filter price in the data set because VRBO Site does not support ULR based max price filtering[
# FIXME: [ ] Test
# BUG:   [ ] Test


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

def Get_Images(p_item):
    #SimpleImageCarousel__image SimpleImageCarousel__image--cur
    raw_tag_res = p_item.find_all('div', attrs={"class": re.compile("SimpleImageCarousel__image--*")})
    #p_item.find('div', attrs={"class": re.compile("SimpleImageCarousel__image--*")}).attrs['style']

    image_list = []

    for raw_item in raw_tag_res:

        tmp =  raw_item.attrs['style']

        # Extract the URL out of the tag
        # 'background-image: url("https://media.vrbo.com/lodging/49000000/48990000/48981700/48981643/e1874d2c.c6.jpg");'
        result = re.findall(r'\"([^]]*)\"', tmp)

        if result:
            image_list.append(result[0])

    return image_list


def Get_Cancellation(p_item):
    # >>> item.contents[2].contents[0].contents[3].text               # Free cancellation
    return ""


#def get_dates(p_start, p_end, p_days, url_tmp):
def get_dates(params):
    """
    # generates dates for a single provided duration
    :param params: Dictionary
            {
                start : "",
                end   : "",
                days  : "",
                url   : ""
            }
    :return: list of dictionary object contaning duration, start, end and search urls
    """

    p_start = params["start"]
    p_end   = params["end"]
    p_days  = params["days"]
    p_url   = params["url"]

    DATE_FORMAT = "%Y-%m-%d"

    intervals = []
    date_set = {}

    start_date = dt.strptime(p_start, DATE_FORMAT)
    end_date   = dt.strptime(p_end, DATE_FORMAT)

    # Substracting one day because first day counts as well
    delta = datetime.timedelta(days=p_days-1)

    while (start_date+datetime.timedelta(days=p_days)) <= end_date:
        date_set["Duration"]    = p_days
        date_set["Start"]       = start_date.date().isoformat()
        date_set["End"]         = (start_date + delta).date().isoformat()
        date_set["SearchUrl"]   = p_url.replace("ARRIVAL_DATE",date_set["Start"]).replace("DEPARTURE_DATE", date_set["End"])

        intervals.append(date_set.copy())

        start_date += datetime.timedelta(days=1)

    return intervals

#def get_multiple_duration_dates(p_start, p_end, p_days, p_url, p_use_as_range=False):
def get_multiple_duration_dates(params):
    # generates dates for multiple durations
    """
    :param params:
    :return:
    """
    p_start        = params["start"]
    p_end          = params["end"]
    p_days         = params["days"]
    p_url          = params["url"]
    p_use_as_range = params["use_as_range"]



    if p_use_as_range and len(p_days) >= 2:
        tmp_range = range(p_days[0], p_days[-1]+1)
        all_durations =[num for num in tmp_range]

    else:
        all_durations = (p_days if type(p_days) is list else [p_days])

#        else:
#            raise Exception("Function: get_multiple_duration_dates.  Error: p_days parameter should have more than two elements if use_as_range is set to True")


    res_dates = []

    for dur in all_durations:

        res_dates.append(get_dates(
                                    {
                                        "start" : p_start,
                                        "end"   : p_end,
                                        "days"  : dur,
                                        "url"   : p_url
                                    }
                                  ))

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
start_str = "2021-07-17"
end_str   = "2021-07-30"
use_as_range = True
durations = [7,8]

UrlCollection = {"Period_Start" : start_str,
                 "Period_End"   : end_str,
                 "Durations"    : durations,
                 "Location"     : location,
                 "Results"      : get_multiple_duration_dates(
                                                                {
                                                                    "start"         : start_str,
                                                                    "end"           : end_str,
                                                                    "days"          : durations,
                                                                    "url"           : Url_Template,
                                                                    "use_as_range"  : True
                                                                }
                                                             )
                }

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
#browser_sub = webdriver.Chrome('./chromedriver', chrome_options=options)    # Browser for the future multithread

browser.implicitly_wait(12)
#browser_sub.implicitly_wait(10)

vrbo_record, vrbo_records = {}, []


for Current_Url in UrlCollection["Results"]:

    for Current_Range in Current_Url:

        print("    Duration   :", Current_Range["Duration"])
        print("    Start      :", Current_Range["Start"])
        print("    End        :", Current_Range["End"])
        print("    Search Url :", Current_Range["SearchUrl"])

        # Load URL
        browser.get(Current_Range["SearchUrl"])
        time.sleep(10)

        browser.switch_to.default_content()   # Points browser to the main page instead of later generated iframe
        soup = bs(browser.page_source, 'html.parser')  # Load the content for processing

        items = soup.find_all('div', attrs={"class": "HitExperiment", "role": "listitem"})


        for item in items:

            vrbo_record["Period_Start"] = UrlCollection["Period_Start"]
            vrbo_record["Period_End"]   = UrlCollection["Period_End"]
            vrbo_record["Duration"]     = Current_Range["Duration"]
            vrbo_record["Location"]     = UrlCollection["Location"]
            vrbo_record["Start"]        = Current_Range["Start"]
            vrbo_record["End"]          = Current_Range["End"]
            vrbo_record["SearchUrl"]    = Current_Range["SearchUrl"]
            vrbo_record["PropertyUrl"]  = base_url + Get_UrlInfo(item)
            vrbo_record["Images"]       = Get_Images(item)
            vrbo_record["Type"]         = Get_Type(item)
            vrbo_record["Headline"]     = Get_Headline(item)
            vrbo_record["Sleeps"]       = Get_Sleeps(item)
            vrbo_record["Rating"]       = Get_Rating(item)
            vrbo_record["Reviews"]      = Get_Reviews(item)
            vrbo_record["Price_Amount"] = Get_PriceAmount(item)
            vrbo_record["Price_Period"] = Get_Price_Period(item)
            #vrbo_record["Cancellation"] = Get_Cancellation(item)

            vrbo_records.append(vrbo_record.copy())

            vrbo_record = {}

        print("    Found      :", len(items) , "[", len(vrbo_records), "]")
        print("")

browser.close()
browser.quit()

print("Total records found :", len(vrbo_records))

if len(vrbo_records) > 0:

    # Exporting search results to the JSON file
    current_date_and_time = str(datetime.datetime.now())
    extension = ".json"
    json_filename = 'data_' + current_date_and_time + extension

    print('Exporting data to the', json_filename, ' file')

    with open(json_filename, 'w') as fp:
        json.dump(vrbo_records, fp, sort_keys=True, indent=4)


print("The End")

'''
Unused code
    #vrbo_record["Sleeps"] = item.find("div", "HitExperimentInfo__content")\
    #    .find(class_="HitExperimentInfo__room-beds-details")\
    #    .find("span",text=lambda val: val and val.startswith("Sleeps")).text
    #Returns: Sleeps 4



        #items = soup.find_all('div', {"data-wdio": re.compile('Waypoint*')})
        #items = soup.find_all('div',attrs={"class":"HitExperiment","role":"listitem","data-wdio":"hit"})

'''


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

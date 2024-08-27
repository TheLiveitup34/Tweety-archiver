#  This file is to fix http links that weren't being caught and fixed to origin 
#  This was also setup original to help scrape clubpenguin
#  @Author TheLiveitup34
# 
import os
import re
import json
import time
import requests
from colorama import Fore


# Updates paths to get the tweets already parsed
path_name = os.path.dirname(os.path.realpath(__file__)) + os.sep + "scraped" + os.sep + "clubpenguin" + os.sep + "media" + os.sep
dirs = os.listdir(path_name)
total_value = len(dirs)
i = 1
# loops through every folder directiory 
for path in dirs:
    os.system("clear()")
    os.system("clear")

    # prints out a percentage to see how many tweets have been updated
    percentage_string = ""
    percentage = ((i/total_value) * 100)
    for j in range(1, 11):
        if j * 10 <= percentage:
            percentage_string += f"{Fore.CYAN}="
        else:
            percentage_string += f"{Fore.BLACK}="
    i += 1
    print(f"{Fore.CYAN}Percentage Completed...{Fore.WHITE}")
    print(f"[{percentage_string}{Fore.WHITE}] {Fore.MAGENTA}{percentage:.2f}%{Fore.WHITE}\n")

    # opens up the tweet data and gets the http links or https links and updates the links
    f = open(f"{path_name}{path}{os.sep}{path}.json", "r+")
    data_tweet = json.loads(f.read())
    print(f"{Fore.CYAN}Working on {Fore.YELLOW}{path}{Fore.BLUE}")
    urls = re.findall("https://t\.co/[0-9A-Za-z]{0,23}", data_tweet["tweet_parsed"])
    urls_http = re.findall("http://t\.co/[0-9A-Za-z]{0,23}", data_tweet["tweet_parsed"])

    # Validates if links are found
    if len(urls_http) > len(urls):
        urls = urls_http
    if len(urls) > 0:
        print(f"\n{Fore.MAGENTA}Found Twitter Shortner links in Tweet..")
        print(f"{Fore.YELLOW}{urls}{Fore.WHITE}")
        print(f"\n{Fore.MAGENTA}Going to fetch origin urls...{Fore.WHITE}")
    else:
        print(f"{Fore.RED}No Links found{Fore.BLUE}")
        f.close()
        continue
    
    # loops through links found and updates the data
    for url in urls:
        res = None
        actual_url = None
        try:
            res = requests.get(url, timeout=3)
        except Exception as e:
            error = str(e)
            actual_url = re.findall("host='(.*?)'", error)[0]
            print(f"{Fore.YELLOW}Failed to reach domain. {actual_url}{Fore.WHITE}")
        if res != None:
            actual_url = res.url
        data_tweet["href_links"].append(actual_url)
        data_tweet["tweet_parsed"] = data_tweet["tweet_parsed"].replace(url, actual_url)
        print(f" - {Fore.BLUE}Fetched {Fore.YELLOW}{url} {Fore.BLUE}and found {Fore.YELLOW}{actual_url}\n{Fore.BLUE} - Replacing {Fore.YELLOW}{url}{Fore.BLUE} with found {Fore.YELLOW}{actual_url}{Fore.WHITE}")
    # Saves and updates the json data
    f.seek(0)
    f.write(json.dumps(data_tweet, indent=4))
    f.truncate()
    time.sleep(.5)
    f.close()
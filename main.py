#  This file is to run the main application making Tweety Easy to use 
#  This allows scraping via twitter/x Search
#  @Author TheLiveitup34
# 

import os
import re
import json
import time
import requests
import shutil
from tweety import Twitter
from tweety.filters import SearchFilters
from colorama import Fore

# This function does nothing but print a verbose information of the file being downloaded may have error displayed when running
def modify_download(file_name, file_size,downloaded_in_bites):
    if file_size == downloaded_in_bites:
        print(f"{Fore.BLUE}Downloaded {Fore.YELLOW}{file_name} {Fore.MAGENTA}{file_size // 1024}{Fore.BLUE}Mb{Fore.BLUE} Successfully...{Fore.WHITE}\n")
    else:
        print(f"{Fore.BLUE}Downloading file {Fore.YELLOW}{file_name}  {Fore.MAGENTA}{downloaded_in_bites // 1024}{Fore.BLUE}Mb/{Fore.MAGENTA}{file_size//1024}{Fore.BLUE}Mb{Fore.WHITE}")
    return None

# This funciton modifies the tweet and fetches new tweets recursivly
def modify_tweet(tweet):

    # Paresed ID checker
    if f"{tweet.id}:{tweet.author.username}" in parsed_ids:
        print(f"{Fore.BLUE}Found Already Parsed ID: {Fore.YELLOW}{tweet.id} {Fore.BLUE}Skiping..{Fore.WHITE}")
        return 
    
    # Establishing a path for the media to be stored
    if not os.path.exists(path_name + "media" + os.sep + tweet.id):
        os.makedirs(path_name + "media" + os.sep + tweet.id)

    # Stores the cached id
    parsed_ids.append(f"{tweet.id}:{tweet.author.username}")
    print(f"\n{Fore.MAGENTA}Found Tweet id:{Fore.YELLOW}{tweet.id}{Fore.MAGENTA} and formatting...{Fore.WHITE}\n")
  
    # Establashes the data structure for final output
    data_tweet = {
        "id": tweet.id,
        "date": str(tweet.date),
        "username": tweet.author.username,
        "display": tweet.author.name,
        "likes": tweet.likes,
        "language": tweet.language,
        "place": tweet.place,
        "views": tweet.views,
        "bookmark_count": tweet.bookmark_count,
        "quote_counts": tweet.quote_counts,
        "reply_counts": tweet.reply_counts,
        "retweet_counts": tweet.retweet_counts,
        "tweet_source": tweet.source,
        "is_quoted": tweet.is_quoted,
        "is_reply": tweet.is_reply,
        "href_links": [],
        "media_files": [],
        "tweet_raw": tweet.text,
        "tweet_parsed": ""
    }

    # Fetch Urls and convert them to original urls
    urls = re.findall("https://t\.co/[0-9A-Za-z]{0,23}", tweet.text)
    urls_http = re.findall("http://t\.co/[0-9A-Za-z]{0,23}", tweet.text)

    # Fix to check if urls are http or https
    if len(urls_http) > len(urls):
        urls = urls_http
        
    # Loop through Urls and fetch the origin link from twitter shortner
    if len(urls) > 0:
        print(f"\n{Fore.MAGENTA}Found Twitter Shortner links in Tweet..")
        print(f"{Fore.YELLOW}{urls}{Fore.WHITE}")
        print(f"\n{Fore.MAGENTA}Going to fetch origin urls...{Fore.WHITE}")
    for url in urls:
        res = None
        actual_url = None

        # Tries and catches dead urls returning resolved url
        try:
            res = requests.get(url, timeout=5)
        except Exception as e:
            error = str(e)
            actual_url = re.findall("host='(.*?)'", error)[0]
            print(f"{Fore.YELLOW}Failed to reach domain. {actual_url}{Fore.WHITE}")
        
        if res != None:
            actual_url = res.url
        data_tweet["href_links"].append(actual_url)
        tweet.text = tweet.text.replace(url, actual_url)
        print(f" - {Fore.BLUE}Fetched {Fore.YELLOW}{url} {Fore.BLUE}and found {Fore.YELLOW}{actual_url}\n{Fore.BLUE} - Replacing {Fore.YELLOW}{url}{Fore.BLUE} with found {Fore.YELLOW}{actual_url}{Fore.WHITE}")

    # Checks if media is in tweet data and fetches it
    if len(tweet.media) > 0:
        print(f"\n{Fore.MAGENTA}Found and Downloading All Media...{Fore.WHITE}")
        for media in tweet.media:
           file_name = media.download(None, modify_download)
           data_tweet["media_files"].append(file_name)
           shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + tweet.id + os.sep + file_name)
           os.remove(base_path + file_name)
           
    data_tweet["tweet_parsed"] = tweet.text

    # Checks if tweet is a quote and tries to download the tweet it quoted
    if tweet.is_quoted == True:
        if tweet.quoted_tweet != None:
            print(f"{Fore.MAGENTA}Quoted Tweet Detected and fetching...")
            try:
                modify_tweet(tweet.quoted_tweet)
                data_tweet["quoted_tweet_id"] = tweet.quoted_tweet.id
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify Quoted Tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()
            

    # Checks if tweet is a reply and tries to download the tweet it replied to
    if tweet.is_reply == True:
        if tweet.replied_to != None:
            print(f"{Fore.MAGENTA}Reply Tweet Detected and fetching...")
            try:
                modify_tweet(tweet.replied_to)
                data_tweet["replied_to_id"] = tweet.replied_to.id
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify Reply Tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()

    # Saves the file in the folder in scraped/USER/media/TWEET_ID/TWEET_ID.json
    f = open(path_name + "media" + os.sep + tweet.id + os.sep + tweet.id + ".json", "w")
    f.write(json.dumps(data_tweet, indent=4))
    f.close()
    return None

# Defines Paths for the app to use for path traversial
base_path = os.path.dirname(os.path.realpath(__file__)) + os.sep
path_name = os.path.dirname(os.path.realpath(__file__)) + os.sep + "scraped"

# Checks if base path is made and set
if not os.path.exists(path_name):
    os.makedirs(path_name)

# Starts Tweety app/session 
app = Twitter("session")
# Start calling to allow you to login Dynamicly Session is saved
app.start("", "")


# Start of username validation Loop
user = ""
confirm = ""
while user == "" and confirm == "":
    # Clear for a clean look 
    os.system("clear")

    # Username input and validation
    user = input(f"{Fore.YELLOW}Enter Target username: {Fore.WHITE}")
    if user == "":
        print(f"{Fore.RED}No {Fore.YELLOW}username{Fore.RED} was provided...{Fore.WHITE}")
        time.sleep(3)
        continue
    user = user.lower()

    # Confirms if you typed the correct username
    confirm = input(f"{Fore.WHITE}You entered '{Fore.YELLOW}{user}{Fore.WHITE}' is that correct? ({Fore.GREEN}y{Fore.WHITE}/{Fore.RED}n{Fore.WHITE}): ")
    confirm = confirm.lower()
    if confirm != "n" and confirm != "y":
        confirm = ""
        user = ""
        continue
    if confirm == "n":
        confirm = ""
        user = ""
        print("Username is not correct exiting...\n");
        continue


# Starts forming search stream
search_string = "(from:" + user + ")"

# Sets path to scraped/USERNAME and makes folder
path_name += os.sep + user
if not os.path.exists(path_name):
    os.makedirs(path_name)
path_name += os.sep



# Start Scrape loop 
export_name = None
fetched_manual = False

while True:
    # Reset Search Strings and parsed_ids
    search_string = "(from:" + user + ")"
    os.system("clear")
    parsed_ids = []
    if os.path.exists(path_name + 'parsed_ids.txt'):
        f = open(path_name + 'parsed_ids.txt', "r")
        parsed_ids = f.read().split("\n")
        f.close()
        
    # Get until input if wanted
    until = input("Enter Until date (leave empty if you dont want until): ")

    if until != "":
        search_string += f" until:{until}"
        print(f"Added Until {until} to search")
    else:
        print("No Until Entered Continuing...\n")

    # Get Since input if wanted
    since = input("Enter Since date (leave empty if you dont want since): ")
    if since != "":
        search_string += f" since:{since}"
    else:
        print("No Since Entered Continuing...\n")

    # Get checks if manual.txt exist and pulls from it to input manual twitter links/ID's
    if os.path.exists(base_path + 'manual.txt') and fetched_manual == False:
        print(f"{Fore.MAGENTA}\nManual ID's Detected and now scraping...{Fore.WHITE}")
        fetched_manual = True
        f = open(base_path + 'manual.txt', "r")
        manual_ids = f.read().split("\n")
        f.close()
        for manual in manual_ids:
            if manual == "":
                continue
            try:
                modify_tweet(app.tweet_detail(manual))
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify manual Tweet id:{Fore.YELLOW}{manual}{Fore.RED}, for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()
 
    # Starts Search loop for twitter searches to navigate pages
    print("Fetching Twitter Search...")
    cursor = ""
    while cursor != None:
        if cursor == "":
            cursor = None
        # Attempts to do twitter search
        try:
            tweets = app.search(search_string, filter_=SearchFilters.Latest(), cursor=cursor)
        except Exception as e:
            print(f"Search was {search_string}")
            print(f"{Fore.RED}Twitter Search failed for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
            if "Rate limit exceeded" in str(e):
                    exit()
            input("\n\nPress Enter to Continue...")
            continue

        # Updates cursor and Starts setting up data to parse 
        cursor = tweets.cursor
        if len(tweets) == 0:
            print(f"Search was {search_string}")
            print("No Tweets Found continuing...")
            cursor = None
            continue
        print("Getting Tweets..")
        if not os.path.exists(path_name + "media"):
            os.makedirs(path_name + "media")

        # Loops through tweets and tries to modify them
        for tweet in tweets:
            try:
                modify_tweet(tweet)
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify searched Tweet id:{Fore.YELLOW}{tweet.id}{Fore.RED}, for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()

        # Updates the parsed_ids 
        f = open(path_name + 'parsed_ids.txt', "w")
        f.write("\n".join(parsed_ids))
        f.close()

    # End of loop for While True: and allows to read data or observe anything 
    input("\n\nPress Enter to Continue...")

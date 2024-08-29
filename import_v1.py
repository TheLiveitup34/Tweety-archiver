#  This file was created to import a v1 cache of assets for clubpenguin at (https://ia601606.us.archive.org/view_archive.php?archive=/13/items/club-penguin-twitter-account/clubpenguin.zip)
#  Purpose of this file is to check if the tweet has been archived/scraped then store it else fix the images not represented in file
#  @Author TheLiveitup34
# 

import os
import re
import json
import requests
import shutil
from tweety import Twitter
from colorama import Fore



# This function does nothing but print a verbose information of the file being downloaded may have error displayed when running
def modify_download(file_name, file_size,downloaded_in_bites):
    if file_size == downloaded_in_bites:
        print(f"{Fore.BLUE}Downloaded {Fore.YELLOW}{file_name} {Fore.MAGENTA}{file_size // 1024}{Fore.BLUE}Mb{Fore.BLUE} Successfully...{Fore.WHITE}\n")
    else:
        print(f"{Fore.BLUE}Downloading file {Fore.YELLOW}{file_name}  {Fore.MAGENTA}{downloaded_in_bites // 1024}{Fore.BLUE}Mb/{Fore.MAGENTA}{file_size//1024}{Fore.BLUE}Mb{Fore.WHITE}")
    return None


# This funciton modifies the tweet and fetches new tweets recursivly
def modify_tweet(tweet, subtweet=False, parent_id=None):

    current_id = tweet.id
    if parent_id != None:
        current_id = parent_id
    # Paresed ID checker
    if f"{tweet.id}:{tweet.author.username}" in parsed_ids:
        print(f"{Fore.BLUE}Found Already Parsed ID: {Fore.YELLOW}{tweet.id} {Fore.BLUE}Skiping..{Fore.WHITE}")
        return 
    
    # Establishing a path for the media to be stored
    if not os.path.exists(path_name + "media" + os.sep + current_id):
        os.makedirs(path_name + "media" + os.sep + current_id)

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
        "poll_data": {},
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
           shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + current_id + os.sep + file_name)
           os.remove(base_path + file_name)
           
    data_tweet["tweet_parsed"] = tweet.text

    # Checks if tweet is a quote and tries to download the tweet it quoted
    if tweet.is_quoted == True:
        if tweet.quoted_tweet != None:
            print(f"{Fore.MAGENTA}Quoted Tweet Detected and fetching...")
            try:
                data_tweet["quoted_tweet"] = modify_tweet(tweet.quoted_tweet, True, tweet.id)
                data_tweet["quoted_tweet_id"] = tweet.quoted_tweet.id
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify Quoted Tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()
        else:
            print(f"{Fore.RED}Failed to Fetch Quote Tweet due to Quoted Tweet Provided in None Value{Fore.WHITE}")
            

    # Checks if tweet is a reply and tries to download the tweet it replied to
    if tweet.is_reply == True:
        if tweet.replied_to != None:
            print(f"{Fore.MAGENTA}Reply Tweet Detected and fetching...")
            try:
                data_tweet["replied_to_tweet"] = modify_tweet(tweet.replied_to, True, tweet.id)
                data_tweet["replied_to_id"] = tweet.replied_to.id
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify Reply Tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()
        else:
            print(f"{Fore.RED}Failed to Fetch Replied Tweet due to Replied Tweet Provied in None value")

    # Checks if tweet Poll exists in tweet
    if tweet.pool != None:
        data_tweet["poll_data"]["id"] = tweet.pool.id
        data_tweet["poll_data"]["name"] = tweet.pool.name
        data_tweet["poll_data"]["choices"] = []
        # Gets Poll Options
        for choices in tweet.pool.choices:
           data_tweet["poll_data"]["choices"].append({
               "name": choices.name, 
                "value": choices.value, 
                "key": choices.key, 
                "counts": choices.counts
            })
           
        data_tweet["poll_data"]["end_time"] = str(tweet.pool.end_time)
        data_tweet["poll_data"]["last_updated_time"] = str(tweet.pool.last_updated_time)
        data_tweet["poll_data"]["duration"] = tweet.pool.duration
        data_tweet["poll_data"]["user_ref"] = []

        for user_ref in tweet.pool.user_ref:
            data_tweet["poll_data"]["user_ref"].append(user_ref.username)
        data_tweet["poll_data"]["is_final"] = tweet.pool.is_final

    if subtweet == False:
        # Saves the file in the folder in scraped/USER/media/TWEET_ID/TWEET_ID.json
        f = open(path_name + "media" + os.sep + tweet.id + os.sep + tweet.id + ".json", "w")
        f.write(json.dumps(data_tweet, indent=4))
        f.close()
    return data_tweet

# Defines Paths for the app to use for path traversial
base_path = os.path.dirname(os.path.realpath(__file__)) + os.sep
path_name = os.path.dirname(os.path.realpath(__file__)) + os.sep + "scraped"
v1_path = os.path.dirname(os.path.realpath(__file__)) + os.sep + "v1" + os.sep

# Checks if clubpengin is set as this was built for a old cache of data to conver to current
if not os.path.exists(path_name):
    os.makedirs(path_name)
path_name += os.sep + "clubpenguin" + os.sep

# Start of Tweeter API Session
app = Twitter("session")
# Start calling to allow you to login Dynamicly Session is saved
app.start("", "")
user = ""
confirm = ""



# Gets all the files in the v1 folder of all v1 cached Data and loops through them
files = os.listdir(v1_path)
for file in files:

    # Fetches all previously fetched data
    parsed_ids = []
    if os.path.exists(path_name + 'parsed_ids.txt'):
        f = open(path_name + 'parsed_ids.txt', "r")
        parsed_ids = f.read().split("\n")
        f.close()

    # Skips the .json files as we know there filename before .json
    if ".json" in file:
        continue

    # Loads the .json file for data manipulation
    f = open(f"{v1_path}{file}.json", "r")
    data = json.loads(f.read())
    f.close()

    tweet_id = data["tweet_id"]
    file_name = data["filename"] + "." + data["extension"]
    
    # Checks if the tweet has been scraped before and if it has the media
    if os.path.exists(path_name + "media" + os.sep + str(data["tweet_id"])) == True:
        if os.path.exists(path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + data["filename"] + "." + data["extension"]) == False:
            
            # Copys the file into the tweet data and saves it as the og name
            shutil.copyfile(v1_path + file, path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + data["filename"] + "." + data["extension"])
            
            # Adds the media to the media_files array in Tweet data
            f = open(path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + str(data["tweet_id"]) + ".json", "r+")
            data_tweet = json.loads(f.read())
            if file_name not in data_tweet["media_files"]:
                data_tweet["media_files"].append(file_name)
                f.seek(0)
                f.write(json.dumps(data_tweet, indent=4))
                f.truncate()
            f.close()
            print(f"Found and copied {tweet_id}")

        else:
            print(f"Image already exists {tweet_id}")


    # Else of tweet not existing
    else:
        # Tries and catches to fetch the tweet if not found within scraped tweet
        try:
            # Scrapes the Tweet
            modify_tweet(app.tweet_detail(data["tweet_id"]))
            # checks if tweet downloaded the media after scraping the tweet does same as above 
            if os.path.exists(path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + data["filename"] + "." + data["extension"]) == False:
                shutil.copyfile(v1_path + file, path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + data["filename"] + "." + data["extension"])
                print(f"Found and copied {tweet_id}")
                f = open(path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + str(data["tweet_id"]) + ".json", "r+")
                data_tweet = json.loads(f.read())
                if file_name not in data_tweet["media_files"]:
                    data_tweet["media_files"].append(file_name)
                    f.seek(0)
                    f.write(json.dumps(data_tweet, indent=4))
                    f.truncate()
                f.close()
            else:
                print(f"Image already exists {tweet_id}")
                
        except Exception as e:
            # prints out any exceptions that may occur and kills the script if Rate Limit is detected
            print(f"{Fore.CYAN}Failed Tweet ID: {Fore.YELLOW}{tweet_id}{Fore.WHITE}")
            print(f"{Fore.RED}Error occured when attempting to fetch not found tweet: {Fore.YELLOW}{e}{Fore.WHITE}")
            if "Rate limit exceeded" in str(e):
                    exit()
    
    # Updates parsed_ids for new tweets scraped
    f = open(path_name + 'parsed_ids.txt', "w")
    f.write("\n".join(parsed_ids))
    f.close()
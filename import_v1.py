import os
import re
import json
import time
import requests
import shutil
from tweety import Twitter
from colorama import Fore


def modify_download(file_name, file_size,downloaded_in_bites):

    if file_size == downloaded_in_bites:
        
        print(f"{Fore.BLUE}Downloaded {Fore.YELLOW}{file_name} {Fore.MAGENTA}{file_size // 1024}{Fore.BLUE}Mb{Fore.BLUE} Successfully...{Fore.WHITE}\n")
    else:
        print(f"{Fore.BLUE}Downloading file {Fore.YELLOW}{file_name}  {Fore.MAGENTA}{downloaded_in_bites // 1024}{Fore.BLUE}Mb/{Fore.MAGENTA}{file_size//1024}{Fore.BLUE}Mb{Fore.WHITE}")

    return None

def modify_tweet(tweet):
    if f"{tweet.id}:{tweet.author.username}" in parsed_ids:
        print(f"{Fore.BLUE}Found Already Parsed ID: {Fore.YELLOW}{tweet.id} {Fore.BLUE}Skiping..{Fore.WHITE}")
        return 
    if not os.path.exists(path_name + "media" + os.sep + tweet.id):
        os.makedirs(path_name + "media" + os.sep + tweet.id)
    parsed_ids.append(f"{tweet.id}:{tweet.author.username}")
    print(f"\n{Fore.MAGENTA}Found Tweet id:{Fore.YELLOW}{tweet.id}{Fore.MAGENTA} and formatting...{Fore.WHITE}\n")
  
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
        "is_quoted": tweet.is_quoted,
        "is_reply": tweet.is_reply,
        "href_links": [],
        "media_files": [],
        "tweet_raw": tweet.text,
        "tweet_parsed": ""
    }

    # Check if tweet was a quoted tweet

    # Fetch Urls and convert them to original urls
    urls = re.findall("https://t\.co/[0-9A-Za-z]{0,23}", tweet.text)
    urls_http = re.findall("http://t\.co/[0-9A-Za-z]{0,23}", tweet.text)
    if len(urls_http) > len(urls):
        urls = urls_http
    if len(urls) > 0:
        print(f"\n{Fore.MAGENTA}Found Twitter Shortner links in Tweet..")
        print(f"{Fore.YELLOW}{urls}{Fore.WHITE}")
        print(f"\n{Fore.MAGENTA}Going to fetch origin urls...{Fore.WHITE}")
    for url in urls:
        res = None
        actual_url = None
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


    if len(tweet.media) > 0:
        print(f"\n{Fore.MAGENTA}Found and Downloading All Media...{Fore.WHITE}")
        for media in tweet.media:
           file_name = media.download(None, modify_download)
           data_tweet["media_files"].append(file_name)
           shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + tweet.id + os.sep + file_name)
           os.remove(base_path + file_name)

    data_tweet["tweet_parsed"] = tweet.text


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

    f = open(path_name + "media" + os.sep + tweet.id + os.sep + tweet.id + ".json", "w")
    f.write(json.dumps(data_tweet, indent=4))
    f.close()
    return None


base_path = os.path.dirname(os.path.realpath(__file__)) + os.sep
path_name = os.path.dirname(os.path.realpath(__file__)) + os.sep + "scraped"
v1_path = os.path.dirname(os.path.realpath(__file__)) + os.sep + "v1" + os.sep
if not os.path.exists(path_name):
    os.makedirs(path_name)
path_name += os.sep + "clubpenguin" + os.sep


app = Twitter("session")
# Start calling to allow you to login Dynamicly Session is saved
app.start("", "")
user = ""
confirm = ""


files = os.listdir(v1_path)
for file in files:
    parsed_ids = []
    if os.path.exists(path_name + 'parsed_ids.txt'):
        f = open(path_name + 'parsed_ids.txt', "r")
        parsed_ids = f.read().split("\n")
        f.close()
    if ".json" in file:
        continue
    f = open(f"{v1_path}{file}.json", "r")
    data = json.loads(f.read())
    f.close()
    tweet_id = data["tweet_id"]

    if os.path.exists(path_name + "media" + os.sep + str(data["tweet_id"])) == True:
        if os.path.exists(path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + data["filename"] + "." + data["extension"]) == False:
            shutil.copyfile(v1_path + file, path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + data["filename"] + "." + data["extension"])
            print(f"Found and copied {tweet_id}")
        else:
            print(f"Image already exists {tweet_id}")
    else:
        try:
            modify_tweet(app.tweet_detail(data["tweet_id"]))
            if os.path.exists(path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + data["filename"] + "." + data["extension"]) == False:
                shutil.copyfile(v1_path + file, path_name + "media" + os.sep + str(data["tweet_id"]) + os.sep + data["filename"] + "." + data["extension"])
                print(f"Found and copied {tweet_id}")
            else:
                print(f"Image already exists {tweet_id}")
        except Exception as e:
            print(f"Error occured when attempting to fetch not found tweet: {e}")
    
    f = open(path_name + 'parsed_ids.txt', "w")
    f.write("\n".join(parsed_ids))
    f.close()
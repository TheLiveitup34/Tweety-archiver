import re
import json
import time
import requests
import shutil
import os
from colorama import Fore


# Defines Paths for the app to use for path traversial
base_path = os.path.dirname(os.path.realpath(__file__)) + os.sep

parsed_ids = []



# This function does nothing but print a verbose information of the file being downloaded may have error displayed when running
def modify_download(file_name, file_size,downloaded_in_bites):
    if file_size == downloaded_in_bites:
        print(f"{Fore.BLUE}Downloaded {Fore.YELLOW}{file_name} {Fore.MAGENTA}{file_size // 1024}{Fore.BLUE}Mb{Fore.BLUE} Successfully...{Fore.WHITE}\n")
    else:
        print(f"{Fore.BLUE}Downloading file {Fore.YELLOW}{file_name}  {Fore.MAGENTA}{downloaded_in_bites // 1024}{Fore.BLUE}Mb/{Fore.MAGENTA}{file_size//1024}{Fore.BLUE}Mb{Fore.WHITE}")
    return None

# This funciton modifies the tweet and fetches new tweets recursivly
def modify_tweet(tweet, subtweet=False, parent_id=None, path_name=None, parsed_id_data=[]):
  
    if len(parsed_id_data) > 0:
        for parsed_id in parsed_id_data:
            if parent_id not in parsed_ids:
                parsed_ids.append(parsed_id)
    current_id = tweet.id
    if parent_id != None:
        current_id = parent_id
    if subtweet == False:
        parent_id = tweet.id
    # Paresed ID checker
    if f"{tweet.id}:{tweet.author.username}" in parsed_ids:
        print(f"{Fore.BLUE}Found Already Parsed ID: {Fore.YELLOW}{tweet.id} {Fore.BLUE}Skiping..{Fore.WHITE}")
        return None
    
    # Establishing a path for the media to be stored
    if not os.path.exists(path_name + "media" + os.sep + current_id) and subtweet == False:
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
        "tweet_parsed": "",
        "comments": []
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
                data_tweet["quoted_tweet"] = modify_tweet(tweet.quoted_tweet, True, parent_id=parent_id, path_name=path_name)
                data_tweet["quoted_tweet_id"] = tweet.quoted_tweet.id
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify Quoted Tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()
        else:
            print(f"{Fore.RED}Failed to Fetch Quote Tweet due to Quoted Tweet Provided in None Value{Fore.WHITE}")
            

    # Checks if tweet is a reply and tries to download the tweet it replied to
    if tweet.is_reply == True and subtweet == False:
        print(f"{Fore.MAGENTA}Reply to Tweet Detected and fetching...")
        try:
            replied_to = tweet.get_reply_to()
            data_tweet["replied_to_tweet"] = modify_tweet(replied_to, True, parent_id=parent_id,path_name=path_name)
            data_tweet["replied_to_id"] = replied_to.id
        except Exception as e:
            print(f"{Fore.RED}Failed to Modify Reply Tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
            if "Rate limit exceeded" in str(e):
                exit()

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
    
    if tweet.reply_counts > 0:
        # Start comment Loop
        comment_cursor = ""
        if subtweet == False:
            print(f"\n{Fore.MAGENTA}Attempting to fetch comments...{Fore.WHITE}")
        else:
            print(f"\n{Fore.MAGENTA}Attempting to fetch comments for subtweet id: {Fore.YELLOW}{current_id}{Fore.MAGENTA}...{Fore.WHITE}")
        while comment_cursor != None:
            if comment_cursor == "":
                comment_cursor = None
            
            try:
                comments = tweet.get_comments(cursor=comment_cursor)
                comment_cursor = comments.cursor
            except Exception as e:
                print(f"{Fore.RED}Attempt to Fetch comments failed for the following Reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()
                continue
            if len(comments) == 0:
                comment_cursor = None
                continue
            for comment in comments:
                for tweetComment in comment.tweets:
                    try:
                        tweet_comment_data = modify_tweet(tweetComment, True, parent_id=parent_id, path_name=path_name)
                        if tweet_comment_data != None:
                            data_tweet["comments"].append(tweet_comment_data)
                    except Exception as e:
                        print(f"{Fore.RED}Failed to Scrape Comment or data for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                        if "Rate limit exceeded" in str(e):
                            exit()
            
        
    
    if subtweet == False:
        # Saves the file in the folder in scraped/USER/media/TWEET_ID/TWEET_ID.json
        f = open(path_name + "media" + os.sep + tweet.id + os.sep + tweet.id + ".json", "w")
        f.write(json.dumps(data_tweet, indent=4))
        f.close()
        return parsed_ids
    return data_tweet

def fetch_username():
    confirm = ""
    user = ""
    while user == "":
        # Clear for a clean look 

        # Username input and validation
        user = input(f"{Fore.YELLOW}Enter Target username: {Fore.WHITE}")
        if user == "":
            print(f"{Fore.RED}No {Fore.YELLOW}username{Fore.RED} was provided...{Fore.WHITE}")
            time.sleep(3)
            continue
        user = user.lower()

        # Confirms if you typed the correct username
    return user

def confirm_data(msg =""):

    confirm = ""
    while confirm == "":
        confirm = input(f"\n{Fore.WHITE}{msg} {Fore.WHITE}({Fore.GREEN}y{Fore.WHITE}/{Fore.RED}n{Fore.WHITE}): ")
        confirm = confirm.lower()
        if confirm != "n" and confirm != "y":
            confirm = ""
            print(f"{Fore.RED}Invalid Response Type trying again...{Fore.WHITE}")
            continue
        if confirm == "n":
            confirm = ""
            return False
    return True

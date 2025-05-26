import os
import re
import json
import sys
import traceback
import time
import requests
import shutil
from colorama import Fore
from configs import configurations
from aac_to_mp3_converter import convert_aac_to_mp3
from async_download_media import async_download_media
from combine_ts_files_to_mp4 import combine_ts_files_to_mp4





# Defines Paths for the app to use for path traversial
base_path = os.path.dirname(os.path.realpath(__file__)) + os.sep

parsed_ids = []



# This function does nothing but print a verbose information of the file being downloaded may have error displayed when running
async def modify_download(file_name, file_size,downloaded_in_bites, verbose=True):
    # check if the file size is Mb or Kb for the display
    file_size_type = "B"
    file_size_type_display = file_size
    downloaded_in_bites_display = downloaded_in_bites
    if file_size > 1024:
        file_size_type = "Kb"
        file_size_type_display = file_size // 1024
        downloaded_in_bites_display = downloaded_in_bites // 1024
    elif file_size > 1024 * 1024:
        file_size = file_size // (1024 * 1024)
        file_size_type_display = "Mb"
        downloaded_in_bites_display = downloaded_in_bites // (1024 * 1024)
    elif file_size > 1024 * 1024 * 1024:
        file_size = file_size // (1024 * 1024 * 1024)
        file_size_type_display = "Gb"
        downloaded_in_bites_display = downloaded_in_bites // (1024 * 1024 * 1024)

    if file_size == downloaded_in_bites:
        print(f"{Fore.BLUE}Downloaded {Fore.YELLOW}{file_name} {Fore.MAGENTA}{file_size_type_display}{Fore.BLUE}{file_size_type}{Fore.BLUE} Successfully...{Fore.WHITE}\n")
    else:
        if verbose == True:
            print(f"{Fore.BLUE}Downloading file {Fore.YELLOW}{file_name}  {Fore.MAGENTA}{downloaded_in_bites_display}{Fore.BLUE}{file_size_type}/{Fore.MAGENTA}{file_size_type_display}{Fore.BLUE}{file_size_type}{Fore.WHITE}")
    return None

async def download_media(media_url, modify_download, verbose=True):
    # download in the current directory
    file_name = os.path.basename(media_url)
    file_name = os.path.join(os.getcwd(), file_name)
    # download the file
    try:
        response = requests.get(media_url, stream=True)
        file_size = int(response.headers.get('content-length', 0))
        with open(file_name, 'wb') as file:
            downloaded_in_bites = 0
            for data in response.iter_content(chunk_size=1024):
                file.write(data)
                downloaded_in_bites += len(data)
                await modify_download(os.path.basename(file_name), file_size, downloaded_in_bites, verbose)
    except Exception as e:
        print(f"{Fore.RED}Failed to download {Fore.YELLOW}{media_url} {Fore.RED}to {Fore.YELLOW}{file_name} {Fore.RED}due to {Fore.MAGENTA}{e}{Fore.WHITE}")
        return None
    return os.path.basename(file_name)


# This funciton modifies the tweet and fetches new tweets recursivly
async def modify_tweet(tweet, subtweet=False, parent_id=None, path_name=None, parsed_id_data=[], app=None, debug=False):
    if "author" not in tweet.__dict__:
        # print
        print(f"{Fore.RED}Failed to Parse Tweet due to the following reason: {Fore.YELLOW}Tweet is a User Object{Fore.WHITE}")
        exit()

    cfg = await configurations()  
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
        print(f"{Fore.BLUE}Found Already Parsed ID: {Fore.YELLOW}{tweet.id} {Fore.BLUE}Skipping..{Fore.WHITE}")
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
        "verified": tweet.author.verified,
        "protected": tweet.author.protected,
        "parody": tweet.author.is_parody_account,
        "commentary": tweet.author.is_commentary_account,
        "fan": tweet.author.is_fan_account,
        "automated": tweet.author.is_automated,
        "language": tweet.language,
        "likes": tweet.likes,
        "reply_counts": tweet.reply_counts,
        "retweet_counts": tweet.retweet_counts,
        "quote_counts": tweet.quote_counts,
        "bookmark_count": tweet.bookmark_count,
        "views": tweet.views,
        "tweet_source": tweet.source,
        "place": tweet.place,
        "warning": tweet.warning,
        "has_newer_version": tweet.has_newer_version,
        "has_moderated_replies": tweet.has_moderated_replies,
        "is_sensitive": tweet.is_sensitive,
        "community_note": tweet.community_note,
        "is_quoted": tweet.is_quoted,
        "is_reply": tweet.is_reply,
        "tweet_raw": tweet.text
    }

    if len(tweet.media) > 0:
        print(f"{Fore.MAGENTA}Found Taged users in Tweet...{Fore.WHITE}")
        data_tweet["media_tags"] = tweet.media[0].tagged_users
    
    afiliate_label = None
    if "content" in tweet._raw:
        afiliate_label = tweet._raw["content"]["itemContent"]["tweet_results"]["result"]["core"]["user_results"]["result"]["affiliates_highlighted_label"]
    else:
        afiliate_label = tweet._raw["item"]["itemContent"]["tweet_results"]["result"]["core"]["user_results"]["result"]["affiliates_highlighted_label"]
    
    if afiliate_label != {}:
        print(f"{Fore.MAGENTA}Found Affiliate Label...{Fore.WHITE}")
        afiliate_label = afiliate_label["label"]
        print(f"{Fore.MAGENTA}Found Affiliate Label...{Fore.WHITE}")
        data_tweet["affiliate"] = {
            "url": afiliate_label["url"]["url"],
            "badge": afiliate_label["badge"]["url"],
            "description": afiliate_label["description"],
            "user_label_type": afiliate_label["userLabelType"],
            "user_label_display_type": afiliate_label["userLabelDisplayType"]
        }

        if cfg["GrabMedia"] == True:
            print(f"{Fore.MAGENTA}Downloading Affiliate Label Media...{Fore.WHITE}")
            # download the media
            file_name = await download_media(afiliate_label["badge"]["url"], modify_download)
            shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + current_id + os.sep + file_name)
            os.remove(base_path + file_name)
            data_tweet["affiliate"]["badge_file_name"] = file_name

    if "community" in tweet.__dict__:
        print(f"{Fore.MAGENTA}Found Community...{Fore.WHITE}")
        data_tweet["community"] = tweet.community
        data_tweet["community_role"] = tweet.author.community_role

    if cfg["GrabArticles"] == True:
        if "article" in tweet.__dict__ and tweet.article != None:
            print(f"{Fore.MAGENTA}Found Article...{Fore.WHITE}")
            data_tweet["article"] = {}
            data_tweet["article"]["id"] = tweet.article.id
            data_tweet["article"]["created_at"] = str(tweet.article.date)
            data_tweet["article"]["title"] = tweet.article.title
            data_tweet["article"]["text"] = tweet.article.text
            data_tweet["article"]["cover_media"] = {}
            data_tweet["article"]["cover_media"]["alt_text"] = tweet.article.cover_media.alt_text
            print(f"{Fore.MAGENTA}Downloading Article Cover Media...{Fore.WHITE}")
            if "url" in tweet.article.cover_media.__dict__:
                data_tweet["article"]["cover_media"]["url"] = tweet.article.cover_media.url
                data_tweet["article"]["cover_media"]["width"] = tweet.article.cover_media.width
                data_tweet["article"]["cover_media"]["height"] = tweet.article.cover_media.height
            else:
                best_stream = await tweet.article.cover_media.best_stream()
                data_tweet["article"]["cover_media"]["url"] = best_stream.url
                data_tweet["article"]["cover_media"]["content_type"] = best_stream.content_type.lower()

            file_name = await download_media(data_tweet["article"]["cover_media"]["url"], modify_download)
            shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + current_id + os.sep + file_name)
            os.remove(base_path + file_name)

            data_tweet["article"]["cover_media"]["file_name"] = file_name
            if len(tweet.article.media) > 0:
                print(f"{Fore.MAGENTA}Found Article Media...{Fore.WHITE}")
                data_tweet["article"]["media"] = []
                for media in tweet.article.media:
                    data_url = None
                    if "url" in media.__dict__:
                        data_url = media.url
                    else:
                        best_stream = await media.best_stream()
                        data_url = best_stream.url
                    file_name = await download_media(data_url, modify_download)
                    shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + current_id + os.sep + file_name)
                    os.remove(base_path + file_name)
                    if "url" in media.__dict__:
                        data_tweet["article"]["media"].append({
                            "url": media.url,
                            "alt_text": media.alt_text,
                            "width": media.width,
                            "height": media.height,
                            "file_name": file_name
                        })
                    else:
                        data_tweet["article"]["media"].append({
                            "url": best_stream.url,
                            "content_type": best_stream.content_type.lower(),
                            "alt_text": media.alt_text,
                            "file_name": file_name
                        })

    if cfg["ConvertLinks"] == True:
        print(f"{Fore.MAGENTA}Converting Twitter Shortner Links to Original Links...{Fore.WHITE}")
        data_tweet["href_links"] = []
    
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
                if url.startswith("http://"):
                    url = url.replace("http://", "https://")
                res = requests.get(url, allow_redirects=False, timeout=5)
                actual_url = res.next.url
            except Exception as e:
                error = str(e)
                print(f"{Fore.RED}Failed to reach domain. Error: {error}")
                if debug:
                    # loop through the traceback and print all the lines
                    print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                    exc_type, exc_value, exc_traceback = sys.exc_info()

                    # Format the traceback
                    traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                    # Print the formatted traceback
                    print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                    for line in traceback_details:
                        print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
            if actual_url == None:
                continue
        
            data_tweet["href_links"].append(actual_url)
            tweet.text = tweet.text.replace(url, actual_url)
            print(f" - {Fore.BLUE}Fetched {Fore.YELLOW}{url} {Fore.BLUE}and found {Fore.YELLOW}{actual_url}\n{Fore.BLUE} - Replacing {Fore.YELLOW}{url}{Fore.BLUE} with found {Fore.YELLOW}{actual_url}{Fore.WHITE}")
        data_tweet["tweet_parsed"] = tweet.text

    if cfg["GrabMedia"] == True:
        data_tweet["media"] = []
        print(f"{Fore.MAGENTA}Checking for Media in Tweet...{Fore.WHITE}")
    # Checks if media is in tweet data and fetches it
        if len(tweet.media) > 0:
            print(f"\n{Fore.MAGENTA}Found and Downloading All Media...{Fore.WHITE}")
            for media in tweet.media:
                file_name = await media.download(None, modify_download)
                shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + current_id + os.sep + file_name)
                os.remove(base_path + file_name)
                data_tweet["media"].append({
                    "url": media.url,
                    "alt_text": media.alt_text,
                    "file_name": file_name,
                    "source_user": []
                })
                if "sensitive_media_warning" in media._raw:
                    print(f"{Fore.MAGENTA}Found Sensitive Media Warning...{Fore.WHITE}")
                    data_tweet["media"][-1]["sensitive_warning"] = []
                    sensitive_media_warnings = media._raw["sensitive_media_warning"].keys()
                    for warning in sensitive_media_warnings:
                        data_tweet["media"][-1]["sensitive_warning"].append({
                            "type": warning,
                            "is_sensitive": media._raw["sensitive_media_warning"][warning]
                        })
                if "source_user" in media.__dict__ and media.source_user != None:
                    print(f"{Fore.MAGENTA}Found Source User in Media...{Fore.WHITE}")
                    data_tweet["media"][-1]["source_user"].append({
                        "username": media.source_user.username,
                        "display": media.source_user.name,
                        "verified": media.source_user.verified
                    })
            
    # Checks if tweet is Quoting another tweet and tries to download the tweet it quoted
    if cfg["GrabTweetQuoted"] == True:
        # Checks if tweet is a quote and tries to download the tweet it quoted
        if tweet.is_quoted == True:
            if tweet.quoted_tweet != None:
                print(f"{Fore.MAGENTA}Quoted Tweet Detected and fetching...")
                try:
                    data_tweet["quoted_tweet"] = await modify_tweet(tweet.quoted_tweet, True, parent_id=parent_id, path_name=path_name, app=app, debug=debug)
                    data_tweet["quoted_tweet_id"] = tweet.quoted_tweet.id
                except Exception as e:
                    print(f"{Fore.RED}Failed to Modify Quoted Tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                    if debug:
                        # loop through the traceback and print all the lines
                        print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                        exc_type, exc_value, exc_traceback = sys.exc_info()

                        # Format the traceback
                        traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                        # Print the formatted traceback
                        print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                        for line in traceback_details:
                            print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                    if "Rate limit exceeded" in str(e):
                        exit()
            else:
                print(f"{Fore.RED}Failed to Fetch Quote Tweet due to Quoted Tweet Provided in None Value{Fore.WHITE}")


    # Checks if tweet is a subtweet and tries to download the tweet it subtweeted
    if cfg["GrabQuoteRetweets"] == True:
        if tweet.quote_counts > 0 and subtweet == False:
            print(f"{Fore.MAGENTA}Subtweet Detected and fetching...")
            data_tweet["tweets_quoting"] = []
            quoted_cursor = ""
            quotes = None
            while quoted_cursor != None:
                if quoted_cursor == "":
                    quoted_cursor = None


                try:
                    quotes = await app.tweet_detail_quotes(tweet, cursor=quoted_cursor)
                    quoted_cursor = quotes.cursor
                except Exception as e:
                    print(f"{Fore.RED}Failed to Fetch Quoted Tweets of the main tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                    if debug:
                        # loop through the traceback and print all the lines
                        print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                        exc_type, exc_value, exc_traceback = sys.exc_info()

                        # Format the traceback
                        traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                        # Print the formatted traceback
                        print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                        for line in traceback_details:
                            print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                    if "Rate limit exceeded" in str(e):
                        exit()
                if quotes == None:
                    quoted_cursor = None
                    continue
                for quote in quotes:
                    print(f"{Fore.MAGENTA}Found Quoted Tweet id: {Fore.YELLOW}{quote.id}{Fore.MAGENTA} and formatting...{Fore.WHITE}")
                    tweetquotes = await modify_tweet(quote, True, parent_id=parent_id, path_name=path_name, app=app, debug=debug) 
                    data_tweet["tweets_quoting"].append(tweetquotes)


    if cfg["GrabRetweetedBy"] == True:
        data_tweet["retweet_users"] = []
        # Checks if tweet has any retweets and tries to download the user list
        if tweet.retweet_counts > 0:
                print(f"{Fore.MAGENTA}Retweet User List Detected and fetching...")
                
                # initaizes the loop to fetch all the users that retweeted the tweet
                retweets_cursor = ""
                while retweets_cursor != None:
                    if retweets_cursor == "":
                        retweets_cursor = None

                    try:
                        retweets = await app.tweet_detail_retweets(tweet, cursor=retweets_cursor)
                        retweets_cursor = retweets.cursor
                    except Exception as e:
                        print(f"{Fore.RED}Failed to Fetch Retweet User List of the main tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                        if debug:
                            # loop through the traceback and print all the lines
                            print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                            exc_type, exc_value, exc_traceback = sys.exc_info()

                            # Format the traceback
                            traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                            # Print the formatted traceback
                            print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                            for line in traceback_details:
                                print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                        if "Rate limit exceeded" in str(e):
                            exit()
                    if len(retweets) == 0:
                        retweets_cursor = None
                        continue
                    for retweet in retweets:
                        print(f"{Fore.MAGENTA}Found Retweet User: {Fore.YELLOW}{retweet.username}{Fore.MAGENTA} and formatting...{Fore.WHITE}")
                        data_tweet["retweet_users"].append({
                            "username": retweet.username,
                            "display": retweet.name,
                            "verified": retweet.verified,
                            "protected": retweet.protected,
                            "parody": retweet.is_parody_account,
                            "commentary": retweet.is_commentary_account,
                            "fan": retweet.is_fan_account,
                            "automated": retweet.is_automated
                        })

                        afiliate_label = None
                        if "content" in retweet._raw:
                            afiliate_label = retweet._raw["content"]["itemContent"]["user_results"]["result"]["affiliates_highlighted_label"]
                        else:
                            afiliate_label = retweet._raw["item"]["itemContent"]["user_results"]["result"]["affiliates_highlighted_label"]
                       
                        if afiliate_label != {}:
                            print(f"{Fore.MAGENTA}Found Affiliate Label...{Fore.WHITE}")
                            afiliate_label = afiliate_label["label"]
                            print(f"{Fore.MAGENTA}Found Affiliate Label...{Fore.WHITE}")
                            data_tweet["retweet_users"][-1]["affiliate"] = {
                                "url": afiliate_label["url"]["url"],
                                "badge": afiliate_label["badge"]["url"],
                                "description": afiliate_label["description"],
                                "user_label_type": afiliate_label["userLabelType"],
                                "user_label_display_type": afiliate_label["userLabelDisplayType"]
                            }

                            if cfg["GrabMedia"] == True:
                                print(f"{Fore.MAGENTA}Downloading Affiliate Label Media...{Fore.WHITE}")
                                # download the media
                                file_name = await download_media(afiliate_label["badge"]["url"], modify_download)
                                shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + current_id + os.sep + file_name)
                                os.remove(base_path + file_name)
                                data_tweet["retweet_users"][-1]["affiliate"]["badge_file_name"] = file_name

                        if "community" in retweet.__dict__:
                            print(f"{Fore.MAGENTA}Found Community...{Fore.WHITE}")
                            data_tweet["retweet_users"][-1]["community"] = retweet.community
                            data_tweet["retweet_users"][-1]["community_role"] = retweet.community_role

    if cfg["GrabRepliedToTweet"] == True:
        # Checks if tweet is a reply and tries to download the tweet it replied to
        if tweet.is_reply == True and subtweet == False:
            print(f"{Fore.MAGENTA}Reply to Tweet Detected and fetching...")
            try:
                replied_to = await tweet.get_reply_to()
                data_tweet["replied_to_tweet"] = await modify_tweet(replied_to, True, parent_id=parent_id,path_name=path_name, app=app, debug=debug)
                data_tweet["replied_to_id"] = replied_to.id
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify Reply Tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if debug:
                    # loop through the traceback and print all the lines
                        print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                        exc_type, exc_value, exc_traceback = sys.exc_info()

                        # Format the traceback
                        traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                        # Print the formatted traceback
                        print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                        for line in traceback_details:
                            print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                if "Rate limit exceeded" in str(e):
                    exit()

    if cfg["GrabPolls"] == True:
    # Checks if tweet Poll exists in tweet
        if tweet.pool != None:
            print(f"{Fore.MAGENTA}Poll Detected and fetching...")
            data_tweet["poll_data"] = {}
            data_tweet["poll_data"]["id"] = tweet.pool.id
            data_tweet["poll_data"]["name"] = tweet.pool.name
            data_tweet["poll_data"]["choices"] = []
            # Gets Poll Options
            for choices in tweet.pool.choices:
                print(f"{Fore.MAGENTA}Found Poll Option: {Fore.YELLOW}{choices.name}{Fore.MAGENTA} and formatting...{Fore.WHITE}")
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
                print(f"{Fore.MAGENTA}Found Poll User Reference: {Fore.YELLOW}{user_ref.username}{Fore.MAGENTA} and formatting...{Fore.WHITE}")
                data_tweet["poll_data"]["user_ref"].append(user_ref.username)
            data_tweet["poll_data"]["is_final"] = tweet.pool.is_final
    
    if cfg["GrabReplies"] == True:   

        if tweet.reply_counts > 0:
            print(f"{Fore.MAGENTA}Replies Detected and fetching...")
            data_tweet["comments"] = []
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
                    if cfg["GrabHiddenReplies"] == True: 
                        comments = await tweet.get_comments(cursor=comment_cursor, get_hidden=True) #Note for Liv, if possible, can we put hidden replies in it's own section?
                    else:
                        comments = await tweet.get_comments(cursor=comment_cursor)
                    comment_cursor = comments.cursor
                except Exception as e:
                    print(f"{Fore.RED}Attempt to Fetch comments failed for the following Reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                    if debug:
                        # loop through the traceback and print all the lines
                        print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                        exc_type, exc_value, exc_traceback = sys.exc_info()

                        # Format the traceback
                        traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                        # Print the formatted traceback
                        print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                        for line in traceback_details:
                            print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                    if "Rate limit exceeded" in str(e):
                        exit()
                    continue
                if len(comments) == 0:
                    print(f"{Fore.MAGENTA}No Comments Found for the Tweet...{Fore.WHITE}")
                    comment_cursor = None
                    continue
                for comment in comments:
                    for tweetComment in comment.tweets:
                        try:
                            tweet_comment_data = await modify_tweet(tweetComment, True, parent_id=parent_id, path_name=path_name, app=app, debug=debug)
                            print(f"{Fore.MAGENTA}Found Comment id: {Fore.YELLOW}{tweetComment.id}{Fore.MAGENTA} and formatting...{Fore.WHITE}")
                            if tweet_comment_data != None:
                                data_tweet["comments"].append(tweet_comment_data)
                        except Exception as e:
                            print(f"{Fore.RED}Failed to Scrape Comment or data for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                            if debug:
                                # loop through the traceback and print all the lines
                                print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                                exc_type, exc_value, exc_traceback = sys.exc_info()

                                # Format the traceback
                                traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                                # Print the formatted traceback
                                print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                                for line in traceback_details:
                                    print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                            if "Rate limit exceeded" in str(e):
                                exit()
            
    if cfg["GrabEditHistory"] == True:   
        if tweet.edit_control != None:
            if len(tweet.edit_control.tweet_ids) > 1:
                print(f"{Fore.MAGENTA}Edit History Detected and fetching...")
                data_tweet["edit_history"] = [] 
                edits = await app.tweet_edit_history(tweet.id)
                for edit in edits:
                    try:
                        print(f"{Fore.MAGENTA}Found Edit id: {Fore.YELLOW}{edit.id}{Fore.MAGENTA} and formatting...{Fore.WHITE}")
                        edithistory = await modify_tweet(edit, True, parent_id=parent_id, path_name=path_name, app=app, debug=debug)
                        if edithistory != None:
                            data_tweet["edit_history"].append(edithistory)
                    except Exception as e:
                        print(f"{Fore.RED}Failed to Scrape Edit History for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                        if debug:
                            # loop through the traceback and print all the lines
                            print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                            exc_type, exc_value, exc_traceback = sys.exc_info()

                            # Format the traceback
                            traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                            # Print the formatted traceback
                            print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                            for line in traceback_details:
                                print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                     
                        if "Rate limit exceeded" in str(e):
                            exit()
    
    if cfg["GrabAudioSpace"] == True:

        if tweet.audio_space_id != None:
            audiosound = None
            data_tweet["audio_space"] = []
            audiosound_download = False
            print(f"{Fore.MAGENTA}Audio Space Detected and fetching...")
            try:
                audiosound = await app.get_audio_space(tweet.audio_space_id)
                audio_url = await audiosound.get_stream_link()

                transcript_url = audio_url.direct_url
                # get everything before the last /
                chunk_url = transcript_url.replace(transcript_url.split("/")[-1], "")

                # fetch data from the transcript url
                transcript = requests.get(transcript_url)
                # get the text from the transcript
                transcript_text = transcript.text
                # find all the chunck_*_a.aac files in the text
                chunk_files = re.findall("chunk_(.*)_a\.aac", transcript_text)
                # add chunc_ and _a.aac to the files
               
                chunk_files = [f"chunk_{file}_a.aac" for file in chunk_files]


                # check if a chucks_download folder exists
                chunks_dir = path_name + "media" + os.sep + current_id + os.sep + "chunks_download"
                if not os.path.exists(chunks_dir):
                    os.makedirs(chunks_dir)


                result = await async_download_media(media_url=chunk_url, files=chunk_files, output_path=chunks_dir, max_concurrent=15)
                if result == None:
                    print(f"{Fore.RED}Failed to download audio chunks{Fore.WHITE}")
                    raise Exception("Failed to download audio chunks")

                chunk_files = [f"{chunks_dir}{os.sep}{file}" for file in chunk_files]
                
                # convert the chunks to mp3
                print(f"{Fore.MAGENTA}Converting {Fore.YELLOW}{len(chunk_files)} {Fore.MAGENTA}chunks to mp3...{Fore.WHITE}")
                convert_success = convert_aac_to_mp3(
                    file_list=chunk_files,
                    output_file=f"{path_name}media{os.sep}{current_id}{os.sep}{audiosound.id}.mp3"
                )
                audiosound_download = True
                if convert_success == False:
                    print(f"{Fore.RED}Failed to convert audio chunks to mp3{Fore.WHITE}")
                else:
                    print(f"{Fore.MAGENTA}Converted {Fore.YELLOW}{len(chunk_files)} {Fore.MAGENTA}chunks to mp3...{Fore.WHITE}")
                    # delete the chunks
                    for chunk_file in chunk_files:
                        os.remove(chunk_file)
                    # delete the chunks_download folder
                    shutil.rmtree(path_name + "media" + os.sep + current_id + os.sep + "chunks_download")
                del chunk_url
                del transcript
                del transcript_text

                print(f"{Fore.MAGENTA}Cleaned up chunck donloads and grabing data.{Fore.WHITE}")
            except Exception as e:
                print(f"{Fore.RED}Failed to Scrape Audio Spaces for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if debug:
                    # loop through the traceback and print all the lines
                    print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                    exc_type, exc_value, exc_traceback = sys.exc_info()

                    # Format the traceback
                    traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                    # Print the formatted traceback
                    print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                    for line in traceback_details:
                        print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                if "Rate limit exceeded" in str(e):
                    print(f"{Fore.RED}Rate limit exceeded...{Fore.WHITE}")
                    exit()
            if audiosound != None:
                if audiosound_download == False:
                    print(f"{Fore.RED}WARNING: {Fore.CYAN}Audio Space may not be available this may be the reason for the error.. check the original audio space if this is the case.{Fore.WHITE}")
                data_tweet["audio_space"].append({
                    "id": audiosound.id,
                    "title": audiosound.title,
                    "state": audiosound.state,
                    "created_at": str(audiosound.created_at),
                    "started_at": str(audiosound.started_at),
                    "ended_at": str(audiosound.ended_at),
                    "updated_at": str(audiosound.updated_at),
                    "total_live_listeners": int(audiosound.total_live_listeners),
                    "total_replay_watched": audiosound.total_replay_watched,
                    "disallow_join": audiosound.disallow_join,
                    "is_employee_only": audiosound.is_employee_only,
                    "is_locked": audiosound.is_locked,
                    "is_muted": audiosound.is_muted,
                    "creator": {
                        "username": audiosound.creator.username,
                        "display": audiosound.creator.name,
                        "verified": audiosound.creator.verified
                    },
                    "admins": [],
                    "speakers": [], 
                })
                if audiosound_download == True:
                    data_tweet["audio_space"][-1]["file_name"] = f"{audiosound.id}.mp3"

                for admin in audiosound.admins:
                    data_tweet["audio_space"][-1]["admins"].append({
                        "twitter_screen_name": admin.twitter_screen_name,
                        "username": admin.username,
                        "display": admin.name,
                        "verified": admin.is_verified
                    })
                for speaker in audiosound.speakers:
                    data_tweet["audio_space"][-1]["speakers"].append({
                        "twitter_screen_name": speaker.twitter_screen_name,
                        "username": speaker.username,
                        "display": speaker.name,
                        "verified": speaker.is_verified
                    })

    if cfg["GrabBroadcasts"] == True:
        if tweet.broadcast != None:

            # write custom function to get broadcast by id
            def get_broadcast_by_id(self, broadcast_id):
                variables = {'id': broadcast_id}
                features = {
                    'articles_preview_enabled': True,
                    'c9s_tweet_anatomy_moderator_badge_enabled': True,
                    'communities_web_enable_tweet_community_results_fetch': True,
                    'creator_subscriptions_quote_tweet_preview_enabled': False,
                    'creator_subscriptions_tweet_preview_api_enabled': True,
                    'freedom_of_speech_not_reach_fetch_enabled': True,
                    'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
                    'longform_notetweets_consumption_enabled': True,
                    'longform_notetweets_inline_media_enabled': True,
                    'longform_notetweets_rich_text_read_enabled': True,
                    'premium_content_api_read_enabled': False,
                    'profile_label_improvements_pcf_label_in_post_enabled': True,
                    'responsive_web_edit_tweet_api_enabled': True,
                    'responsive_web_enhance_cards_enabled': False,
                    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                    'responsive_web_graphql_timeline_navigation_enabled': True,
                    'responsive_web_grok_analysis_button_from_backend': True,
                    'responsive_web_grok_analyze_button_fetch_trends_enabled': False,
                    'responsive_web_grok_analyze_post_followups_enabled': True,
                    'responsive_web_grok_image_annotation_enabled': True,
                    'responsive_web_grok_share_attachment_enabled': True,
                    'responsive_web_grok_show_grok_translated_post': False,
                    'responsive_web_jetfuel_frame': False,
                    'responsive_web_twitter_article_tweet_consumption_enabled': True,
                    'rweb_tipjar_consumption_enabled': True,
                    'standardized_nudges_misinfo': True,
                    'tweet_awards_web_tipping_enabled': False,
                    'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
                    'verified_phone_label_enabled': False,
                    'view_counts_everywhere_api_enabled': True
                }
                params = {
                    'variables': json.dumps(variables, separators=(',', ':')),
                    'features': json.dumps(features, separators=(',', ':')),
                }
                return {'headers': {},'method':"GET", 'url': "https://x.com/i/api/graphql/TVpOsxrXbB4yWQYxGCjBbw/BroadcastQuery",'params': params}
            app.http._builder.get_broadcast_by_id = get_broadcast_by_id
            async def get_broadcast_by_id(self, broadcast_id):
                response_data = self._builder.get_broadcast_by_id(self._builder, broadcast_id)
                response = await self.__get_response__(**response_data)
                return response
            app.http.get_broadcast_by_id = get_broadcast_by_id

            print(f"{Fore.MAGENTA}Broadcast Detected and fetching...")
            data_tweet["broadcast"] = [] 
            data_tweet["broadcast"].append({
                "url": tweet.broadcast.url,
                "id": tweet.broadcast.id,
                "title": tweet.broadcast.title,
                "state": tweet.broadcast.state,
                "source": tweet.broadcast.source,
                "username": tweet.broadcast.username,
                "display_name": tweet.broadcast.broadcaster_name,
                "width": tweet.broadcast.width,
                "height": tweet.broadcast.height
            })

            print(f"{Fore.MAGENTA}Found Broadcast...{Fore.WHITE}")
            broadcast = await tweet.broadcast.get_stream_link()
            broadcast_id = broadcast.share_url.split("/")[-1]

            broadcast_info = await app.http.get_broadcast_by_id(app.http, broadcast_id)
            data_tweet["broadcast"][-1]["view_count"] = broadcast_info["data"]["broadcast"]["total_watched"]
            data_tweet["broadcast"][-1]["live_count"] = broadcast_info["data"]["broadcast"]["total_watching"]
            data_tweet["broadcast"][-1]["replay_count"] = broadcast_info["data"]["broadcast"]["total_watched"] - broadcast_info["data"]["broadcast"]["total_watching"]

            base_url =  "https://" + broadcast.direct_url.split("/")[2]
            resolutions = requests.get(broadcast.direct_url)
            resolutions = resolutions.text
            resolutions = resolutions.split("\n")

            resolution_links = {}
            resolution_types = []
            for i in range(len(resolutions)):
                if "RESOLUTION" in resolutions[i]:
                    resolution = resolutions[i].split("RESOLUTION")[1].split(",")[0][1:]
                    resolution_links[resolution] = resolutions[i + 1]
                    resolution_types.append(resolution)
            broadcastResolutionValidation = True
            if cfg["BroadcastsResolution"].lower() != "all" and cfg["BroadcastsResolution"].lower() not in resolution_types:
                broadcastResolutionValidation = False
                print(f"{Fore.RED}Invalid Resolution Type Provided: {Fore.YELLOW}{cfg['BroadcastsResolution']}{Fore.RED}...{Fore.WHITE}")
                print(f"{Fore.RED}Valid Resolution Types are: {Fore.YELLOW}{Fore.WHITE}")
                print(f"{Fore.YELLOW}  - all{Fore.WHITE}")
                for res in resolution_types:
                    print(f"{Fore.YELLOW}  - {res}{Fore.WHITE}")
            

            if cfg["BroadcastsResolution"].lower() != "all" and cfg["BroadcastsResolution"].lower() in resolution_types:
                # remove all the other resolutions from the list
                resolution_types = [cfg["BroadcastsResolution"].lower()]

            if broadcastResolutionValidation == True:
                data_tweet["broadcast"][-1]["files"] = []
                for res_type in resolution_types:
                    # check if the video exists already
                    print(f"{Fore.MAGENTA}Downloading Broadcast Video...{Fore.WHITE}")
                    chunk_url = base_url + resolution_links[res_type]
                    transcript = requests.get(chunk_url)
                    # get the text from the transcript
                    transcript_text = transcript.text
                    # find all the chunck_*_a.aac files in the text
                    chunk_files = re.findall("chunk_(.*)_a\.ts", transcript_text)
                    # add chunc_ and _a.aac to the files
                    
                    chunk_files = [f"chunk_{file}_a.ts" for file in chunk_files]

                    chunk_url = chunk_url.replace(chunk_url.split("/")[-1], "")

                    chunks_dir = path_name + "media" + os.sep + current_id + os.sep + "chunks_download_" + res_type 
                    if not os.path.exists(chunks_dir):
                        if os.path.exists(path_name + "media" + os.sep + current_id + os.sep + f"{tweet.broadcast.id}_{res_type}.mp4"):
                            print(f"{Fore.BLUE}Found Broadcast Video: {Fore.YELLOW}{tweet.broadcast.id}_{res_type}.mp4{Fore.BLUE}...{Fore.WHITE}")
                            data_tweet["broadcast"][-1]["files"].append({
                                "file_name": f"{tweet.broadcast.id}_{res_type}.mp4",
                                "resolution": res_type
                            })
                            continue
                        os.makedirs(chunks_dir)
                    else:
                        # check how many files are in the folder
                        files = os.listdir(chunks_dir)
                        if len(files) != len(chunk_files):
                            # clear the files in the folder to prevent corrupted files
                            for file in files:
                                os.remove(chunks_dir + os.sep + file)
                        if os.path.exists(path_name + "media" + os.sep + current_id + os.sep + f"{tweet.broadcast.id}_{res_type}.mp4"):
                            # remove the video file 
                            os.remove(path_name + "media" + os.sep + current_id + os.sep + f"{tweet.broadcast.id}_{res_type}.mp4")
                        
                    result = await async_download_media(media_url=chunk_url, files=chunk_files, output_path=chunks_dir, max_concurrent=15)

                    if result == True:
                        print(f"{Fore.MAGENTA}Downloaded Broadcast Video...{Fore.WHITE}")
                        # print(chunk_files)
                        chunk_files = [f"{chunks_dir}{os.sep}{file}" for file in chunk_files]
                        # convert the chunks to mp4
                        print(f"{Fore.MAGENTA}Converting {Fore.YELLOW}{len(chunk_files)} {Fore.MAGENTA}chunks to mp4...{Fore.WHITE}")
                        convert_success = combine_ts_files_to_mp4(
                            chunk_files,
                            f"{path_name}media{os.sep}{current_id}{os.sep}{tweet.broadcast.id}_{res_type}.mp4"
                        )

                        if convert_success == False:
                            print(f"{Fore.RED}Failed to convert audio chunks to mp4{Fore.WHITE}")
                        else:
                            print(f"{Fore.MAGENTA}Converted {Fore.YELLOW}{len(chunk_files)} {Fore.MAGENTA}chunks to mp4...{Fore.WHITE}")
                            # delete the chunks
                            for chunk_file in chunk_files:
                                os.remove(chunk_file)
                            # delete the chunks_download folder
                            shutil.rmtree(path_name + "media" + os.sep + current_id + os.sep + f"chunks_download_{res_type}")
                        del chunk_url
                        del chunk_files
                        del transcript
                        del transcript_text
                        data_tweet["broadcast"][-1]["files"].append({
                            "file_name": f"{tweet.broadcast.id}_{res_type}.mp4",
                            "resolution": res_type
                        })
                
    # I would like to add stats, but that looks impossible currently   

    if cfg["GrabGrok"] == True:
        if tweet.grok_share != None:
            
            def get_grok_conversation_by_uid(self, uid, cursor=None):
                variables = {'grok_share_id': uid}
                featuers = { 'articles_preview_enabled': True,
                'c9s_tweet_anatomy_moderator_badge_enabled': True,
                'communities_web_enable_tweet_community_results_fetch': True,
                'creator_subscriptions_quote_tweet_preview_enabled': False,
                'creator_subscriptions_tweet_preview_api_enabled': True,
                'freedom_of_speech_not_reach_fetch_enabled': True,
                'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
                'longform_notetweets_consumption_enabled': True,
                'longform_notetweets_inline_media_enabled': True,
                'longform_notetweets_rich_text_read_enabled': True,
                'premium_content_api_read_enabled': False,
                'profile_label_improvements_pcf_label_in_post_enabled': True,
                'responsive_web_edit_tweet_api_enabled': True,
                'responsive_web_enhance_cards_enabled': False,
                'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                'responsive_web_graphql_timeline_navigation_enabled': True,
                'responsive_web_grok_analysis_button_from_backend': True,
                'responsive_web_grok_analyze_button_fetch_trends_enabled': False,
                'responsive_web_grok_analyze_post_followups_enabled': True,
                'responsive_web_grok_image_annotation_enabled': True,
                'responsive_web_grok_share_attachment_enabled': True,
                'responsive_web_grok_show_grok_translated_post': False,
                'responsive_web_jetfuel_frame': False,
                'responsive_web_twitter_article_tweet_consumption_enabled': True,
                'rweb_tipjar_consumption_enabled': True,
                'standardized_nudges_misinfo': True,
                'tweet_awards_web_tipping_enabled': False,
                'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
                'verified_phone_label_enabled': False,
                'view_counts_everywhere_api_enabled': True}
                if cursor:
                    variables["cursor"] = cursor
                params = {'variables':str(json.dumps(variables, separators=(",", ":"))), 
                          'features': str(json.dumps(featuers, separators=(",", ":")))}
                return {'headers': {},'method':"GET", 'url': "https://x.com/i/api/graphql/Ishd84Zga7NEhblatALH6A/GrokShare",'params': params}
            app.http._builder.get_grok_conversation_by_uid =  get_grok_conversation_by_uid

            async def get_grok_conversation_by_uid(self, uid, cursor=None):
                request_data = self._builder.get_grok_conversation_by_uid(self._builder, uid, cursor)
                # convert response_data from tuple to a mapping
                response = await self.__get_response__(**request_data)
                return response
            app.http.get_grok_conversation_by_uid = get_grok_conversation_by_uid


           
            data_tweet["grok_share"] = []
            data_tweet["grok_share"].append({
                "id": tweet.grok_share.id,
                "messages": []
            }) 
            cursor = None
            try:
                # grok_response = await app.http.get_grok_conversation_by_id(tweet.id, cursor=cursor)
                grok_response = await app.http.get_grok_conversation_by_uid(app.http, tweet.grok_share.id, cursor=None)
                messages = grok_response["data"]["grokShare"]["items"]
                for message in messages:
                    data_tweet["grok_share"][-1]["messages"].append({
                        "message" : message["message"],
                        "sender": message["sender"]
                    })
                    if "file_attachments" in message:
                        data_tweet["grok_share"][-1]["messages"][-1]["file_attachments"] = []
                        for file in message["file_attachments"]:
                            data_tweet["grok_share"][-1]["messages"][-1]["file_attachments"].append({
                                "type": file["mime_type"],
                                "url": file["url"]
                            })
                            if cfg["GrabMedia"] == True:
                                print(f"{Fore.MAGENTA}Downloading Grok Share Media...{Fore.WHITE}")
                                file_name = await download_media(file["url"], modify_download, verbose=True)
                                shutil.copyfile(base_path + file_name, path_name + "media" + os.sep + current_id + os.sep + file_name)
                                os.remove(base_path + file_name)
                                data_tweet["grok_share"][-1]["messages"][-1]["file_attachments"][-1]["file_name"] = file_name
                    if "web_results" in message:
                        print(f"{Fore.MAGENTA}Found Web Results...{Fore.WHITE}")
                        data_tweet["grok_share"][-1]["messages"][-1]["web_results"] = []
                        for web_result in message["web_results"]:
                            data_tweet["grok_share"][-1]["messages"][-1]["web_results"].append({
                                "title": web_result.get("title", None),
                                "url": web_result.get("url", None),
                                "snippet": web_result.get("snippet", None),
                                "language": web_result.get("language", None),
                                "favicon": web_result.get("favicon", None),
                                "favicon_base64": web_result.get("favicon_base64", None)
                            })
                    if "cited_web_results" in message:
                        print(f"{Fore.MAGENTA}Found Cited Web Results...{Fore.WHITE}")
                        data_tweet["grok_share"][-1]["messages"][-1]["cited_web_results"] = []
                        for cited_web_result in message["cited_web_results"]:
                            data_tweet["grok_share"][-1]["messages"][-1]["cited_web_results"].append({
                                "title": cited_web_result.get("title", None),
                                "url": cited_web_result.get("url", None),
                                "snippet": cited_web_result.get("snippet", None),
                                "language": cited_web_result.get("language", None),
                                "favicon": cited_web_result.get("favicon", None),
                                "favicon_base64": cited_web_result.get("favicon_base64", None)
                            })
                    if "post_ids_results" in message:
                        print(f"{Fore.MAGENTA}Found Grok Users refrenced...{Fore.WHITE}")
                        data_tweet["grok_share"][-1]["messages"][-1]["post_id_results"] = []
                        for post_id in message["post_ids_results"]:
                            try:
                                post = await app.tweet_detail(post_id["result"]['rest_id'])
                                print(f"{Fore.MAGENTA}Found Grok Share Post...{Fore.WHITE}")
                                post_data = await modify_tweet(post, True, parent_id=parent_id, path_name=path_name, app=app, debug=debug)
                                if post_data != None:   
                                    data_tweet["grok_share"][-1]["messages"][-1]["post_id_results"].append(post_data)
                            except Exception as e:
                                print(f"{Fore.RED}Failed to Scrape Grok Share Post for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                                if debug:
                                    # loop through the traceback and print all the lines
                                    print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                                    exc_type, exc_value, exc_traceback = sys.exc_info()

                                    # Format the traceback
                                    traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                                    # Print the formatted traceback
                                    print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                                    for line in traceback_details:
                                        print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                                    
                                if "Rate limit exceeded" in str(e):
                                    print(f"{Fore.RED}Rate limit exceeded...{Fore.WHITE}")
                                    exit()


            except Exception as e:
                print(f"{Fore.RED}Failed to Scrape Grok Share for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if debug:
                    # loop through the traceback and print all the lines
                    print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                    exc_type, exc_value, exc_traceback = sys.exc_info()

                    # Format the traceback
                    traceback_details = traceback.format_exception(exc_type, exc_value, exc_traceback)

                    # Print the formatted traceback
                    print(f"{Fore.RED}An error occurred:{Fore.WHITE}")
                    for line in traceback_details:
                        print(f"{Fore.YELLOW}{line}{Fore.WHITE}", end='')
                if "Rate limit exceeded" in str(e):
                    print(f"{Fore.RED}Rate limit exceeded...{Fore.WHITE}")
                    exit()

    if subtweet == False:
        # Saves the file in the folder in scraped/USER/media/TWEET_ID/TWEET_ID.json
        f = open(path_name + "media" + os.sep + tweet.id + os.sep + tweet.id + ".json", "w")
        f.write(json.dumps(data_tweet, indent=4))
        f.close()
        return parsed_ids
    return data_tweet




# function used to fetch the target username of who isbeing scraped
async def fetch_username():
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


# Function used to confirm messages
async def confirm_data(msg =""):

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

  

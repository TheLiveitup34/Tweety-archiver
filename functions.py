import re
import json
import time
import requests
import shutil
import os
from colorama import Fore
from configs import configurations


# Defines Paths for the app to use for path traversial
base_path = os.path.dirname(os.path.realpath(__file__)) + os.sep

parsed_ids = []



# This function does nothing but print a verbose information of the file being downloaded may have error displayed when running
async def modify_download(file_name, file_size,downloaded_in_bites):
    if file_size == downloaded_in_bites:
        print(f"{Fore.BLUE}Downloaded {Fore.YELLOW}{file_name} {Fore.MAGENTA}{file_size // 1024}{Fore.BLUE}Mb{Fore.BLUE} Successfully...{Fore.WHITE}\n")
    else:
        print(f"{Fore.BLUE}Downloading file {Fore.YELLOW}{file_name}  {Fore.MAGENTA}{downloaded_in_bites // 1024}{Fore.BLUE}Mb/{Fore.MAGENTA}{file_size//1024}{Fore.BLUE}Mb{Fore.WHITE}")
    return None

async def download_media(media_url, modify_download):
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
                await modify_download(os.path.basename(file_name), file_size, downloaded_in_bites)
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
        "has_newer_version": tweet.has_newer_version,
        "has_moderated_replies": tweet.has_moderated_replies,
        "is_sensitive": tweet.is_sensitive,
        "community_note": tweet.community_note,
        "is_quoted": tweet.is_quoted,
        "is_reply": tweet.is_reply,
        "tweet_raw": tweet.text
    }

    if "community" in tweet.__dict__:
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
                    for line in e.__traceback__.tb_frame.f_back:
                        print(f"{Fore.YELLOW}{line}")
            if actual_url == None:
                continue
        
            data_tweet["href_links"].append(actual_url)
            tweet.text = tweet.text.replace(url, actual_url)
            print(f" - {Fore.BLUE}Fetched {Fore.YELLOW}{url} {Fore.BLUE}and found {Fore.YELLOW}{actual_url}\n{Fore.BLUE} - Replacing {Fore.YELLOW}{url}{Fore.BLUE} with found {Fore.YELLOW}{actual_url}{Fore.WHITE}")
        data_tweet["tweet_parsed"] = tweet.text

    if cfg["GrabMedia"] == True:
        data_tweet["media"] = []
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
                if "source_user" in media.__dict__ and media.source_user != None:
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
                        for line in e.__traceback__.tb_frame.f_back:
                            print(f"{Fore.YELLOW}{line}")
                    if "Rate limit exceeded" in str(e):
                        exit()
            else:
                print(f"{Fore.RED}Failed to Fetch Quote Tweet due to Quoted Tweet Provided in None Value{Fore.WHITE}")


    # Checks if tweet is a subtweet and tries to download the tweet it subtweeted
    if cfg["GrabQuoteRetweets"] == True:
        if tweet.quote_counts > 0 and subtweet == False:
            data_tweet["tweets_quoting"] = []
            quoted_cursor = ""
            quotes = None
            while quoted_cursor != None:
                if quoted_cursor == "":
                    quoted_cursor = None


                try:
                    quotes = await app.get_tweet_quotes(tweet, cursor=quoted_cursor)
                    quoted_cursor = quotes.cursor
                except Exception as e:
                    print(f"{Fore.RED}Failed to Fetch Quoted Tweets of the main tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                    if debug:
                        # loop through the traceback and print all the lines
                        print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                        for line in e.__traceback__.tb_frame.f_back:
                            print(f"{Fore.YELLOW}{line}")
                    if "Rate limit exceeded" in str(e):
                        exit()
                if quotes == None:
                    quoted_cursor = None
                    continue
                for quote in quotes:
                    tweetquotes = await modify_tweet(quote, True, parent_id=parent_id, path_name=path_name, app=app, debug=debug) 
                    data_tweet["tweets_quoting"].append(tweetquotes)


    if cfg["GrabRetweetedBy"] == True:
        data_tweet["retweet_users"] = []
        # Checks if tweet has any retweets and tries to download the user list
        if tweet.retweet_counts > 0:
                
                # initaizes the loop to fetch all the users that retweeted the tweet
                retweets_cursor = ""
                while retweets_cursor != None:
                    if retweets_cursor == "":
                        retweets_cursor = None

                    try:
                        retweets = await app.get_tweet_retweets(tweet, cursor=retweets_cursor)
                        retweets_cursor = retweets.cursor
                    except Exception as e:
                        print(f"{Fore.RED}Failed to Fetch Retweet User List of the main tweet for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                        if debug:
                            # loop through the traceback and print all the lines
                            print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                            for line in e.__traceback__.tb_frame.f_back:
                                print(f"{Fore.YELLOW}{line}")
                        if "Rate limit exceeded" in str(e):
                            exit()
                    if len(retweets) == 0:
                        retweets_cursor = None
                        continue
                    for retweet in retweets:
                        data_tweet["retweet_users"].append({
                            "username": retweet.username,
                            "display": retweet.name,
                            "verified": retweet.verified,
                            "protected": retweet.protected,
                            "parody": retweet.is_parody_account,
                            "automated": retweet.is_automated
                        })


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
                        for line in e.__traceback__.tb_frame.f_back:
                            print(f"{Fore.YELLOW}{line}")
                if "Rate limit exceeded" in str(e):
                    exit()

    if cfg["GrabPolls"] == True:
    # Checks if tweet Poll exists in tweet
        if tweet.pool != None:
            data_tweet["poll_data"] = {}
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
    
    if cfg["GrabReplies"] == True:   

        if tweet.reply_counts > 0:
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
                        for line in e.__traceback__.tb_frame.f_back:
                            print(f"{Fore.YELLOW}{line}")
                    if "Rate limit exceeded" in str(e):
                        exit()
                    continue
                if len(comments) == 0:
                    comment_cursor = None
                    continue
                for comment in comments:
                    for tweetComment in comment.tweets:
                        try:
                            tweet_comment_data = await modify_tweet(tweetComment, True, parent_id=parent_id, path_name=path_name, app=app, debug=debug)
                            if tweet_comment_data != None:
                                data_tweet["comments"].append(tweet_comment_data)
                        except Exception as e:
                            print(f"{Fore.RED}Failed to Scrape Comment or data for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                            if debug:
                                # loop through the traceback and print all the lines
                                print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                                for line in e.__traceback__.tb_frame.f_back:
                                    print(f"{Fore.YELLOW}{line}")
                            if "Rate limit exceeded" in str(e):
                                exit()
            
    if cfg["GrabEditHistory"] == True:   
        if tweet.edit_control != None:
            if len(tweet.edit_control.tweet_ids) > 1:
                data_tweet["edit_history"] = [] 
                edits = await app.tweet_edit_history(tweet.id)
                for edit in edits:
                    try:
                        edithistory = await modify_tweet(edit, True, parent_id=parent_id, path_name=path_name, app=app, debug=debug)
                        if edithistory != None:
                            data_tweet["edit_history"].append(edithistory)
                    except Exception as e:
                        print(f"{Fore.RED}Failed to Scrape Comment or data for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                        if debug:
                            # loop through the traceback and print all the lines
                            print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                            for line in e.__traceback__.tb_frame.f_back:
                                print(f"{Fore.YELLOW}{line}")
                        if "Rate limit exceeded" in str(e):
                            exit()
    
    if cfg["GrabAudioSpace"] == True:
        # add check here
        data_tweet["audio_space"] = []
        audioid = tweet.audio_space_id
        try:
            audiosound = await app.get_audio_space(audioid)
            print(audiosound)
            if audiosound != None:
                for audio in audiosound:
                    data_tweet["audio_space"].append({
                    }) #I wasn't sure of the data to put here, tried audio.id and audio.AudioSpace.id. w/o proper docs, I couldn't get this to work.
        except Exception as e:
            print(f"{Fore.RED}Failed to Scrape Audio Spaces for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
            if debug:
                # loop through the traceback and print all the lines
                print(f"{Fore.RED}Traceback:{Fore.WHITE}")
                for line in e.__traceback__.tb_frame.f_back:
                    print(f"{Fore.YELLOW}{line}")
            if "Rate limit exceeded" in str(e):
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

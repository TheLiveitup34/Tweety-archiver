#  This file is to run the main application making Tweety Easy to use 
#  This allows scraping via twitter/x Search
#  @Author TheLiveitup34
# 

import os
import time
from functions import modify_tweet
from tweety import Twitter
from tweety.filters import SearchFilters
from colorama import Fore

# Defines Paths for the app to use for path traversial
base_path = os.path.dirname(os.path.realpath(__file__)) + os.sep
path_name = os.path.dirname(os.path.realpath(__file__)) + os.sep + "scraped"

# Checks if base path is made and set
if not os.path.exists(path_name):
    os.makedirs(path_name)

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
    parsed_id_data = []
    parsed_ids = []
    # Reset Search Strings and parsed_id_data
    search_string = "(from:" + user + ")"
    os.system("clear")
    if os.path.exists(path_name + 'parsed_id_data.txt'):
        f = open(path_name + 'parsed_id_data.txt', "r")
        parsed_id_data = f.read().split("\n")
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
                temp = modify_tweet(app.tweet_detail(manual), path_name=path_name, parsed_id_data=parsed_id_data)
                if temp != None:
                    for ids in temp:
                        if ids not in parsed_id_data:
                            parsed_id_data.append(ids)
                    f = open(path_name + 'parsed_id_data.txt', "w")
                    f.write("\n".join(parsed_id_data))
                    f.close()
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
                temp = modify_tweet(tweet, path_name=path_name, parsed_id_data=parsed_id_data)
                if temp != None:
                    for ids in temp:
                        if ids not in parsed_id_data:
                            parsed_id_data.append(ids)
                    # Updates the parsed_id_data 
                    f = open(path_name + 'parsed_id_data.txt', "w")
                    f.write("\n".join(parsed_id_data))
                    f.close()
            except Exception as e:
                print(f"{Fore.RED}Failed to Modify searched Tweet id:{Fore.YELLOW}{tweet.id}{Fore.RED}, for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "Rate limit exceeded" in str(e):
                    exit()
          

    # End of loop for While True: and allows to read data or observe anything 
    input("\n\nPress Enter to Continue...")

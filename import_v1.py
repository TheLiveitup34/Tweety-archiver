#  This file was created to import a v1 cache of assets for clubpenguin at (https://ia601606.us.archive.org/view_archive.php?archive=/13/items/club-penguin-twitter-account/clubpenguin.zip)
#  Purpose of this file is to check if the tweet has been archived/scraped then store it else fix the images not represented in file
#  @Author TheLiveitup34
# 

import os
import json
import shutil
from tweety import Twitter
from colorama import Fore
from functions import modify_tweet


def main():
    # Defines Paths for the app to use for path traversial
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



    # Gets all the files in the v1 folder of all v1 cached Data and loops through them
    files = os.listdir(v1_path)
    for file in files:

        # Fetches all previously fetched data
        parsed_id_data = []
        if os.path.exists(path_name + 'parsed_id_data.txt'):
            f = open(path_name + 'parsed_id_data.txt', "r")
            parsed_id_data = f.read().split("\n")
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
                temp =  modify_tweet(app.tweet_detail(data["tweet_id"]), path_name=path_name, parsed_id_data=parsed_id_data, app=app)
                if temp != None:
                    for ids in temp:
                        if ids not in parsed_id_data:
                            parsed_id_data.append(ids)
                    f = open(path_name + 'parsed_id_data.txt', "w")
                    f.write("\n".join(parsed_id_data))
                    f.close()
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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Detected User Keyboard Interuption Ending Program..")
#  This file is to run the main application making Tweety Easy to use 
#  This allows scraping via twitter/x Search
#  @Author TheLiveitup34
# 

import os
import time
import sys
import asyncio
import traceback
from http_mixin import inject_functions_to_api
from colorama import Fore
from tweety import TwitterAsync
from tweety.filters import SearchFilters
from functions import modify_tweet, fetch_username, confirm_data

DEBUG_LOGGING = True

async def main():
    # Defines Paths for the app to use for path traversial
    base_path = os.path.dirname(os.path.realpath(__file__)) + os.sep
    path_name = os.path.dirname(os.path.realpath(__file__)) + os.sep + "scraped"



    # Checks if base path is made and set
    if not os.path.exists(path_name):
        os.makedirs(path_name)
    login_type = False
    app = TwitterAsync("session")
    # check if there is a .env file and if not create one
    if not os.path.exists(path_name + os.sep + "session.tw_session"):
        if not os.path.exists(base_path + ".env"):
            print(f"{Fore.RED}No .env file detected, please update your credentials either Auth_Token or Credentials in the .env file{Fore.WHITE}")
            # make a .env file with the following format
            # TWITTER_USERNAME=your_username
            # TWITTER_PASSWORD=your_password
            f = open(base_path + ".env", "w")
            f.write("TWITTER_USERNAME=your_username\n")
            f.write("TWITTER_PASSWORD=your_password\n")
            f.write("TWITTER_AUTH_TOKEN=your_auth_token\n")
            
            f.close()
            exit()
        else:
            # check if the .env file is empty
            f = open(base_path + ".env", "r")
            lines = f.readlines()
            f.close()
            if len(lines) == 0:
                print(f"{Fore.RED}No credentials found in .env file, please update your credentials in the .env file{Fore.WHITE}")
                exit()
            else:
                # check if the .env file has the correct format
                if len(lines) != 3:
                    print(f"{Fore.RED}Invalid .env file format, please update your credentials in the .env file{Fore.WHITE}")
                    exit()
                else:
                    # check if the .env file has the correct keys
                    if lines[0].split("=")[0] != "TWITTER_USERNAME" or lines[1].split("=")[0] != "TWITTER_PASSWORD" or lines[2].split("=")[0] != "TWITTER_AUTH_TOKEN":
                        print(f"{Fore.RED}Invalid .env file format, please update your credentials in the .env file{Fore.WHITE}")
                        exit()
                    else:
                        username = lines[0].split("=")[1].strip()
                        password = lines[1].split("=")[1].strip()
                        auth_token = lines[2].split("=")[1].strip()

                        # check if username and password and or auth_token is empty
                        if username == "" or password == "" or auth_token == "":
                            print(f"{Fore.RED}No credentials found in .env file, please update your credentials in the .env file{Fore.WHITE}")
                            exit()
                        # check if the .env file has the correct values
                        if username == "your_username" and password == "your_password" and auth_token == "your_auth_token":
                            print(f"{Fore.RED}Default .env file detected please update your credentials...{Fore.WHITE}")
                            exit()
                        else:
                            if username != "your_username" and password != "your_password" and auth_token == "your_auth_token":
                                login_type = True
                                print(f"{Fore.YELLOW}Detected Credentials, Attempting to login...{Fore.WHITE}")
                            elif username == "your_username" and password == "your_password" and auth_token != "your_auth_token":
                                print(f"{Fore.YELLOW}Detected Auth Token, Attempting to login...{Fore.WHITE}")
                            elif username != "your_username" and password != "your_password" and auth_token != "your_auth_token":
                                print(f"{Fore.YELLOW}Detected Credentials and Auth Token, Attempting to login...{Fore.WHITE}")
                                login_type = True
                            else:
                                print(f"{Fore.RED}Invalid .env file format, please update your credentials in the .env file{Fore.WHITE}")
                                exit()
                
   
    # Start calling to allow you to login Dynamicly Session is saved
    
        if login_type == True:
            try:
                await app.sign_in(username, password)
            except Exception as e:
                print(f"{Fore.RED}Failed to login for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if "actionrequired" in str(e).lower() or "check your email" in str(e).lower() or "enter your" in str(e).lower():
                    action = input(f"{Fore.RED}Action Required:{Fore.YELLOW} {str(e.message)}: ")
                    await app.sign_in(username, password, extra=action)
                if DEBUG_LOGGING:
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
            await app.load_auth_token(auth_token)
    else:
        print(f"{Fore.YELLOW}Detected Session, Attempting to login...{Fore.WHITE}")
        await app.connect()
     # Injects functions to the app to allow for more functionality
    print(f"{Fore.YELLOW}Injecting More Api Requests to Tweety...{Fore.WHITE}")    
    app = inject_functions_to_api(app)

    function_names = ["get_grok_conversation_by_uid", "get_broadcast_by_id"]
    failed_functions_count = 0
    for function_name in function_names:
        if hasattr(app.http, function_name):
            print(f"{Fore.GREEN}Successfully injected {function_name} into Tweety{Fore.WHITE}")
        else:
            print(f"{Fore.RED}Failed to inject {function_name} into Tweety{Fore.WHITE}")
            failed_functions_count += 1
        # check if the function is avliable in app.http._builder
        if hasattr(app.http._builder, function_name):
            print(f"{Fore.GREEN}Successfully injected {function_name} into Tweety's _builder{Fore.WHITE}")
        else:
            print(f"{Fore.RED}Failed to inject {function_name} into Tweety's _builder{Fore.WHITE}")
            failed_functions_count += 1
    # If any functions failed to inject, exit the program
    if failed_functions_count > 0:
        print(f"{Fore.RED}Failed to inject {failed_functions_count} functions into Tweety{Fore.WHITE}")
        print(f"{Fore.RED}Please report this issue to the developer{Fore.WHITE}")
        exit()
    print(f"{Fore.GREEN}Successfully injected all functions into Tweety{Fore.WHITE}")
    
    # Start of username validation Loop
    username_valid = False
    user = ""

    while username_valid == False:
        os.system("clear")
        if os.path.exists(path_name + os.sep + "last_used_username.txt"):
            f = open(path_name + os.sep + "last_used_username.txt", "r")
            user = f.read().strip().replace(" ", "")
            f.close()
            print(f"{Fore.MAGENTA}We have detected you used the username: {Fore.YELLOW}{user}{Fore.WHITE}")
            username_valid = await confirm_data(f"Would you still like to use this username?")
            if username_valid == False:
                os.remove(path_name + os.sep + "last_used_username.txt")
        else:
            user = await fetch_username()

            username_valid = await confirm_data(f"You have entered '{Fore.YELLOW}{user}{Fore.WHITE}' is that correct?")
            if username_valid == True:
                f = open(path_name + os.sep + "last_used_username.txt", "w")
                f.write(user)
                f.close()

    # Starts forming search stream
    search_string = "(from:" + user + ")"

    # Sets path to scraped/USERNAME and makes folder
    path_name += os.sep + user
    if not os.path.exists(path_name):
        os.makedirs(path_name)
    path_name += os.sep



    # Start Scrape loop 
    fetched_manual = False

    while True:
        parsed_id_data = []
        # Reset Search Strings and parsed_id_data
        search_string = "(from:" + user + ")"
        os.system("clear")
        if os.path.exists(path_name + 'parsed_id_data.txt') and DEBUG_LOGGING == False:
            f = open(path_name + 'parsed_id_data.txt', "r")
            parsed_id_data = f.read().split("\n")
            f.close()

        # Get until input if wanted
        until_validated = False
        while until_validated == False:
            os.system('clear')
            until = input(f"{Fore.MAGENTA}Enter Until date (YYYY-MM-DD) ({Fore.YELLOW}leave empty if you dont want until{Fore.MAGENTA}):{Fore.WHITE} ")
            if until != "":
                until_validated = await confirm_data(f"You have Entered '{Fore.YELLOW}{until}{Fore.WHITE}' is this correct?")
            else:
                until_validated = await confirm_data(f"You have entered {Fore.YELLOW}NOTHING{Fore.WHITE} is that correct?")

            if until_validated:
                if until != "":
                    search_string += f" until:{until}"
                    print(f"Added Until {until} to search")
                else:
                    print("No Until Entered Continuing...\n")
                time.sleep(2)

        since_validated = False
        while since_validated == False:
            os.system("clear")
            # Get Since input if wanted
            since = input(f"{Fore.MAGENTA}Enter Since date (YYYY-MM-DD) ({Fore.YELLOW}leave empty if you dont want since{Fore.MAGENTA}):{Fore.WHITE} ")

            if since != "":
                since_validated = await confirm_data(f"You have Entered '{Fore.YELLOW}{until}{Fore.WHITE}' is this correct?")
            else:
                since_validated = await confirm_data(f"You have entered {Fore.YELLOW}NOTHING{Fore.WHITE} is that correct?")

            if since_validated == True:
                if since != "":
                    search_string += f" since:{since}"
                    print(f"Added Since {until} to search")
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
                    temp2 = await app.tweet_detail(manual)
                    temp = await modify_tweet(temp2, path_name=path_name, parsed_id_data=parsed_id_data, app=app, debug=DEBUG_LOGGING)
                    if temp != None:
                        for ids in temp:
                            if ids not in parsed_id_data:
                                parsed_id_data.append(ids)
                        if DEBUG_LOGGING == False:
                            f = open(path_name + 'parsed_id_data.txt', "w")
                            f.write("\n".join(parsed_id_data))
                            f.close()
                except Exception as e:
                    print(f"{Fore.RED}Failed to Modify manual Tweet id:{Fore.YELLOW}{manual}{Fore.RED}, for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                    if DEBUG_LOGGING:
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


        # Starts Search loop for twitter searches to navigate pages
        print("Fetching Twitter Search...")
        cursor = ""
        while cursor != None:
            if cursor == "":
                cursor = None
            # Attempts to do twitter search
            try:
                tweets = await app.search(search_string, filter_=SearchFilters.Latest(), cursor=cursor)
            except Exception as e:
                print(f"Search was {search_string}")
                print(f"{Fore.RED}Twitter Search failed for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                if DEBUG_LOGGING:
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
                    temp = await modify_tweet(tweet, path_name=path_name, parsed_id_data=parsed_id_data, app=app, debug=DEBUG_LOGGING)
                    if temp != None:
                        for ids in temp:
                            if ids not in parsed_id_data:
                                parsed_id_data.append(ids)
                        # Updates the parsed_id_data 
                        if DEBUG_LOGGING == False:
                            f = open(path_name + 'parsed_id_data.txt', "w")
                            f.write("\n".join(parsed_id_data))
                            f.close()
                except Exception as e:
                    print(f"{Fore.RED}Failed to Modify searched Tweet id:{Fore.YELLOW}{tweet.id}{Fore.RED}, for the following reason: {Fore.YELLOW}{e}{Fore.WHITE}")
                    if DEBUG_LOGGING:
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
            

        # End of loop for While True: and allows to read data or observe anything 
        input("\n\nPress Enter to Continue...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Detected User Keyboard Interuption Ending Program..")

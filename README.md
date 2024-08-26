
# Tweety Archiver

A tool built on the github repo [Tweety](https://github.com/mahrtayyab/tweety) and is a requirment to run and operate this tool

## To use the tool First install Tweety with the following from tweety instalation steps



## Installation: 
```bash
pip install tweety-ns
```

## Keep synced with latest fixes

##### **Pip might not be always updated , so to keep everything synced.**

```bash
pip install https://github.com/mahrtayyab/tweety/archive/main.zip --upgrade 
```

## Then download and install the repo

```bash
git clone https://github.com/TheLiveitup34/Tweety-archiver.git
```
Then change directory into Tweety-Archiver

```bash
cd Tweety-archiver/
```

Install the requirements.txt

##### **Note if you dont have pip installed download pip via [Pip's Website](https://pypi.org/project/pip/)**
[https://pypi.org/project/pip/](https://pypi.org/project/pip/)

##### **This project also requires python to be installed via [Pythons website](https://www.python.org/downloads/)**
[https://www.python.org/downloads/](https://www.python.org/downloads/)

Note this was written in python version 3.10.12 and may not work in later versions depending if updates or tweety has a version break

```bash
pip install -r requirements.txt
```
##### **It may have a error when installing requirements.txt look at the information and attempt to pip install any missing packages. that it says to install**

## Now you can run Tweety archiver
```bash
python3 main.py
```

it will auto prompt to login to twitter and store a session this is part of Tweety.

Once you login then it will prompt for a username to start archiving.

This works as if your searching twitter and its using the format of 
```bash
(from:USERNAME) until:20XX-XX-XX since:20XX-XX-XX
``` 
This is dynamic and you will only have to enter the username when prompt then it will ask you if you want to use until or since these can be skipped by pressing enter

Once this is done it will loop through each search page till there are no more tweets or API Limit has been hit. if api limit hasn't been hit it will reprompt for until and since.

This will build a folder structure like the following
```bash
YOUR_DIR_PATH/Tweety-archiver/scraped/USER_SCRAPED/media
```
within the media folder will contain a folder labeled with the id of each tweet containing images/videos/gifs or any other media that will be auto downloaded and a .json file that contains the contents of the tweet before and after parsing and fetching the twitter shortners and other meta data you can explore


> [!IMPORTANT] 
> Please use this with caution and some of the bugs will not be from me and may be impart of tweety and uses with caution because your account may be set to read-only mode and or other issues read more on tweety and X/Twitters Terms to find out.

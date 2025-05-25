import asyncio
"""
This module contains the configuration for the Twitter bot.
It includes the following settings:
============================

    MAN CONFIGURATION
- GrabArticles: Whether to grab articles on twitter. (Note if you have GrabMedia Disabled, this will still download media for articles)
- ConvertLinks: Whether to convert links in tweets from the twitter url shortner to its main link.
- GrabMedia: Whether to grab media from tweets.(images, videos, gifs) Not the related to articles.
- GrabTweetQuoted: Whether to grab the tweet it quoted.
- GrabPolls: Whether to grab polls from tweets.
- GrabRetweetedBy: Whether to grab the users that retweeted the tweet.
- GrabRepliedToTweet: Whether to grab the tweet it replied to.
- GrabReplies: Whether to grab replies from tweets.
- GrabEditHistory: Whether to grab edit history from tweets.
- GrabHiddenReplies: Whether to grab hidden replies from tweets (Requires GrabReplies to be True).
- GrabQuoteRetweets: Whether to grab quote retweets from tweets.
- GrabProposedNotes: Whether to grab proposed community notes from tweets.
- GrabSpamReplies: Whether to grab spam replies from tweets (Requires GrabReplies to be True).
- GrabBroadcasts: Whether to grab broadcasts from tweets.
- BroadcastsResolution: The resolution of the broadcasts to grab. options (all, 1920x1080, 1280x720, 848x480, 568x320, 400x222)
    NOTE: If you do not see a resolution that is not on the list you can enter any text and it will tell you all the available resolutions.
- GrabAudioSpace: Whether to grab audio space from tweets.(This operation will take some time to complete as it has to convert multiple audio files to mp3 and combine them into one file)
- GrabLists: Whether to grab list data from tweets.
- GrabGrok: Whether to grab grok conversations from tweets.
- GrabCommunity: Whether to grab community data from tweets.

============================
This module is used to configure the bot's behavior and settings.

"""
async def configurations():
    return {
        "GrabArticles": False,
        "ConvertLinks": False,
        "GrabMedia": False,
        "GrabPolls": False,
        "GrabTweetQuoted": False,
        "GrabRetweetedBy": False,
        "GrabRepliedToTweet": False,
        "GrabReplies": False,
        "GrabEditHistory": False,
        "GrabHiddenReplies": False,
        "GrabQuoteRetweets": False,
        "GrabProposedNotes": False,
        "GrabSpamReplies": False,
        "GrabBroadcasts": False,
        "BroadcastsResolution": "all",
        "GrabAudioSpace": False,
        "GrabLists": False,
        "GrabGrok": False,
        "GrabCommunity": False
    }

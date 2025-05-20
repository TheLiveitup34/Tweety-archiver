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
- GrabProposedNotes: Whether to grab proposed notes from tweets.
- GrabSpamReplies: Whether to grab spam replies from tweets (Requires GrabReplies to be True).
- GrabBroadcasts: Whether to grab broadcasts from tweets.
- GrabAudioSpace: Whether to grab audio space from tweets.
- GrabLists: Whether to grab list data from tweets.

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
        "GrabAudioSpace": False,
        "GrabLists": False
    }

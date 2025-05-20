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
- GrabHiddenReplies: Whether to grab hidden replies from tweets.
- GrabQuoteRetweets: Whether to grab quote retweets from tweets.

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
        "GrabEditHistory": True,
        "GrabHiddenReplies": False,
        "GrabQuoteRetweets": False,
    }

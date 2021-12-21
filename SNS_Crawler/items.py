# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class NewsItem(scrapy.Item):
    title = scrapy.Field()
    body = scrapy.Field()
    date = scrapy.Field()
    keyword = scrapy.Field()
    newspaperId = scrapy.Field()
    url = scrapy.Field()
    md5 = scrapy.Field()
    def __repr__(self):
        return ''

class ImdbMovieItem(scrapy.Item):
    id = scrapy.Field()
    title = scrapy.Field()
    plot = scrapy.Field()
    storyline = scrapy.Field()

class ImdbReviewItem(scrapy.Item):
    review_id = scrapy.Field()
    movie_id = scrapy.Field()
    cmt_title = scrapy.Field()
    cmt_body = scrapy.Field()
    date = scrapy.Field()
    rate = scrapy.Field()

class YoutubeChannelItem(scrapy.Item) :
    id = scrapy.Field()
    title = scrapy.Field()
    desc = scrapy.Field()
    view = scrapy.Field()
    subs = scrapy.Field()
    video = scrapy.Field()
    def __repr__(self):
        return ''

class YoutubeVideoItem(scrapy.Item) :
    id = scrapy.Field()
    channelId = scrapy.Field()
    title = scrapy.Field()
    desc = scrapy.Field()
    date = scrapy.Field()
    view = scrapy.Field()
    like = scrapy.Field()
    dislike = scrapy.Field()
    def __repr__(self):
        return ''

class YoutubeCommentItem(scrapy.Item):
    commentId = scrapy.Field()
    channelId = scrapy.Field()
    videoId   = scrapy.Field()
    body      = scrapy.Field()
    date      = scrapy.Field()
    lang      = scrapy.Field()
    def __repr__(self):
        return ''

class WebtoonItem(scrapy.Item) :
    id = scrapy.Field()
    subs = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    lang = scrapy.Field()   
    def __repr__(self):
        return ''

class WebtoonCommentItem(scrapy.Item):
    commentId = scrapy.Field()
    webtoonId = scrapy.Field()
    episodeNo = scrapy.Field()
    body = scrapy.Field()
    date = scrapy.Field()
    lang = scrapy.Field()
    country = scrapy.Field()
    def __repr__(self):
        return ''

class RedditItem(scrapy.Item):
    postId = scrapy.Field()
    title = scrapy.Field()
    body = scrapy.Field()
    date = scrapy.Field()
    subreddit = scrapy.Field()
    lang = scrapy.Field()
    comments = scrapy.Field()
    def __repr__(self):
        return ''

class TwitterItem(scrapy.Item):
    tweetId = scrapy.Field()
    userId = scrapy.Field()
    username = scrapy.Field()
    name = scrapy.Field()
    date = scrapy.Field()
    body = scrapy.Field()
    media_urls = scrapy.Field()

    lang = scrapy.Field()
    hashtags = scrapy.Field()
    mentions = scrapy.Field()
    tweet_links = scrapy.Field()

    retweeted_tweet = scrapy.Field()
    retweet_count = scrapy.Field()
    favorite_count = scrapy.Field()
    tweet_type = scrapy.Field()
    def __repr__(self):
        return ''

class TwitterGeoItem(scrapy.Item):
    tweetId = scrapy.Field()
    userId = scrapy.Field()
    username = scrapy.Field()
    name = scrapy.Field()
    date = scrapy.Field()
    body = scrapy.Field()
    geo = scrapy.Field()
    lang = scrapy.Field()
    keyword = scrapy.Field()

    hashtags = scrapy.Field()
    mentions = scrapy.Field()
    tweet_links = scrapy.Field()
    
    retweeted_tweet = scrapy.Field()
    tweet_type = scrapy.Field()
    def __repr__(self):
        return ''

class TwitterUserItem(scrapy.Item):
    tweetId = scrapy.Field()
    userId = scrapy.Field()
    username = scrapy.Field()
    name = scrapy.Field()
    date = scrapy.Field()
    body = scrapy.Field()
    geo = scrapy.Field()
    lang = scrapy.Field()
    hashtags = scrapy.Field()
    mentions = scrapy.Field()
    tweet_links = scrapy.Field()
    
    retweeted_tweet = scrapy.Field()
    tweet_type = scrapy.Field()
    def __repr__(self):
        return ''

class TwitterRTItem(scrapy.Item):
    rtId = scrapy.Field()
    bodyId = scrapy.Field()
    userId = scrapy.Field()
    username = scrapy.Field()
    name = scrapy.Field()
    date = scrapy.Field()
    body = scrapy.Field()
    geo = scrapy.Field()
    lang = scrapy.Field()
    hashtags = scrapy.Field()
    mentions = scrapy.Field()
    tweet_links = scrapy.Field()
    
    retweeted_tweet = scrapy.Field()
    tweet_type = scrapy.Field()
    def __repr__(self):
        return ''
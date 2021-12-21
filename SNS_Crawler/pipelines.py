# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from .apikey import *
from .items import *
import hashlib
import pymysql
import sys
import regex as re

emoji_filter = re.compile("["u"\U00010000-\U0010FFFF""]+", flags=re.UNICODE)
class NewsPipeline:
    def __init__(self) :
        try :
            self.crawlDB = pymysql.connect(
                user=SQL_USER,
                passwd=SQL_PW,
                host=SQL_HOST,
                port=SQL_PORT,
                db=SQL_DB
            )
            self.cursor = self.crawlDB.cursor()
        except :
            print('ERROR: DB connection failed')
            sys.exit(1)

    def process_item(self, item, spider):
        item['title'] = item['title'].replace('\n', ' ')
        item['title'] = item['title'].replace('"', ' ')
        item['title'] = item['title'].strip()
        item['body'] = item['body'].replace('\n', ' ')
        item['body'] = item['body'].replace('"', ' ')
        item['body'] = item['body'].strip()
        enc = hashlib.md5(item['title'].encode('utf-8'))
        enc.update(item['body'].encode('utf-8'))
        item['md5'] = enc.hexdigest()

        insert_sql = 'INSERT IGNORE INTO crawlDB.NewsArticle(body, date, keyword, newscompanyId, title, url, hash) VALUES(%s, %s, %s, %s, %s, %s, %s)'
        try :
            self.cursor.execute(
                insert_sql, 
                (
                    item['body'], 
                    item['date'], 
                    item['keyword'], 
                    item['newspaperId'], 
                    item['title'], 
                    item['url'],
                    item['md5']
                )
            )
            self.crawlDB.commit()
        except:
            sys.exit(1)
        return item

class RedditPipeline:
    def __init__(self):
        self.create_connection()

    def create_connection(self):
        try :
            self.crawlDB = pymysql.connect(
                user=SQL_USER,
                passwd=SQL_PW,
                host=SQL_HOST,
                port=SQL_PORT,
                db=SQL_DB
            )
            self.cursor = self.crawlDB.cursor(pymysql.cursors.DictCursor)
        except :
            print('ERROR: DB connection failed')
            sys.exit(1)

    def process_item(self, item, spider):
        self.store_in_db(item)
        return item

    def store_in_db(self, item) :
        item['body'][0] = emoji_filter.sub(r'', item['body'][0])
        select_sql = 'SELECT * from RedditPost where postId = %s'
        select_arg = [item['postId']]
        insert_sql = 'INSERT INTO RedditPost(postId, title, body, date, subreddit) VALUES(%s, %s, %s, %s, %s)'
        insert_arg = [item['postId'], item['title'], item['body'], item['date'], item['subreddit']]
        try :
            self.cursor.execute(select_sql, select_arg)
            rows = self.cursor.fetchall()
            if len(rows) == 1 :
                return item
        except Exception as e:
            print(e)
            print(select_sql, select_arg)
            pass
            #sys.exit(1)
        try :
            self.cursor.execute(insert_sql, insert_arg)
            self.crawlDB.commit()
        except Exception as e:
            print(e)
            print(insert_sql, insert_arg)
            pass
            #sys.exit(1)

        try :
            comments = item['comments']
            print(comments)
            for comment in comments :
                select_sql_2 = 'SELECT * from RedditComment where commentId = %s'
                select_arg_2 = [comment['commentId']]
                try :
                    self.cursor.execute(select_sql_2, select_arg_2)
                    rows = self.cursor.fetchall()
                    if len(rows) == 1 :
                        return item
                except Exception as e:
                    print(e)
                    print(select_sql_2, select_arg_2)
                    pass
                    #sys.exit(1)
                try : 
                    insert_sql_2 = 'INSERT INTO RedditComment(postId, commentId, body, date) VALUES(%s, %s, %s, %s)'
                    insert_arg_2 = [item['postId'], comment['commentId'], emoji_filter.sub(r'', comment['body']), comment['date']]
                    
                    self.cursor.execute(insert_sql_2, insert_arg_2)
                    self.crawlDB.commit()
                except Exception as e:
                    print(e)
                    print(insert_sql_2, insert_arg_2)
                    pass
                    #sys.exit(1)
        except Exception as e:
            print(e)
        self.crawlDB.commit()

class TwitterPipeline:
    def __init__(self):
        self.create_connection()

    def create_connection(self):
        try :
            self.crawlDB = pymysql.connect(
                user=SQL_USER,
                passwd=SQL_PW,
                host=SQL_HOST,
                port=SQL_PORT,
                db=SQL_DB
            )
            self.cursor = self.crawlDB.cursor(pymysql.cursors.DictCursor)
        except :
            print('ERROR: DB connection failed')
            sys.exit(1)

    def process_item(self, item, spider):
        self.store_in_db(item)
        return item

    def store_in_db(self, item) :
        TwitterUser = 'TwitterUser'
        TwitterTweet= 'TwitterTweet'
        TwitterMention = 'TwitterMention'
        TwitterHashtag= 'TwitterHashtag'

        select_sql = ''
        select_arg = []
        insert_sql = ''
        insert_arg = []
                
        if type(item) == TwitterRTItem:
            item['body'][0] = emoji_filter.sub(r'', item['body'][0])
            select_sql = 'SELECT * from TwitterRT where rtId = %s'
            select_arg = [item['rtId']]
            insert_sql = 'INSERT INTO TwitterRT(rtId, userId, bodyId, body, lang, geo) VALUES(%s, %s, %s, %s, %s, %s)'
            insert_arg = [item['rtId'], item['userId'], item['bodyId'], item['body'], item['lang'], item['geo']]
            try :
                self.cursor.execute(select_sql, select_arg)
                rows = self.cursor.fetchall()
                if len(rows) == 1 :
                    return item
            except Exception as e:
                print(e)
                print(select_sql, select_arg)
                # sys.exit(1)
                pass
            try :
                self.cursor.execute(insert_sql, insert_arg)
                self.crawlDB.commit()
            except Exception as e:
                print(e)
                print(insert_sql, insert_arg)
                # sys.exit(1)
                pass

        elif type(item) == TwitterUserItem:
            select_sql_2 = 'SELECT * from TwitterUser where userId = %s'
            select_arg_2 = [item['userId']]
            insert_sql_2 = 'INSERT INTO TwitterUser(userId, username, name) VALUES(%s, %s, %s)'
            insert_arg_2 = [item['userId'], item['username'], item['name']]

            try :
                self.cursor.execute(select_sql_2, select_arg_2)
                rows = self.cursor.fetchall()
            except Exception as e:
                print(e)
                print(select_sql_2, select_arg_2)
                pass
                #sys.exit(1)
            try :
                self.cursor.execute(insert_sql_2, insert_arg_2)
                self.crawlDB.commit()
            except Exception as e:
                print(e)
                print(insert_sql_2, insert_arg_2)
                pass
                #sys.exit(1)
                
            item['body'][0] = emoji_filter.sub(r'', item['body'][0])
            select_sql = 'SELECT * from TwitterTweet where tweetId = %s'
            select_arg = [item['tweetId']]
            insert_sql = 'INSERT INTO TwitterTweet(tweetId, userId, body, lang, geo) VALUES(%s, %s, %s, %s, %s)'
            insert_arg = [item['tweetId'], item['userId'], item['body'], item['lang'],item['geo']]

            try :
                self.cursor.execute(select_sql, select_arg)
                rows = self.cursor.fetchall()
                if len(rows) == 1 :
                    return item
            except Exception as e:
                print(e)
                print(select_sql, select_arg)
                pass
                #sys.exit(1)
            try :
                self.cursor.execute(insert_sql, insert_arg)
                self.crawlDB.commit()
            except Exception as e:
                print(e)
                print(insert_sql, insert_arg)
                pass
                #sys.exit(1)
            
        elif type(item) == TwitterGeoItem:
            select_sql_2 = 'SELECT * from TwitterUser where userId = %s'
            select_arg_2 = [item['userId']]
            insert_sql_2 = 'INSERT INTO TwitterUser(userId, username, name) VALUES(%s, %s, %s)'
            insert_arg_2 = [item['userId'], item['username'], item['name']]

            try :
                self.cursor.execute(select_sql_2, select_arg_2)
                rows = self.cursor.fetchall()
            except Exception as e:
                print(e)
                print(select_sql_2, select_arg_2)
                pass
                #sys.exit(1)
            try :
                self.cursor.execute(insert_sql_2, insert_arg_2)
                self.crawlDB.commit()
            except Exception as e:
                print(e)
                print(insert_sql_2, insert_arg_2)
                pass
                #sys.exit(1)

            item['body'][0] = emoji_filter.sub(r'', item['body'][0])
            select_sql = 'SELECT * from TwitterTweet where tweetId = %s'
            select_arg = [item['tweetId']]
            insert_sql = 'INSERT INTO TwitterTweet(tweetId, userId, body, lang, geo) VALUES(%s, %s, %s, %s, %s)'
            insert_arg = [item['tweetId'], item['userId'], item['body'], item['lang'], item['geo']]
            try :
                self.cursor.execute(select_sql, select_arg)
                rows = self.cursor.fetchall()
                if len(rows) == 1 :
                    return item
            except Exception as e:
                print(e)
                print(select_sql, select_arg)
                pass
                #sys.exit(1)
            try :
                self.cursor.execute(insert_sql, insert_arg)
                self.crawlDB.commit()
            except Exception as e:
                print(e)
                print(insert_sql, insert_arg)
                pass
                #sys.exit(1)
            
            insert_sql_3 = 'INSERT INTO TwitterKeyword(tweetId, keyword, date) VALUES(%s, %s, %s)'
            insert_arg_3 = [item['tweetId'], item['keyword'], item['date']]

            try :
                self.cursor.execute(insert_sql_3, insert_arg_3)
                self.crawlDB.commit()
            except Exception as e:
                print(e)
                print(insert_sql_3, insert_arg_3)
                pass
                #sys.exit(1)
        return item

class YoutubePipeline:
    def __init__(self) :
        try :
            self.crawlDB = pymysql.connect(
                user=SQL_USER,
                passwd=SQL_PW,
                host=SQL_HOST,
                port=SQL_PORT,
                db=SQL_DB
            )
            self.cursor = self.crawlDB.cursor()
        except :
            print('ERROR: DB connection failed')
            sys.exit(1)
        
    def process_item(self, item, spider):
        select_sql = ''
        select_arg = []
        insert_sql = ''
        insert_arg = []
        if type(item) == YoutubeCommentItem :
            item['body'] = emoji_filter.sub(r'', item['body'])
            select_sql = 'SELECT * from YoutubeComment where commentId = %s'
            select_arg = [item['commentId']]
            insert_sql = 'INSERT INTO YoutubeComment(commentId, videoId, body, date) VALUES(%s, %s, %s, %s)'
            insert_arg = [item['commentId'], item['videoId'], 
                          item['body'], item['date']]
        elif type(item) == YoutubeChannelItem :
            item['title'] = emoji_filter.sub(r'', item['title'])
            item['desc'] = emoji_filter.sub(r'', item['desc'])
            select_sql = 'SELECT * from YoutubeChannel where channelId = %s'
            select_arg = [item['id']]
            insert_sql = 'INSERT INTO YoutubeChannel(channelId, title, `desc`, viewCount, subscriberCount, videoCount) VALUES(%s, %s, %s, %s, %s, %s)'
            insert_arg = [item['id'], item['title'], item['desc'], 
                          item['view'], item['subs'], item['video']]
        elif type(item) == YoutubeVideoItem :
            item['title'] = emoji_filter.sub(r'', item['title'])
            item['desc'] = emoji_filter.sub(r'', item['desc'])
            select_sql = 'SELECT * from YoutubeVideo where videoId = %s'
            select_arg = [item['id']]
            insert_sql = 'INSERT INTO YoutubeVideo(videoId, channelId, title, viewCount, date, `desc`, likeCount) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
            insert_arg = [item['id'], item['channelId'], item['title'], item['view'], 
                          item['date'], item['desc'], item['like']]

        try :
            self.cursor.execute(select_sql, select_arg)
            rows = self.cursor.fetchall()
            if len(rows) == 1 :
                return item
        except :
            print(select_sql, select_arg)
            sys.exit(1)
        try :
            self.cursor.execute(insert_sql, insert_arg)
            self.crawlDB.commit()
        except:
            print(insert_sql, insert_arg)
            sys.exit(1)
        return item

class ImdbPipeline:
    def __init__(self) :
        try :
            self.crawlDB = pymysql.connect(
                user=SQL_USER,
                passwd=SQL_PW,
                host=SQL_HOST,
                port=SQL_PORT,
                db=SQL_DB
            )
            self.cursor = self.crawlDB.cursor()
        except :
            print('ERROR: DB connection failed')
            sys.exit(1)
        
    def process_item(self, item, spider):
        select_sql = ''
        select_arg = []
        insert_sql = ''
        insert_arg = []
        if type(item) == ImdbMovieItem :
            select_sql = 'SELECT * from ImdbMovie where movieId = %s'
            select_arg = [item['id']]
            insert_sql = 'INSERT INTO ImdbMovie(movieId, title, plot, storyline) VALUES(%s, %s, %s, %s)'
            insert_arg = [item['id'], item['title'],
                          item['plot'], item['storyline']]
        elif type(item) == ImdbReviewItem :
            item['cmt_title'] = emoji_filter.sub(r'', item['cmt_title'])
            item['cmt_body'] = emoji_filter.sub(r'', item['cmt_body'])
            select_sql = 'SELECT * from ImdbReview where reviewId = %s'
            select_arg = [item['review_id']]
            insert_sql = 'INSERT INTO ImdbReview(reviewId, movieId, title, body, date, rate) VALUES(%s, %s, %s, %s, %s, %s)'
            insert_arg = [item['review_id'], item['movie_id'], item['cmt_title'], 
                          item['cmt_body'], item['date'], item['rate']]
        try :
            self.cursor.execute(select_sql, select_arg)
            rows = self.cursor.fetchall()
            if len(rows) == 1 :
                return item
        except :
            print(select_sql, select_arg)
            sys.exit(1)
        try :
            self.cursor.execute(insert_sql, insert_arg)
            self.crawlDB.commit()
        except:
            print(insert_sql, insert_arg)
            sys.exit(1)
        return item

class WebtoonPipeline:
    def __init__(self) :
        try :
            self.crawlDB = pymysql.connect(
                user=SQL_USER,
                passwd=SQL_PW,
                host=SQL_HOST,
                port=SQL_PORT,
                db=SQL_DB
            )
            self.cursor = self.crawlDB.cursor()
        except :
            print('ERROR: DB connection failed')
            sys.exit(1)
        
    def process_item(self, item, spider):
        insert_sql = ''
        insert_arg = []
        if type(item) == WebtoonItem :
            insert_sql = 'INSERT IGNORE INTO Webtoon(webtoonId, title, author, subscriber, lang) VALUES(%s, %s, %s, %s, %s)'
            insert_arg = [item['id'], item['title'], item['author'], item['subs'], item['lang']]
        elif type(item) == WebtoonCommentItem :
            item['body'] = emoji_filter.sub(r'', item['body'])
            insert_sql = 'INSERT IGNORE INTO WebtoonComment(commentId, webtoonId, episodeNo, body, date, lang, country) VALUES(%s, %s, %s, %s, %s, %s, %s)'
            insert_arg = [item['commentId'], item['webtoonId'], item['episodeNo'], 
                          item['body'], item['date'], item['lang'], item['country']]

        try :
            self.cursor.execute(insert_sql, insert_arg)
            self.crawlDB.commit()
        except:
            print(insert_sql, insert_arg)
            sys.exit(1)
        return item

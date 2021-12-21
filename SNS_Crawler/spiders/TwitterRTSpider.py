import json

import scrapy
from SNS_Crawler.items import TwitterRTItem
from scrapy.loader import ItemLoader

import twint
import datetime as dt
from datetime import datetime
from dateutil.relativedelta import relativedelta

def write_json(path, data) :
    if path[-5:] != ".json":
        path = path +".json"
    with open(path, 'w', encoding = "utf-8") as outfile:
        outfile.write(json.dumps(data, ensure_ascii=False))


class TwitterRTSpider(scrapy.Spider):
    name = 'twitter_user_rt'
    custom_settings = {
    }
    def __init__(self, users='', begin_date='', end_date='', geo=''):
        self.config = twint.Config()
        self.set_custom(["id", "conversation_id","date", "username", "user_id", "tweet", "language", "geo", "mention"])
        # 좌측이 데이터베이스에 표시할 내용, 우측이 실제 트위터에서 데이터를 수집할 때 사용할 파라미터
        self.set_timedelta("day")
        self.geo = geo
        self.geo_user = {
            "North_America":["allkpop","soompi","iconickdramas","kdramafairy","kdramaworlld"],
            "Southeast_Asia":["infodrakor_id", "kdrama_menfess", "korcinema_fess"],
            "Europe":["Spain_Kpop_", "Kpop_Project_SP"],
        }
        self.user_geo = {
            "allkpop":"North_America",
            "soompi": "North_America",
            "iconickdramas" : "North_America",
            "kdramafairy" : "North_America",
            "kdramaworlld" : "North_America",
            "infodrakor_id":"Southeast_Asia",
            "kdrama_menfess":"Southeast_Asia",
            "korcinema_fess":"Southeast_Asia",
            "Spain_Kpop_":"Europe",
            "Kpop_Project_SP" : "Europe"
        }

        self.users = ['allkpop']
        if users != '':
            self.users = users.split(',')
        if geo != '':
            self.users = self.geo_user[geo]
        self.begin_date = '2020-08-16'
        self.end_date = '2020-08-18'
        if begin_date != '' :
            self.begin_date = f'{begin_date[:4]}-{begin_date[4:6]}-{begin_date[6:8]}'
        if end_date != '' :
            self.end_date = f'{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}'
        if geo != '':
            self.geo = geo
        else :
            self.geo =''
    def set_custom(self, customList:list):
        self.config.Custom["tweet"] = customList
        print("Custom: ",self.config.Custom["tweet"])
    def set_timedelta(self, period):
        self.period = period
        if period == "day":
            self.timedelta = dt.timedelta(days=1)
        elif period == "week" :
            self.timedelta = dt.timedelta(weeks=1)
        elif period == "month" :
            self.timedelta = relativedelta(months=1)
        elif period == "quarter" :
            self.timedelta = relativedelta(months=3)
        elif period == "year" :
            self.timedelta = relativedelta(years=1)

    def start_requests(self):
        print("start_requests")
        start_url = 'http://quotes.toscrape.com/page/1/'
        #start_url = "https://api.twitter.com/1.1/tweets/search/30day/dev.json"
        
        yield scrapy.Request(url = start_url, callback=self.search)

    
    def search(self, response):
        
        self.config.Hide_output = False
        self.config.Popular_tweets = True
        
        # Language Filter (off)
        #self.config.Lang = lang
        # if self.geo != '':
        #         self.config.Geo = self.geo
        for username in self.users:
            print(f"#### {username} ####")
            self.config.Search ="@"+username
            
            # date setting
            pivot = self.begin_date
            date_since = datetime.strptime(self.begin_date, '%Y-%m-%d')
            date_until = datetime.strptime(self.end_date,'%Y-%m-%d')
            date_pivot = date_since
            while True :
                self.config.Store_object = True

                self.config.Since = pivot
                date_pivot = datetime.strptime(pivot, '%Y-%m-%d')    
                
                if date_pivot >= date_until :
                    # condition like do while statement
                    break
                date_end = date_pivot + self.timedelta
                end = date_end.strftime("%Y-%m-%d")
                print("#### ", datetime.now(), "####")
                print(f"search for {username} between {self.config.Since} and {end}")
                
                while True :
                    tweets = []
                    self.config.Store_object_tweets_list =tweets
                    if date_pivot >= datetime.strptime(end, '%Y-%m-%d') :
                        break
                    date_pivot = date_pivot + dt.timedelta(days=1)
                    pivot = datetime.strftime(date_pivot, '%Y-%m-%d')
                    self.config.Until = pivot
                    
                    twint.run.Search(self.config)
                    print(f"complete search for {username} between {self.config.Since} and {self.config.Until}")

                    for tweet in tweets:
                        loader = ItemLoader(item = TwitterRTItem(),response=response)
                        loader.add_value('rtId', str(tweet.id))
                        loader.add_value('bodyId',str(tweet.conversation_id))
                        loader.add_value('userId', str(tweet.user_id))
                        loader.add_value('username', tweet.username)
                        loader.add_value('name',tweet.name)
                        loader.add_value('date',str(tweet.datestamp))
                        loader.add_value('body',tweet.tweet)
                        loader.add_value('lang',tweet.lang)
                        loader.add_value('hashtags',tweet.hashtags)
                        try:
                            loader.add_value('geo',self.user_geo[username])
                        except:
                            loader.add_value('geo',self.geo)


                        yield loader.load_item()

                    print("Search Done!")
                    
                    self.config.Since = pivot
                        
import json

import scrapy
from SNS_Crawler.items import TwitterGeoItem
from SNS_Crawler.apikey import *
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

class TwitterGeoSpider(scrapy.Spider):
    name = 'twitter_geo'
    custom_settings = {
    }
    def __init__(self, keywords='', geo='', begin_date='', end_date=''):
        self.config = twint.Config()
        self.set_custom(["id", "date", "username", "user_id", "tweet", "language", "geo"])
        # 좌측이 데이터베이스에 표시할 내용, 우측이 실제 트위터에서 데이터를 수집할 때 사용할 파라미터
        self.geoDict = {
            "North_America":"39.09988405413171,-94.57866878020425,2400km",
            "South_America":"-25.26125550803821,-57.57779557215821,3500km",
            "Southeast_Asia": "10.759904,106.682048,1800km",
            "Japan" : "35.65864508541174,139.74547153338207,700km",
            "Europe": "47.804523, 13.042257,1200km",
            "India":"17.371338917502417,78.4803041351664,1000km",
            "Australia": "-28.00265437536671,134.39228939983974,2000km",
            "South_Africa":"-32.64648576305515,27.617846079254992,1100km",
            "Middle_East":"28.496720866936958,44.304230826320286,1600km",
        }
        self.set_timedelta("day")

        self.keywords = ['BTS']
        if keywords != '':
            self.keywords = keywords.split(',')
        self.begin_date = '2018-01-01'
        self.end_date = '2018-01-31'
        if begin_date != '' :
            self.begin_date = f'{begin_date[:4]}-{begin_date[4:6]}-{begin_date[6:8]}'
        if end_date != '' :
            self.end_date = f'{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}'
        self.geoList = ['North_America']
        if geo != '':
            self.geoList = geo.split(',')
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

        # Retweets Filter (off)
        self.config.Filter_retweets = True
        self.config.Retweets = False
        self.config.Native_retweets = False

        for keyword in self.keywords:
            print(f"#### {keyword} ####")
            self.config.Search = keyword
            for geo in self.geoList :
                self.config.Geo = self.geoDict[geo]

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
                    print("#### ", geo, "####")
                    print(f"search for {keyword} between {self.config.Since} and {end}")
                    data = []
                    while True :
                        tweets = []
                        self.config.Store_object_tweets_list =tweets
                        if date_pivot >= datetime.strptime(end, '%Y-%m-%d') :
                            break
                        date_pivot = date_pivot + dt.timedelta(days=1)
                        pivot = datetime.strftime(date_pivot, '%Y-%m-%d')
                        self.config.Until = pivot

                        twint.run.Search(self.config)
                        print(f"complete search for {keyword} between {self.config.Since} and {self.config.Until}")
                        
                        for tweet in tweets:
                            loader = ItemLoader(item = TwitterGeoItem(),response=response)
                            loader.add_value('tweetId', str(tweet.id))

                            loader.add_value('userId', str(tweet.user_id))
                            loader.add_value('username', tweet.username)
                            loader.add_value('name',tweet.name)
                            loader.add_value('date',str(tweet.datestamp))
                            loader.add_value('body',tweet.tweet)
                            loader.add_value('lang',tweet.lang)
                            loader.add_value('hashtags',tweet.hashtags)
                            loader.add_value('geo',geo)
                            loader.add_value('keyword',keyword)
                            yield loader.load_item()

                        print("Search Done!")
                        
                        self.config.Since = pivot
                        
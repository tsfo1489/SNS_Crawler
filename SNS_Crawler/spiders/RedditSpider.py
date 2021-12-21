import praw
from praw.models import MoreComments
from psaw import PushshiftAPI
import json
import datetime as dt
from datetime import datetime
from dateutil.relativedelta import relativedelta

import scrapy

from SNS_Crawler.items import RedditItem
from SNS_Crawler.apikey import *
from scrapy.loader import ItemLoader


def write_json(path, data) :
        if path[-5:] != ".json":
            path = path +".json"
        with open(path, 'w', encoding = "utf-8") as outfile:
            outfile.write(json.dumps(data, ensure_ascii=False))

def create_reddit_object():
        reddit = praw.Reddit(client_id = REDDIT_CLIENT_ID,
                            client_secret=REDDIT_CLIENT_SECRET,
                            user_agent=REDDIT_USER_AGENT,
                            username=REDDIT_USERNAME,
                            password=REDDIT_PASSWORD,)
        return reddit

class RedditSpider(scrapy.Spider):
    name = 'reddit'
    
    custom_settings = {
    }
    def __init__(self, subreddit='', begin_date='', end_date='', keywords='',  **kwargs) :
        try :
            self.reddit = create_reddit_object()
            self.set_timedelta("month")
        except :
            self.reddit = None
        self.subreddit = 'kpop'
        if subreddit != '' :
            self.subreddit = subreddit
        self.keywords = []
        if keywords != '':
            self.keywords = keywords.split(',')
        self.begin_date = '2018-01-01'
        self.end_date = '2018-01-05'
        if begin_date != '' :
            self.begin_date = f'{begin_date[:4]}-{begin_date[4:6]}-{begin_date[6:8]}'
        if end_date != '' :
            self.end_date = f'{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}'


    def start_requests(self):
        
        start_url = 'http://quotes.toscrape.com/page/1/'

        self.set_timedelta("day")
        self.keywordList = self.keywords
        self.since = self.begin_date
        self.until = self.end_date
        
        yield scrapy.Request(url = start_url, callback=self.scrap_subreddit)

    def set_reddit(self, client_id, client_secret, user_agent,username, password):
        try:
            self.reddit = praw.Reddit(client_id = client_id,
                            client_secret = client_secret,
                            user_agent = user_agent,
                            username = username,
                            password = password)
            print("Success!")
        except :
            print("Fail!")

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

    def checkKeyword(self, text) :
        findList = []
        for keyword in self.keywordList :
            if keyword in text :
                findList.append(keyword)
        if len(findList) == 0:
            return []
        else :
            return findList

    def scrap_subreddit(self, response):
        if self.reddit == None :
            print("Please set reddit api key")
            return
        
        api = PushshiftAPI(self.reddit)

        before = int(datetime.strptime(self.until, "%Y-%m-%d").timestamp())
        print("from ",self.since," to ", self.until)
        pivot = int(datetime.strptime(self.since, "%Y-%m-%d").timestamp())
        while True :
            print ("item_scraped_count ",self.crawler.stats.get_value('item_scraped_count'))
            if pivot >= before :
                print("pivot>=before break")
                break
            
            date = datetime.fromtimestamp(pivot)
            next_pivot = int((date + self.timedelta).timestamp())
            if next_pivot > before :
                next_pivot = before
            print("### ",datetime.now() ,"subreddit ", self.subreddit, " ###")
            self.submissionList = list(api.search_submissions(
                after = pivot,
                before = next_pivot,
                subreddit=self.subreddit,
                filter=['title','subreddit']
                ))
            print(date, " ~ ", datetime.fromtimestamp(next_pivot))

            num = 0
            self.previousTitle = ""
            total = len(self.submissionList)
            print("total ",total," results")
            for submission in self.submissionList :
                loader = ItemLoader(item = RedditItem(), response=response)
                self.submission = submission
                num += 1

                if num % 500 == 0:
                    print(f"Analyzing {num} results...",num*100//total,"%")
                if submission.selftext == "[deleted]" or submission.selftext == "[removed]" :
                    # deleted or removed 상태의 글은 제외한다.
                    continue
                elif submission.title == self.previousTitle :
                    # 샘플링 결과 이전 글의 제목과 같은 경우가 다수 발견되었다. 이 경우도 제외한다.
                    continue
                else :
                    # 키워드를 입력하면 키워드 필터링 실행
                    # 키워드를 입력하지 않으면 전수조사
                    if len(self.keywordList) != 0:
                        checkTitle = self.checkKeyword(submission.title)
                        checkText = self.checkKeyword(submission.selftext)
                        checkText.extend(checkTitle)
                        checkText = list(set(checkText))
                        print(checkText)
                        if len(checkText) == 0 :
                            continue
                            
                    commentList = []
                    loader = ItemLoader(item = RedditItem(), response=response)
                    # 키워드, 검색결과번호, 제목, 날짜, 내용, 댓글을 저장한다.
                
                    loader.add_value('postId', self.submission.id)
                    loader.add_value('title', self.submission.title)
                    self.previousTitle = self.submission.title
                    loader.add_value('body', self.submission.selftext)
                    date = datetime.fromtimestamp(self.submission.created_utc)
                    loader.add_value('date', str(date))
                    loader.add_value('subreddit', self.subreddit)
                    
                    for top_level_comment in self.submission.comments:
                        if isinstance(top_level_comment, MoreComments) :
                            # MoreComments는 무시한다.
                            continue
                        elif top_level_comment.body.strip() == "[deleted]" or top_level_comment.body.strip() == "[removed]" :
                            # 코멘트가 지워진 경우도 무시한다.
                            continue
                        else :
                            commentDict = {}
                            commentDict["commentId"] = top_level_comment.id
                            commentDict["body"] = top_level_comment.body.strip().replace('\"','\\\"')
                            date_comment = datetime.fromtimestamp(top_level_comment.created_utc)
                            commentDict["date"] = str(date_comment)
                            commentList.append(commentDict)

                    loader.add_value('comments', commentList)
                    yield loader.load_item()

            print("Done!")
            pivot = next_pivot
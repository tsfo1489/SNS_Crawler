import scrapy, json
from urllib import parse
from datetime import datetime
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from ..items import *


class WebtoonNaverSpider(scrapy.Spider):
    name = 'webtoon_naver'
    webtoons = ['2550']
    comment_url = 'https://global.apis.naver.com/commentBox/cbox/web_neo_list_jsonp.json?'

    custom_settings = {
    }

    def __init__(self, webtoons='', **kwargs) :
        if webtoons != '':
            self.webtoons = [x for x in webtoons.split(',')]
        print(self.webtoons)
        super().__init__(**kwargs)

    def start_requests(self):
        for w in self.webtoons :
            if w.isdigit() :
                yield scrapy.Request(
                    url=f'https://www.webtoons.com/en/sports/the-boxer/list?title_no={w}',
                    callback=self.get_meta_webtoon
                )
            else :
                yield scrapy.Request(w, self.get_meta_webtoon)

    def subs_str_to_int(self, raw_sub) :
        sub = 0
        raw_sub = raw_sub.replace(',', '.')
        if raw_sub[-1] == 'M' :
            sub = float(raw_sub[:-1]) * 1000000
        elif raw_sub[-1] == 'K' :
            sub = float(raw_sub[:-1]) * 1000
        elif raw_sub[-1] == '萬' :
            sub = float(raw_sub[:-1]) * 10000
        elif raw_sub[-2:] == 'RB' :
            sub = float(raw_sub[:-2]) * 1000
        elif raw_sub[-2:] == 'JT' :
            sub = float(raw_sub[:-2]) * 1000000
        else :
            sub = float(raw_sub)
        return round(sub)

    def get_meta_webtoon(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        doc = WebtoonItem()
        parsed_query = dict(parse.parse_qsl(response.url[response.url.find('?') + 1:]))
        doc['id'] = 'N' + parsed_query['title_no']
        raw_subs = soup.select_one('em.cnt').text.strip()
        doc['subs'] = self.subs_str_to_int(raw_subs)
        doc['title'] = soup.select_one('h1.subj').text
        raw_author = soup.select_one('a.author')
        raw_author = [obj.strip() for obj in raw_author if isinstance(obj, NavigableString)]
        doc['author'] = ''.join(raw_author)
        url = response.url
        lang = url[url.find('com/') + 4:url.find('com/') + 6]
        doc['lang'] = lang
        yield doc

        episode_n = int(soup.select_one('span.tx').text[1:])
        lang = url[url.find('com/') + 4:url.find('com/') + 6]
        param = {
                'ticket': 'webtoon',
                'templateId': 'or_' + (lang if lang != 'zh' else 'tw'),
                'pool': 'cbox',
                'lang': lang,
                'pageSize': 100,
                'sort': 'z',
                'consumerKey' : 'BiqLr39tq3iAWWxuiOXg',
                '_callback' : 'a'
            }
        hd = {'referer' : 'https://www.webtoons.com'}
        for epi in range(episode_n) :
            param['objectId'] = f'w_{doc["id"][1:]}_{epi}'
            param['page'] = 1
            yield scrapy.Request(
                    url=self.comment_url + parse.urlencode(param), 
                    headers=hd, 
                    callback=self.parse_comment,
                    meta={'webtoon':doc, 'epi':epi}
                )
    
    def parse_comment(self, response):
        data = json.loads(response.body[2:-2])
        for c in data['result']['commentList'] :
            comment = WebtoonCommentItem()
            comment['commentId'] = c['commentNo']
            comment['webtoonId'] = response.meta['webtoon']['id']
            comment['episodeNo'] = response.meta.get('epi')
            comment['date'] = c['regTime'][:10]
            comment['lang'] = c['lang']
            comment['country'] = c['country']
            comment['body'] = c['contents']
            yield comment

        parsed_query = dict(parse.parse_qsl(response.url[response.url.find('?') + 1:]))
        parsed_query['page'] = int(parsed_query['page'])
        if parsed_query['page'] < data['result']['pageModel']['lastPage'] :
            parsed_query['page'] = parsed_query['page'] + 1
            query_str = parse.urlencode(parsed_query)
            hd = {'referer' : 'https://www.webtoons.com'}
            yield scrapy.Request(
                    url=self.comment_url + query_str, 
                    headers=hd, 
                    callback=self.parse_comment,
                    meta=response.meta
                )

class WebtoonTapasSpider(scrapy.Spider):
    name = 'webtoon_tapas'
    webtoons = ['https://tapas.io/series/tbate-comic/info']
    custom_settings = {
        'LOG_FILE': 'log/webtoon_tapas.log'
    }

    def __init__(self, webtoons='', **kwargs) :
        if webtoons != '':
            self.webtoons = [x for x in webtoons.split(',')]
        print(self.webtoons)
        super().__init__(**kwargs)

    def start_requests(self):
        for w in self.webtoons :
            if w.isdigit() :
                yield scrapy.Request(
                    f'https://tapas.io/series/{w}/info',
                    self.get_meta_webtoon,
                    meta={'webtoon':w}
                )
            else :
                yield scrapy.Request(w, self.get_meta_webtoon)
    
    def get_meta_webtoon(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        doc = WebtoonItem()
        doc['title'] = soup.select_one('a.title').text.strip()
        doc['subs'] = soup.select_one('a.js-subscribe-cnt')['data-cnt']
        raw_id = soup.select_one('a.js-subscribe-cnt')['href']
        raw_id = raw_id[raw_id.rfind('=') + 1:]
        doc['id'] = 'T' + raw_id
        raw_author = [x.text.strip() for x in soup.select('ul.creator-section a.name')]
        doc['author'] = ' / '.join(raw_author)
        doc['lang'] = 'en'
        yield doc

        yield scrapy.Request(
            f'https://tapas.io/series/{doc["id"][1:]}/episodes?page=1&sort=OLDEST',
            self.parse_list,
            meta={'webtoon':doc}
        )

    def parse_list(self, response) :
        data = json.loads(response.body)
        soup = BeautifulSoup(data['data']['body'],'html.parser')
        episodes = soup.select('li.body__item')
        w = response.meta['webtoon']
        parsed = parse.urlparse(response.url)
        new_q = dict(parse.parse_qsl(parse.urlparse(response.url, 'query').query))
        new_q['page'] = int(new_q['page']) + 1
        parsed = parsed._replace(query=parse.urlencode(new_q))
        for episode in episodes :
            yield scrapy.Request(
                f'https://tapas.io/comment/{episode["data-id"]}?page=1',
                self.parse_page,
                meta={'webtoon':w, 'epi':episode.select_one('a.info__label').text[8:].strip()}
            )
        if len(episodes) == 20 :
            yield scrapy.Request(
                        parse.urlunparse(parsed), 
                        self.parse_list,
                        meta={'webtoon':w})

    def parse_page(self, response):
        data = json.loads(response.body)
        soup = BeautifulSoup(data['data']['html'],'html.parser')
        cmtarr = soup.select('div.body__row')
        w = response.meta['webtoon']
        epi = response.meta['epi']
        parsed = parse.urlparse(response.url)
        new_q = dict(parse.parse_qsl(parse.urlparse(response.url, 'query').query))
        new_q['page'] = int(new_q['page']) + 1
        parsed = parsed._replace(query=parse.urlencode(new_q))
        for c in cmtarr:
            comment = WebtoonCommentItem()
            comment['webtoonId'] = response.meta['webtoon']['id']
            comment['episodeNo'] = response.meta.get('epi')
            comment['commentId'] = c.select_one('a.info__button')['data-id']
            comment['body'] = c.select_one('div.body__comment').text
            raw_date = c.select_one('p.writer__date').text
            comment['date'] = datetime.strptime(raw_date, '%b %d, %Y').strftime('%Y-%m-%d')
            comment['lang'] = 'en'
            comment['country'] = 'US'

            yield comment
        if len(cmtarr) == 10 :
            yield scrapy.Request(
                        parse.urlunparse(parsed), 
                        self.parse_page,
                        meta={'webtoon':w,'epi':epi})
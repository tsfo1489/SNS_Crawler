import scrapy, json, time
from urllib import parse
from datetime import datetime
from bs4 import BeautifulSoup
from ..items import NewsItem
from ..apikey import *
from selenium import webdriver

class CnGlobaltimesSpider(scrapy.Spider):
    name = 'CN_globaltimes'
    allowed_domains = ['huanqiu.com', 'customsearch.googleapis.com']
    keywords = ['K-pop']
    begin_date = datetime.strptime('20180101', '%Y%m%d')
    end_date = datetime.strptime('20210630', '%Y%m%d')
    api_url = f'{GOOGLE_CSE_LINK}key={GOOGLE_APIKEY}&alt=json&cx={GLOBALTIMES_CX}&'
    
    custom_settings = {
    }
    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        b_date = self.begin_date.strftime('%Y%m%d')
        e_date = self.end_date.strftime('%Y%m%d')
        self.api_url += f'sort=date:r:{b_date}:{e_date}&'
        super().__init__(**kwargs)

    def start_requests(self):
        for keyword in self.keywords :
            yield scrapy.Request(
                f'{self.api_url}q={keyword}', 
                self.parse_list, 
                meta={'keyword':keyword}
            )

    def parse_list(self, response):
        data = json.loads(response.body)
        result_N = data['queries']['request'][0]['totalResults']
        result_N = int(result_N)
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)

        for article in data['items'] :
            yield scrapy.Request(
                article['link'], 
                self.parse_page, 
                meta=response.meta
            )
            
        if 'nextPage' in data['queries'] :
            next_page = data['queries']['nextPage'][0]
            keyword = response.meta['keyword']
            yield scrapy.Request(
                f'{self.api_url}q={keyword}&start={next_page["startIndex"]}', 
                self.parse_list, 
                meta={'keyword':keyword}
            )
        
    def parse_page(self, response) :
        soup = BeautifulSoup(response.text, 'html.parser')
        if response.url.find('3w.') > 0 :
            raw_date = soup.select_one('span.time').text[:10]
            raw_title = soup.select_one('h1.a-title').text
            raw_body = soup.select_one('div.a-con').text
        else :
            raw_date = soup.select_one('p.time').text[:10]
            raw_title = soup.select_one('div.t-container-title').text
            raw_body = soup.select_one('section').text
            
        doc = NewsItem()
        doc['title'] = raw_title
        doc['body'] = raw_body
        doc['date'] = raw_date
        doc['keyword'] = response.meta.get('keyword')
        doc['newspaperId'] = 1
        doc['url'] = response.url
        return doc

class UsNytimesSpider(scrapy.Spider):
    name = 'US_nytimes'
    keywords = ['K-pop']
    begin_date = datetime.strptime('20180101', '%Y%m%d')
    end_date = datetime.strptime('20210630', '%Y%m%d')
    custom_settings = {
        'DOWNLOAD_DELAY': 6
    }

    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        print(self.keywords, self.begin_date, self.end_date)
        super().__init__(**kwargs)
        
    def start_requests(self):
        main_url = 'https://api.nytimes.com/svc/search/v2/articlesearch.json'
        for keyword in self.keywords :
            for i in range(100):
                param = {
                    'q' : keyword,
                    'api-key' : NYTIMES_APIKEY,
                    'begin_date': self.begin_date,
                    'end_date': self.end_date,
                    'page': i
                }
                url = f'{main_url}?{parse.urlencode(param)}'
                yield scrapy.Request(url, self.parse_list, meta={'keyword':keyword})

    def parse_list(self, response):
        data = json.loads(response.body)
        
        result_N = data['response']['meta']['hits']
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)

        if data['status'] == 'OK' :
            results = data['response']['docs']
            keyword = response.meta.get('keyword')
            for result in results :
                doc = {}
                doc['title'] = result['headline']['main']
                doc['date'] = result['pub_date'][:10]
                doc['keyword'] = keyword
                doc['url'] = result['web_url']
                yield scrapy.Request(doc['url'], self.parse_page, meta=doc)
    
    def parse_page(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        if soup.select_one('h1[data-testid=headline]') is None :
            pass
        else :
            metadata = response.meta
            doc = NewsItem()
            doc['title'] = metadata['title']
            doc['body'] = soup.select_one('section[name=articleBody]').text
            doc['date'] = metadata['date']
            doc['keyword'] = metadata['keyword']
            doc['newspaperId'] = 2
            doc['url'] = metadata['url']
            yield doc

class UkGuardianSpider(scrapy.Spider):
    name = 'UK_guardian'
    keywords = ['K-pop']
    begin_date = '2018-01-01'
    end_date = '2021-06-30'
    custom_settings = {
        'DOWNLOAD_DELAY': 0.1,
        'DOWNLOADER_MIDDLEWARES' : {
            'Crawler.middlewares.NewsDownloaderMiddleware': 543,
        }
    }

    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d').strftime('%Y-%m-%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')
        print(self.keywords, self.begin_date, self.end_date)
        super().__init__(**kwargs)

    def start_requests(self):
        main_url = f'https://content.guardianapis.com/search?api-key={GUARDIAN_APIKEY}&from_date={self.begin_date}&end_date={self.end_date}&page-size=100&page=1'
        for keyword in self.keywords :
            yield scrapy.Request(f'{main_url}&q={keyword}', self.parse_list, meta={'keyword':keyword})
        pass

    def parse_list(self, response):
        data = json.loads(response.text)

        result_N = data['response']['total']
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)

        keyword = response.meta.get('keyword')
        for artcData in data['response']['results'] :
            if artcData['type'] == 'article' :
                url = artcData['webUrl']
                yield scrapy.Request(
                    url, 
                    self.parse_page, 
                    meta={'keyword':response.meta.get('keyword')}
                )
                
        parsed = parse.urlparse(response.url)
        new_q = dict(parse.parse_qsl(parse.urlparse(response.url, 'query').query))
        new_q['page'] = int(new_q['page']) + 1
        parsed = parsed._replace(query=parse.urlencode(new_q))
        yield scrapy.Request(parse.urlunparse(parsed), self.parse_list, meta={'keyword':keyword})

    def parse_page(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        if soup.select_one('label[for=dateToggle]') is None :
            raw_date = soup.select_one('div.dcr-18svo86').text[4:-10]
        else :
            raw_date = soup.select_one('label[for=dateToggle]').text[4:-10]
        doc = NewsItem()
        doc['title'] = soup.select_one('h1').text
        doc['body'] = soup.select_one('div.article-body-viewer-selector').text
        doc['date'] = datetime.strptime(raw_date, '%d %b %Y').strftime('%Y-%m-%d')
        doc['keyword'] = response.meta.get('keyword')
        doc['newspaperId'] = 3
        doc['url'] = response.url
        yield doc

class UsLatimesSpider(scrapy.Spider):
    name = 'US_latimes'
    allowed_domains = ['www.latimes.com']
    keywords = ['K-pop']
    begin_date = datetime.strptime('2018-01-01', '%Y-%m-%d')
    end_date = datetime.strptime('2021-06-30', '%Y-%m-%d')

    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        print(self.keywords, self.begin_date, self.end_date)
        super().__init__(**kwargs)

    def start_requests(self):
        main_url = 'https://www.latimes.com/search?'
        for keyword in self.keywords:
            yield scrapy.Request(
                        f'{main_url}q={keyword}&s=1', 
                        self.parse_list, 
                        meta={'keyword':keyword}
                    )

    def parse_list(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')

        result_N = soup.select_one('span.search-results-module-count-desktop > b').text.replace(',','')
        result_N = int(result_N)
        self.crawler.stats.set_value(f'items/{response.meta["keyword"]}', result_N)
        cnt = 0
        for result in soup.select('div.promo-wrapper') :
            raw_date = result.select_one('p.promo-timestamp')['data-date']
            if raw_date.find('.') != -1 :
                date = datetime.strptime(raw_date, '%b. %d, %Y')
            else :
                date = datetime.strptime(raw_date, '%B %d, %Y')
            if date < self.begin_date:
                break
            if date <= self.end_date:
                url = result.select_one('a')['href']
                if url.find('/entertainment-arts/gallery/') == -1 and url.find('/liveblog/') == -1 :
                    yield scrapy.Request(
                                result.select_one('a')['href'], 
                                self.parse_page, 
                                meta=response.meta
                            )
        if not soup.select_one('a[rel=next]') is None and date >= self.begin_date:
            next_page = soup.select_one('a[rel=next]')['href']
            yield scrapy.Request(next_page, self.parse_list, meta=response.meta)

    def parse_page(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        try :
            raw_date = soup.select_one('span.published-date-day').text.strip()
            if raw_date.find('.') != -1 :
                date = datetime.strptime(raw_date, '%b. %d, %Y')
            else :
                date = datetime.strptime(raw_date, '%B %d, %Y')
            doc = NewsItem()
            doc['title'] = soup.select_one('h1.headline').text.strip()
            if soup.select_one('div.rich-text-article-body') is None :
                doc['body'] = soup.select_one('div.rich-text-body').text.strip()
            else :
                doc['body'] = soup.select_one('div.rich-text-article-body').text.strip()
            doc['date'] = date.strftime('%Y-%m-%d')
            doc['keyword'] = response.meta['keyword']
            doc['newspaperId'] = 4
            doc['url'] = response.url
            yield doc
        except AttributeError :
            pass

class SgStraitstimesSpider(scrapy.Spider):
    name = 'SG_straitstimes'
    allowed_domains = ['www.straitstimes.com', 'api.queryly.com']
    keywords = ['K-pop']
    begin_date = datetime.strptime('20180101', '%Y%m%d')
    end_date = datetime.strptime('20210630', '%Y%m%d')
    api_url = 'https://api.queryly.com/json.aspx?queryly_key=a7dbcffb18bb41eb&'
    hds={
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71',
        'referer' : 'https://www.straitstimes.com',
    }
    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        self.cookies = self.get_login_cookie()
        super().__init__(**kwargs)

    def get_login_cookie(self) :
        options = webdriver.ChromeOptions()
        options.add_argument('window-size=1920,1080')
        options.add_argument('headless')
        options.add_argument("disable-gpu")
        driver = webdriver.Chrome(CHROMDRIVER_PATH, options=options)

        driver.implicitly_wait(3)
        driver.get('https://www.straitstimes.com/global')
        driver.refresh()
        main_page_title = driver.title
        driver.find_element_by_css_selector('a#sph_login').click()
        id_field = driver.find_element_by_css_selector('input#IDToken1')
        id_field.send_keys(STRAITS_ID)
        pw_field = driver.find_element_by_css_selector('input#IDToken2')
        pw_field.send_keys(STRAITS_PW)
        driver.find_element_by_css_selector('button#btnLogin').click()
        flag = False
        while True :
            print(driver.title)
            if driver.title != main_page_title :
                flag = True
            if driver.title == main_page_title and flag :
                break
            time.sleep(1)
        raw_cookies = driver.get_cookies()
        cookies = {}
        for cookie in raw_cookies :
            cookies[cookie['name']] = cookie['value']
        driver.close()
        return cookies

    def start_requests(self):
        for keyword in self.keywords :
            yield scrapy.Request(
                    f'{self.api_url}query={keyword}', 
                    self.parse_list, 
                    cookies=self.cookies,
                    meta={'keyword':keyword},
                  )

    def parse_list(self, response):
        data = json.loads(response.body)

        result_N = data['metadata']['total']
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)

        keyword = response.meta.get('keyword')
        for article in data['items'] :
            raw_date = article['pubdate']
            date = datetime.strptime(raw_date, '%b %d, %Y')
            if date >= self.begin_date and date <= self.end_date:
                yield scrapy.Request(
                        article['link'], self.parse_page,
                        meta=response.meta,
                        headers=self.hds,
                        cookies=self.cookies
                    )
        if data['metadata']['total'] > data['metadata']['endindex'] :
            end = data['metadata']['endindex']
            yield scrapy.Request(
                    f'{self.api_url}query={keyword}&startindex={end}', 
                    self.parse_list, 
                    cookies=self.cookies,
                    meta=response.meta
                  )

    def parse_page(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        if len(soup.select('div.paywall-text-area')) > 0 :
            print(response.url, 'cost')
        
        doc = NewsItem()
        doc['title'] = soup.select_one('h1.headline').text.strip()
        doc['body'] = soup.select_one('div[itemprop=articleBody]').text.strip()
        raw_date = soup.select_one('li.story-postdate').text.strip()
        raw_date = datetime.strptime(raw_date[9:raw_date.rfind(',')], '%b %d, %Y')
        doc['date'] = raw_date.strftime('%Y-%m-%d')
        doc['keyword'] = response.meta['keyword']
        doc['newspaperId'] = 5
        doc['url'] = response.url
        yield doc

class JpAsahiSpider(scrapy.Spider):
    name = 'JP_asahi'
    allowed_domains = ['asahi.com']
    keywords = ['K-pop']
    begin_date = datetime.strptime('20180101', '%Y%m%d')
    end_date = datetime.strptime('20210630', '%Y%m%d')
    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        super().__init__(**kwargs)

    def start_requests(self):
        login_url = 'https://digital.asahi.com/login/login.html?'
        login_data = {
            'jumpUrl': 'https://www.asahi.com/',
            'login_id': ASAHI_ID,
            'login_password': ASAHI_PW
        }
        yield scrapy.FormRequest(login_url, callback=self.search, formdata=login_data)
    
    def search(self, response) :
        temp_cookies = response.headers.getlist('Set-Cookie')[0].decode("utf-8").split(";")
        self.cookies = {}
        for cookie in temp_cookies:
            if cookie == '':
                continue
            self.cookies[cookie.split('=')[0].strip()] = cookie.split('=')[1].strip()

        api_url = 'https://sitesearch.asahi.com/sitesearch-api/?'
        for keyword in self.keywords :
            yield scrapy.Request(f'{api_url}Keywords={keyword}&start={0}', self.parse_list, meta={'keyword':keyword})

    def parse_list(self, response) :
        data = json.loads(response.body)['goo']

        result_N = data['hit_num']['num']
        result_N = int(result_N)
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)

        for article in data['docs'] :
            raw_date = article['ReleaseDate'][:8]
            raw_date = datetime.strptime(raw_date, '%Y%m%d')
            if raw_date >= self.begin_date and raw_date <= self.end_date:
                yield scrapy.Request(
                        article['URL'], 
                        self.parse_page, 
                        cookies=self.cookies,
                        meta={'keyword':response.meta['keyword'], 'date':raw_date}
                    )

        if data['hit_num']['num'] > data['range']['to'] :
            parsed = parse.urlparse(response.url)
            new_q = dict(parse.parse_qsl(parse.urlparse(response.url, 'query').query))
            new_q['start'] = int(data['range']['to']) + 1
            parsed = parsed._replace(query=parse.urlencode(new_q))
            yield scrapy.Request(parse.urlunparse(parsed), self.parse_list, meta=response.meta)

    def parse_page(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        doc = NewsItem()
        if response.url.find('book') > 0 or response.url.find('webronza') > 0 :
            doc['title'] = soup.select('h1')[0].text.strip()    
        else :
            doc['title'] = soup.select('h1')[1].text.strip()
        
        if response.url.find('webronza') > 0 :
            doc['body'] = soup.select_one('div.entryBody').text.strip()
        elif response.url.find('book') > 0 :
            if soup.select_one('section.module-body') is None :
                return
            doc['body'] = soup.select_one('section.module-body').text.strip()
        elif soup.select_one('div._3YqJ1') is None :
            doc['body'] = soup.select_one('div.ArticleBody').text.strip()
        else :
            doc['body'] = soup.select_one('div._3YqJ1').text.strip()
        doc['date'] = response.meta['date'].strftime('%Y-%m-%d')
        doc['keyword'] = response.meta.get('keyword')
        doc['newspaperId'] = 6
        doc['url'] = response.url
        yield doc

class JpSankeiSpider(scrapy.Spider):
    name = 'JP_sankei'
    keywords = ['K-pop']
    begin_date = datetime.strptime('20180101', '%Y%m%d')
    end_date = datetime.strptime('20210630', '%Y%m%d')
    api_url = 'https://www.sankei.com/pf/api/v3/content/fetch/sd-search-api?query='

    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        super().__init__(**kwargs)

    def start_requests(self):
        login_url = 'https://special.sankei.com/login'
        yield scrapy.Request(login_url, self.get_auth)

    def get_auth(self, response) :
        temp = dict(parse.parse_qsl(parse.urlparse(response.url).query))
        login_data = {
            'LOGIN': 'ログイン',
            'STAY_LOGGED_IN': '1',
            'LOGIN_ID': SANKEI_ID,
            'LOGIN_PASSWORD': SANKEI_PW,
            'vm': 'post',
            'AuthState': temp['AuthState']
        }
        yield scrapy.FormRequest(response.url, callback=self.login, formdata=login_data)

    def login(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        saml = {
            'SAMLResponse': soup.select_one('input[name="SAMLResponse"]')['value']
        }
        yield scrapy.FormRequest('https://special.sankei.com/saml/sp/sankeinews-sp/login', callback=self.search, formdata=saml)

    def search(self, response) :
        temp_cookies = response.headers.getlist('Set-Cookie')[0].decode("utf-8").split(";")
        self.cookies = {}
        for cookie in temp_cookies:
            if len(cookie.split('=')) < 2:
                continue
            self.cookies[cookie.split('=')[0].strip()] = cookie.split('=')[1].strip()
        for keyword in self.keywords :
            query = json.dumps({'kw': keyword}, ensure_ascii=False)
            yield scrapy.Request(f'{self.api_url}{query}', self.parse_list, meta={'keyword': keyword})

    def parse_list(self, response):
        data = json.loads(response.body)

        result_N = data['total_count']
        result_N = int(result_N)
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)

        for article in data['content_elements'] :
            if not 'display_date' in article :
                continue
            raw_date = datetime.strptime(article['display_date'][:10], '%Y-%m-%d')
            if not 'website_url' in article or raw_date < self.begin_date or raw_date > self.end_date:
                continue
            yield scrapy.Request(
                    'https://www.sankei.com'+article['website_url'], 
                    self.parse_page, 
                    meta=response.meta,
                    cookies=self.cookies
                  )
        if data['total_count'] > data['page'] * 10 :
            keyword = response.meta['keyword']
            query = json.dumps({'kw': keyword, 'p':data['page'] + 1}, ensure_ascii=False)
            yield scrapy.Request(f'{self.api_url}{query}', self.parse_list, meta={'keyword': keyword})

    def parse_page(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        doc = NewsItem()
        doc['title'] = soup.select_one('h3.article-headline').text.strip()
        doc['body'] = soup.select_one('div.article-body').text.strip()
        raw_date = soup.select_one('time')['datetime'][:10]
        doc['date'] = raw_date
        doc['keyword'] = response.meta['keyword']
        doc['newspaperId'] = 7
        doc['url'] = response.url
        yield doc

class SaBbcmundoSpider(scrapy.Spider):
    name = 'SA_bbcmundo'
    allowed_domains = ['bbc.com', 'customsearch.googleapis.com']
    keywords = ['K-pop']
    begin_date = datetime.strptime('20180101', '%Y%m%d')
    end_date = datetime.strptime('20210630', '%Y%m%d')
    api_url = f'{GOOGLE_CSE_LINK}key={GOOGLE_APIKEY}&alt=json&cx={BBCMUNDO_CX}&'

    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        b_date = self.begin_date.strftime('%Y%m%d')
        e_date = self.end_date.strftime('%Y%m%d')
        self.api_url += f'sort=date:r:{b_date}:{e_date}&'
        super().__init__(**kwargs)

    def start_requests(self):
        for keyword in self.keywords :
            yield scrapy.Request(
                f'{self.api_url}q={keyword}', 
                self.parse_list, 
                meta={'keyword':keyword}
            )

    def parse_list(self, response):
        data = json.loads(response.body)
        
        result_N = data['queries']['request'][0]['totalResults']
        result_N = int(result_N)
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)

        for article in data['items'] :
            if not '/topics/' in article['link']:
                yield scrapy.Request(
                    article['link'], 
                    self.parse_page, 
                    meta=response.meta
                )

        if 'nextPage' in data['queries'] :
            next_page = data['queries']['nextPage'][0]
            keyword = response.meta['keyword']
            yield scrapy.Request(
                f'{self.api_url}q={keyword}&start={next_page["startIndex"]}', 
                self.parse_list, 
                meta={'keyword':keyword}
            )

    def parse_page(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        doc = NewsItem()
        doc['title'] = soup.select_one('h1#content').text.strip()
        body = ''
        for raw_body in soup.select('div.bbc-19j92fr') :
            body += raw_body.text.strip() + '\n'
        doc['body'] = body
        raw_date = soup.select_one('time')['datetime'][:10]
        doc['date'] = raw_date
        doc['keyword'] = response.meta['keyword']
        doc['newspaperId'] = 8
        doc['url'] = response.url
        yield doc

class FRLeMondeSpider(scrapy.Spider):
    name = 'FR_lemonde'
    keywords = ['K-Pop']
    begin_date = datetime.strptime('2018-01-01', '%Y-%m-%d')
    end_date = datetime.strptime('2021-06-30', '%Y-%m-%d')
    custom_settings = {
        'ITEM_PIPELINES': {
            'Crawler.pipelines.NewsPipeline' : 100
        },
        'LOG_FILE': 'log/lemonde.log'
    }

    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        print(self.keywords, self.begin_date, self.end_date)
        super().__init__(**kwargs)
    
    def start_requests(self):
        yield scrapy.Request('https://secure.lemonde.fr/sfuser/connexion', self.login)

    def login(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        token = soup.select_one('input#connection__token')['value']
        login_data = {
            'connection[mail]': LEMONDE_ID,
            'connection[password]': LEMONDE_PW,
            'connection[_token]': token
        }
        yield scrapy.FormRequest(response.url, callback=self.search, formdata=login_data)
        pass

    def search(self, response) :
        temp_cookies = response.headers.getlist('Set-Cookie')[0].decode("utf-8").split(";")
        self.cookies = {}
        for cookie in temp_cookies:
            if len(cookie.split('=')) < 2:
                continue
            self.cookies[cookie.split('=')[0].strip()] = cookie.split('=')[1].strip()
        main_url = 'https://www.lemonde.fr/recherche/?'
        bd = self.begin_date.strftime('%d/%m/%Y')
        ed = self.end_date.strftime('%d/%m/%Y')
        
        for keyword in self.keywords:
            yield scrapy.Request(
                    f'{main_url}search_keywords={keyword}&start_at={bd}&end_at={ed}&search_sort=relevance_desc',
                    self.parse_list, 
                    meta={'keyword':keyword}
                )

    def parse_list(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')

        for result in soup.select('section.teaser--inline-picture') :
            if not '/live/' in result.select_one('a.teaser__link')['href'] :
                yield scrapy.Request(
                        result.select_one('a.teaser__link')['href'], 
                        self.parse_page, 
                        meta=response.meta,
                        cookies=self.cookies
                    )
        
        pages = soup.select('a.river__pagination')
        current_page = soup.select_one('a.river__pagination--focus-search')
        cpn = int(current_page.text)
        en = int(pages[-1].text)
        
        result_N = en * 40
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)
        
        if cpn < en:
            clink = current_page['href'].replace(f'page={cpn}',f'page={cpn+1}')
            yield scrapy.Request(clink, self.parse_list, meta=response.meta)

        
    def parse_page(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        raw_date = soup.select_one('meta[property="og:article:published_time"]')['content']
        date = raw_date[0:10]
        doc = NewsItem()
        doc['title'] = soup.select_one('h1.article__title').text.strip()
        doc['body'] = soup.select_one('.article__content').text.strip()
        doc['date'] = date
        doc['keyword'] = response.meta['keyword']
        doc['newspaperId'] = 9
        doc['url'] = response.url
        yield doc

class ESElPaisSpider(scrapy.Spider):
    name = 'ES_elpais'
    keywords = ['K-pop']
    begin_date = datetime.strptime('2018-01-01', '%Y-%m-%d')
    end_date = datetime.strptime('2021-06-30', '%Y-%m-%d')
    api_url = f'{GOOGLE_CSE_LINK}key={GOOGLE_APIKEY}&alt=json&cx={ELPAIS_CX}&'

    def __init__(self, keywords='', begin_date='', end_date='', **kwargs) :
        if keywords != '':
            self.keywords = keywords.split(',')
        if begin_date != '':
            self.begin_date = datetime.strptime(begin_date, '%Y%m%d')
        if end_date != '' :
            self.end_date = datetime.strptime(end_date, '%Y%m%d')
        print(self.keywords, self.begin_date, self.end_date)
        b_date = self.begin_date.strftime('%Y%m%d')
        e_date = self.end_date.strftime('%Y%m%d')
        self.api_url += f'sort=date:r:{b_date}:{e_date}&'
        super().__init__(**kwargs)
    
    def start_requests(self):
        for keyword in self.keywords :
            yield scrapy.Request(
                f'{self.api_url}q={keyword}', 
                self.parse_list, 
                meta={'keyword':keyword}
            )

    def parse_list(self, response):
        data = json.loads(response.body)
        result_N = data['queries']['request'][0]['totalResults']
        result_N = int(result_N)
        self.crawler.stats.set_value(f'items/counts/{response.meta["keyword"]}', result_N)
        for article in data['items'] :
            if ('.html' in article['link'] or 'smoda.elpais' in article['link']) and '/tag/' not in article['link'] and '/pag/' not in article['link'] and '/album/' not in article['link']:
                yield scrapy.Request(
                    article['link'], 
                    self.parse_page, 
                    meta=response.meta
                )
                
        if 'nextPage' in data['queries'] :
            next_page = data['queries']['nextPage'][0]
            keyword = response.meta['keyword']
            yield scrapy.Request(
                f'{self.api_url}q={keyword}&start={next_page["startIndex"]}', 
                self.parse_list, 
                meta={'keyword':keyword}
            )

    def parse_page(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        key = response.url
        raw_date = ''
        doc = NewsItem()
        if not 'smoda.elpais' in key:
            raw_date = soup.select_one('meta[property="article:published_time"]')['content']
            bodies = ['#ctn_article_body','#cuerpo_noticia','div.atom.atom_single_excerpt']
            for b in bodies:
                ind = 0
                try:
                    doc['body'] = soup.select_one(b).text.strip()
                except:
                    ind = 1
                    pass
                if ind == 0:
                    break
        else:
            raw_date = soup.select_one('time[itemprop=datePublished]')['datetime']
            doc['body'] = soup.select_one('div.entry-content__texto').text.strip()
        doc['title'] = soup.select_one('h1').text
        doc['date'] = raw_date[0:10]
        doc['keyword'] = response.meta['keyword']
        doc['newspaperId'] = 10
        doc['url'] = key
        yield doc
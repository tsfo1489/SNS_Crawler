from datetime import datetime
import scrapy
from bs4 import BeautifulSoup
from ..items import *

class ImdbSpider(scrapy.Spider):
    name = 'imdb'
    allowed_domains = ['imdb.com']
    movies = []
    urls = []
    custom_settings = {
    }
    
    def __init__(self, ids='', urls='', **kwargs):
        super().__init__(**kwargs)
        if ids != '':
            self.movies = ids.split(',')
        if urls != '':
            self.urls = urls.split(',')
        

    def start_requests(self):
        main_url = 'https://www.imdb.com/title/tt'
        for movie in self.movies :
            yield scrapy.Request(
                    f'{main_url}{movie}', 
                    self.parse_movie,
                    meta={'movie':movie}
                )
        for movie in self.urls :
            movie_code = movie[movie.find('/tt') + 3:]
            if '/' in movie_code :
                movie_code = movie_code[:movie_code.find('/')]
            yield scrapy.Request(
                    f'{movie}', 
                    self.parse_movie,
                    meta={'movie':movie_code}
                )


    def parse_movie(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        movie = ImdbMovieItem()
        movie['id'] = response.meta['movie']
        movie['title'] = soup.select_one('h1').text.strip()
        movie['plot'] = soup.select_one('p[data-testid="plot"] > span').text.strip()
        movie['storyline'] = soup.select_one('div[data-testid="storyline-plot-summary"]').text.strip()
        yield movie
        m_code = response.meta.get('movie')
        yield scrapy.Request(
                f'https://www.imdb.com/title/tt{m_code}/reviews/_ajax', 
                self.parse_query, 
                meta={'movie':movie}
            )

    def parse_query(self, response) :
        soup = BeautifulSoup(response.body, 'html.parser')
        cmt_list = soup.select('div.lister-item-content')
        paginationKey = soup.select_one('div.load-more-data')
        m_code = response.meta['movie']['id']

        for c in cmt_list :
            doc = ImdbReviewItem()
            s = c.a['href'].split('/')[2]
            doc['review_id'] = s[2:len(s)]
            doc['movie_id'] = m_code
            doc['cmt_title'] = c.select_one('a.title').text.strip()
            doc['cmt_body'] = c.select_one('div.show-more__control').text.strip()
            raw_date = c.select_one('span.review-date').text.strip()
            doc['date'] = datetime.strptime(raw_date, '%d %B %Y').strftime('%Y-%m-%d')
            try :
                doc['rate'] = int(c.select_one('div.ipl-ratings-bar').text.strip().split('/')[0])
            except :
                doc['rate'] = None
            yield doc

        if not paginationKey is None :
            paginationKey = paginationKey['data-key']
            next_page = f'https://www.imdb.com/title/tt{m_code}/reviews/_ajax?paginationKey={paginationKey}'
            yield scrapy.Request(next_page, callback=self.parse_query, meta={'movie':response.meta['movie']})

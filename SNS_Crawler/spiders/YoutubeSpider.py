import scrapy
import json
import regex as re
from urllib import parse
from ..apikey import YT_APIKEY
from ..items import *

YT_API_LINK = 'https://www.googleapis.com/youtube/v3/'

class YoutubeSpider(scrapy.Spider):
    name = 'Youtube'
    allowed_domains = ['youtube.com', 'googleapis.com']
    custom_settings = {
    }

    def __init__(self, channel_ids='', playlist_ids='', video_ids='', **kwargs):
        super().__init__(**kwargs)
        self.ids = []
        for id in channel_ids.split(','):
            if id != '' :
                self.ids.append({'type':'channel_id', 'id': id})
        for id in playlist_ids.split(',') :
            if id != '' :
                self.ids.append({'type':'playlist', 'id': id})
        for id in video_ids.split(',') :
            if id != '' :
                self.ids.append({'type':'video', 'id': id})

    def start_requests(self):
        for id in self.ids :
            query = {
                'key': YT_APIKEY,
                'part': 'snippet',
                'id': id['id']
            }
            #Playlist
            if id['type'] == 'playlist' :
                query_str = parse.urlencode(query)
                yield scrapy.Request(
                        f'{YT_API_LINK}playlists?{query_str}', 
                        self.get_meta_playlist,
                        meta={'type': 'Playlist','id': id['id']}
                      )
            #Channel ID
            if id['type'] == 'channel_id' :
                query['part'] = 'snippet, statistics'
                query_str = parse.urlencode(query)
                yield scrapy.Request(
                        f'{YT_API_LINK}channels?{query_str}', 
                        self.get_meta_channel,
                        meta={'type': 'Channel','id': id['id']}
                      )
            #Video
            if id['type'] == 'video' :
                query['part'] = 'snippet, statistics'
                query_str = parse.urlencode(query)
                yield scrapy.Request(
                        f'{YT_API_LINK}videos?{query_str}', 
                        self.get_meta_video,
                        meta={'type': 'Video','id': id['id']}
                      )

    def get_meta_playlist(self, response) :
        data = json.loads(response.body)
        data = data['items'][0]
        query = {
            'key': YT_APIKEY,
            'part': 'snippet, statistics',
            'id': data['snippet']['channelId']
        }
        query_str = parse.urlencode(query)
        yield scrapy.Request(
                f'{YT_API_LINK}channels?{query_str}', 
                self.get_meta_channel,
                meta=response.meta
              )

    def get_meta_channel(self, response) :
        data = json.loads(response.body)
        data = data['items'][0]
        doc = YoutubeChannelItem()
        doc['id'] = data['id']
        doc['title'] = data['snippet']['title']
        doc['desc'] = data['snippet']['description']
        doc['view'] = data['statistics']['viewCount']
        doc['subs'] = data['statistics']['subscriberCount']
        doc['video'] = data['statistics']['videoCount']
        yield doc
        query = {
            'key': YT_APIKEY,
            'part': 'snippet',
        }
        if response.meta['type'] == 'Playlist' :
            query['playlistId'] = response.meta['id']
            query_str = parse.urlencode(query)
            yield scrapy.Request(
                    f'{YT_API_LINK}playlistItems?{query_str}',
                    self.parse_playlist,
                    meta={'Channel':doc}
                  )
        elif response.meta['type'] == 'Channel' :
            query['type'] = 'video'
            query['channelId'] = response.meta['id']
            query_str = parse.urlencode(query)
            yield scrapy.Request(
                    f'{YT_API_LINK}search?{query_str}',
                    self.parse_channel,
                    meta={'Channel':doc}
                  )
        elif response.meta['type'] == 'Video' :
            yield response.meta['video_item']
            query = {
                'key': YT_APIKEY,
                'part': 'snippet, id, replies',
                'maxResults': 100,
                'videoId': response.meta['id']
            }
            query_str = parse.urlencode(query)
            yield scrapy.Request(
                f'{YT_API_LINK}commentThreads?{query_str}', 
                self.parse_video, 
                meta=response.meta)
    
    def get_meta_video(self, response) :
        data = json.loads(response.body)
        meta = response.meta
        data = data['items'][0]
        doc = YoutubeVideoItem()
        doc['id'] = data['id']
        doc['channelId'] = data['snippet']['channelId']
        doc['title'] = data['snippet']['title']
        doc['desc'] = data['snippet']['description']
        doc['date'] = data['snippet']['publishedAt'][:10]
        doc['view'] = data['statistics']['viewCount']
        doc['like'] = data['statistics']['likeCount']
        # doc['dislike'] = data['statistics']['dislikeCount']
        meta['Video'] = doc

        if 'type' in response.meta and response.meta['type'] == 'Video' :
            query = {
                'key': YT_APIKEY,
                'part': 'snippet, statistics',
                'id': data['snippet']['channelId']
            }
            query_str = parse.urlencode(query)
            yield scrapy.Request(
                    f'{YT_API_LINK}channels?{query_str}', 
                    self.get_meta_channel,
                    meta={'type': 'Video','id': response.meta['id'], 'video_item':doc},
                    dont_filter=True
                    )
        else :
            yield doc
            query = {
                'key': YT_APIKEY,
                'part': 'snippet, id, replies',
                'maxResults': 100,
                'videoId': data['id']
            }
            query_str = parse.urlencode(query)
            yield scrapy.Request(f'{YT_API_LINK}commentThreads?{query_str}', self.parse_video, meta=meta)

    def parse_playlist(self, response):
        data = json.loads(response.body)
        meta = response.meta
        if 'nextPageToken' in data :
            parsed_query = dict(parse.parse_qsl(response.url[response.url.find('?') + 1:]))
            parsed_query['pageToken'] = data['nextPageToken']
            query_str = parse.urlencode(parsed_query)
            yield scrapy.Request(f'{YT_API_LINK}playlistItems?{query_str}', self.parse_playlist, meta=meta)

        for video in data['items'] :
            query = {
                'key': YT_APIKEY,
                'part': 'snippet,statistics',
                'id': video['snippet']['resourceId']['videoId']
            }
            query_str = parse.urlencode(query)
            yield scrapy.Request(f'{YT_API_LINK}videos?{query_str}', self.get_meta_video, meta=meta)

    def parse_channel(self, response):
        data = json.loads(response.body)
        for video in data['items'] :
            query = {
                'key': YT_APIKEY,
                'part': 'snippet,statistics',
                'id': video['id']['videoId']
            }
            query_str = parse.urlencode(query)
            yield scrapy.Request(
                    f'{YT_API_LINK}videos?{query_str}', 
                    self.get_meta_video, 
                    meta=response.meta
                  )
        
        if 'nextPageToken' in data :
            parsed_query = dict(parse.parse_qsl(response.url[response.url.find('?') + 1:]))
            parsed_query['pageToken'] = data['nextPageToken']
            query_str = parse.urlencode(parsed_query)
            yield scrapy.Request(
                    f'{YT_API_LINK}search?{query_str}', 
                    self.parse_channel,
                    meta=response.meta
                  )

    def parse_video(self, response) :
        data = json.loads(response.body)
        for comment in data['items'] :
            top_comment = comment['snippet']['topLevelComment']
            doc = YoutubeCommentItem()
            doc['commentId'] = top_comment['id']
            doc['videoId']   = top_comment['snippet']['videoId']
            doc['body']      = top_comment['snippet']['textDisplay']
            doc['date']      = top_comment['snippet']['publishedAt'][:10]
            yield doc
            if comment['snippet']['totalReplyCount'] > 0 :
                for repl in comment['replies']['comments'] :
                    doc = YoutubeCommentItem()
                    doc['commentId'] = repl['id']
                    doc['videoId']   = repl['snippet']['videoId']
                    doc['body']      = repl['snippet']['textDisplay']
                    doc['date']      = repl['snippet']['publishedAt'][:10]
                    yield doc

        if 'nextPageToken' in data :
            parsed_query = dict(parse.parse_qsl(response.url[response.url.find('?') + 1:]))
            parsed_query['pageToken'] = data['nextPageToken']
            query_str = parse.urlencode(parsed_query)
            yield scrapy.Request(f'{YT_API_LINK}commentThreads?{query_str}', self.parse_video, meta=response.meta)
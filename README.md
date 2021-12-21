# 해외 매체 데이터 수집 크롤러

세계 각지의 언론매체, 유튜브, 트위터, 레딧, IMDB, 웹툰 플랫폼 등의 온라인 데이터를 수집하는 크롤러입니다.

## 사전준비 :loudspeaker:

### API Key
언론 매체 크롤러와 Youtube 크롤러, Reddit 크롤러에서는 다음과 같은 상용 API를 사용하고 있습니다.

1. Google Custom Search API
  - 환구시보, BBC Mundo, El Pais 키워드 검색용
  - 10,000 Queries/day
  - [Custom Search JSON API | Programmable Search Engine (google.com)](https://developers.google.com/custom-search/v1/overview?hl=ko)
  - API Key 발급 방법 참조: [[SpringBoot] Google Custom Search API를 이용한 이미지 (velog.io)](https://velog.io/@ayoung0073/springboot-google-custom-search)
2. Youtube Data API
  - Youtube 크롤링용 API
  - 10,000 Queries/day
  - [YouTube | Google Developers](https://developers.google.com/youtube/?hl=ko)
  - API Key 발급 방법 참조: [Youtube API key 발급받기 (velog.io)](https://velog.io/@yhe228/Youtube-API%EB%A5%BC-%EC%9D%B4%EC%9A%A9%ED%95%B4-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EA%B0%80%EC%A0%B8%EC%98%A4%EA%B8%B0)
3. The New York Times Article Search API
  - 뉴욕 타임즈 키워드 검색용
  - 4,000 Queries/day
  - [Article Search | Dev Portal (nytimes.com)](https://developer.nytimes.com/docs/articlesearch-product/1/overview)
4. The Guardian API(Developer)
  - 영국 더 가디언 키워드 검색용
  - 5,000 Queries/day
  - [The Guardian - Open Platform - Get Started](https://open-platform.theguardian.com/access/)
5. Reddit API
  - 레딧의 서브레딧 검색용
  - 1,000 Submission Limit/subreddit
  - [레딧 API 앱 생성](https://antilibrary.org/2352)

생성한 API Key들을 Crawler/apikey.py에 저장하여 사용합니다.

### 패키지

다음 명령어로 필요한 모든 패키지를 설치할 수 있습니다.

```cmd
pip install -r requirements.txt
```

트위터는 API 대신 [Twint](https://github.com/twintproject/twint)를 사용해 데이터를 수집했습니다. Twint는 데이터 수집에 큰 제약이 없다는 것이 장점입니다.

크롤링에 필요한 패키지는 다음과 같습니다.
1. [Twint](https://github.com/twintproject/twint) 설치
  ```cmd
  pip3 install --user --upgrade git+https://github.com/twintproject/twint.git@origin/master#egg=twint
  ```
2. [PRAW(Python Reddit API Wrapper)](https://github.com/praw-dev/praw)
  ```cmd
  pip install praw
  ```
3. [PSAW(Python Pushshift.io API Wrapper)](https://github.com/dmarx/psaw)
  ```cmd
  pip install psaw
  ```


## 사용법 :clipboard:

Control 디렉토리에서 명령어를 실행합니다.

### 기본

```cmd
scrapy crawl [크롤러 이름] [-a [parameter]=[value]]
```

### 1. 언론매체 크롤러

| 크롤러 이름     | 내용                       |
| --------------- | -------------------------- |
| CN_globaltimes  | 중국 환구시보              |
| US_nytimes      | 미국 뉴욕 타임즈           |
| UK_guardian     | 영국 더 가디언             |
| US_latimes      | 미국 LA 타임즈             |
| SG_straitstimes | 싱가포르 스트레이츠 타임즈 |
| JP_asahi        | 일본 아사히 신문           |
| JP_sankei       | 일본 산케이 신문           |
| SA_bbcmundo     | 남미 BBC Mundo             |
| FR_lemonde      | 프랑스 르 몽드             |
| ES_elpais       | 스페인 엘 파이스           |

- Parameters

  1. keywords: 검색 키워드, “,”로 구분하여 여러 개 입력 가능합니다.
  2. begin_date: 검색 기간 시작 날짜 (YYYYMMDD/기본값: 20180101)
  3. end_date: 검색 기간 끝 날짜 (YYYYMMDD/기본값: 20210630)

- Example
환구시보에서 “K-pop”, “BTS”, “EXO” 키워드로 2020년 1월 1일부터 2020년 1월 32일까지의 뉴스 기사 크롤링
  ```cmd
  scrapy crawl CN_globaltimes -a keywords=K-pop,BTS,Exo -a begin_date=20200101 -a end_date=20201231
  ```

### 2. Youtube 크롤러

| 크롤러 이름 | 내용   |
| ----------- | ------ |
| Youtube     | 유튜브 |

- Parameters
  1. channel_ids: 크롤링 대상 채널 ID, 채널 URL에서 UC로 시작하는 부분, “,”로 여러 개 입력 가능합니다.

  2. playlist_ids: 크롤링 대상 재생목록 ID, 재생목록 URL에서 “list=”뒤에 붙는 PL로 시작하는 부분, “,”로 여러 개 입력 가능합니다.
  3. video_ids: 크롤링 대상 영상 ID, 영상 URL에서 “v=”뒤에 붙는 부분, “,”로 여러 개 입력 가능합니다.

- 예제
  1. 채널(https://www.youtube.com/channel/UCfpaSruWW3S4dibonKXENjA)의 전체 영상의 댓글을 크롤링
    ```cmd
    scrapy crawl Youtube -a channel_ids=UChhOtjq-3QyyLmP2jv9amrg, UCfpaSruWW3S4dibonKXENjA
    ```
  2. 재생목록(https://www.youtube.com/playlist?list=PLcckjnQV0VqCAyF-tfveJDUfJ1DfS-IZj)의 전체 영상의 댓글 크롤링
    ```cmd
    scrapy crawl Youtube -a playlist_ids=PLcckjnQV0VqCAyF-tfveJDUfJ1DfS-IZj
    ```
  3. 영상(https://www.youtube.com/watch?v=3P1CnWI62Ik)의 전체 댓글 크롤링
    ```cmd
    scrapy crawl Youtube video_ids=3P1CnWI62Ik
    ```

### 3. 트위터 크롤러

| 크롤러 이름     | 내용                           |
| --------------- | ------------------------------ |
| twitter_user    | 트위터 채널의 트윗 검색        |
| twitter_user_rt | 트위터 채널에 대한 RT멘션 검색 |
| twitter_geo     | 트위터 권역별 키워드 검색      |

트위터는 권역별 허브채널이 존재하는 경우 twitter_user와 twitter_user_rt를 이용해 트윗 데이터를 수집할 수 있습니다.

각 권역별 허브채널은 다음과 같습니다.

| 권역                     | 허브채널                                                  |
| ------------------------ | --------------------------------------------------------- |
| North_America            | allkpop, soompi, iconickdramas, kdramafairy, kdramaworlld |
| South_America            | 없음                                                      |
| Japan                    | 없음                                                      |
| Southeast_Asia           | infodrakor_id, kdrama_menfess, korcinema_fess             |
| India                    | 없음                                                      |
| Middle_East              | 없음                                                      |
| Europe                   | Spain_Kpop_, Kpop_Project_SP                              |
| Republic_of_South_Africa | 없음                                                      |
| Austrailia               | 없음                                                      |

마땅한 허브채널이 찾을 수 없는 경우 twitter_geo를 이용해 트윗 데이터를 수집하거나 users 파라미터를 사용하여 유저의 트윗을 수집할 수 있습니다.

- 트위터 채널 크롤러(twitter_user) Parameters
  1. users: 해당 유저의 트윗을 수집합니다. “,”로 구분하여 여러 개 입력 가능합니다. (기본값: allkpop)
  2. geo: 미리 조사한 권역별 허브채널의 트윗을 수집합니다. North_America, Southeast_Asia, Europe의 3가지 권역만 가능합니다. users와 geo를 함께 입력하면 geo 기준으로 크롤링을 수행합니다.
  3. begin_date: 검색 기간 시작 날짜 (YYYYMMDD)
  4. end_date: 검색 기간 끝 날짜 (YYYYMMDD)

- 트위터 채널 RT멘션 크롤러(twitter_user_rt) Parameters
  1. users: 해당 유저의 트윗에 대한 RT멘션을 수집합니다. “,”로 구분하여 여러 개 입력 가능 (기본값: allkpop)
  2. geo: 미리 조사한 권역별 허브채널의 트윗을 수집합니다. North_America, Southeast_Asia, Europe의 3가지 권역만 가능합니다. users와 geo를 함께 입력하면 geo 기준으로 크롤링을 수행합니다.
  3. begin_date: 검색 기간 시작 날짜 (YYYYMMDD)
  4. end_date: 검색 기간 끝 날짜 (YYYYMMDD)

- 권역별 키워드 검색 크롤러(twitter_geo) Parameters
  1. keywords: 해당 키워드가 포함된 트윗을 수집합니다. (기본값: BTS)
  2. geo: 권역을 필터링해서 검색합니다. (기본값:North_America)
  ![geo_neo](https://user-images.githubusercontent.com/41911523/132099751-cc84ee2e-bdf4-4a6d-8c86-39a5e2b153a1.png)
  3. begin_date: 검색 기간 시작 날짜 (기본값: 20180101)
  4. end_date: 검색 기간 끝 날짜 (기본값: 20180131)
  
- 예제
  1. allkpop, soompi의 트윗을 2018년 1월 1일부터 2021년 6월 30일까지 크롤링
    ```cmd
    scrapy crawl twitter_user -a users=allkpop,soompi -a begin_date=20180101 -a end_date=20210630
    ```
  2. 북미권역 허브 채널의 RT 멘션을 크롤링
    ```cmd
    scrapy crawl twitter_user_rt -a geo=North_America
    ```
  3. 동남아시아 권역에서 BTS, TWICE 키워드를 포함한 2020년 1월 1일부터 2020년 6월 30일까지의 트윗을 크롤링
    ```cmd
    scrapy crawl twitter_geo -a keywords=BTS,TWICE -a geo=Southeast_Asia -a begin_date=20200101 -a end_date=20200630
    
### 4. 레딧 크롤러

| 크롤러 이름 | 내용 |
| ----------- | ---- |
| reddit      | 레딧 |

- 레딧 크롤러 Parameters
  1. subreddit: 크롤링 대상 서브레딧 이름입니다.(기본값:kpop)
  2. begin_date: 검색 기간 시작 날짜 (YYYYMMDD/기본값: 20180101)
  3. end_date: 검색 기간 끝 날짜 (YYYYMMDD/기본값: 20180105)
  4. keywords: 검색할 키워드, “,”로 구분하여 여러 개 입력 가능합니다. 미입력시 서브레딧의 모든 포스트를 수집합니다.
  
- 예제
  1. 기간내 KDRAMA 서브레딧의 모든 포스트 수집
    ```cmd
    scrapy crawl reddit -a subreddit=KDRAMA -a begin_date=20200101 -a end_date=20200630
    ```
  2. 기간내 kpop 서브레딧의 BTS, TWICE 키워드가 포함된 포스트 수집
    ```cmd
    scrapy crawl reddit -a subreddit=kpop -a begin_date=20200101 -a end_date=20200630 -a keywords=BTS,TWICE
    ```

### 5. IMDB 크롤러

| 크롤러 이름 | 내용             |
| ----------- | ---------------- |
| IMDb        | IMDb 영화 감상평 |

- Parameters
  1. ids: IMDb의 자체 영화 ID입니다. “,”로 구분하여 여러 개 입력 가능합니다. https://www.imdb.com/title/tt3967856같은 URL에서 tt뒤에 붙어있는 3967856이 ID입니다.
  2. urls: IMDb 영화 소개 페이지 URL입니다. “,”로 구분하여 여러 개 입력 가능합니다.

- 예제
  1. urls를 이용하여 영화 리뷰 수집
  ```cmd
  scrapy crawl imdb -a urls=https://www.imdb.com/title/tt6751668/?ref_=nv_sr_srsg_0
  ```
  2. ids를 이용하여 영화 리뷰 수집(위 방법과 완전히 동일한 결과를 얻을 수 있습니다.)
  ```cmd
  scrapy crawl imdb -a ids=6751668
  ```
  
### 6. 웹툰 크롤러

| 크롤러 이름   | 내용             |
| ------------- | ---------------- |
| webtoon_naver | 해외 네이버 웹툰 |
| webtoon_tapas | Tapas 웹툰       |

- Parameters
  1. webtoons: 웹툰 소개 페이지의 URL입니다. Tapas.io의 경우 마지막이 /info로 끝나는 URL이 소개 페이지입니다.
- 예제
  1. Webtoons.com 크롤링
  ```cmd
  scrapy crawl webtoon_naver -a webtoons=https://www.webtoons.com/en/sports/the-boxer/list?title_no=2027
  ```
  2. Tapas.io 크롤링
  ```cmd
  scrapy crawl webtoon_tapas -a webtoons=https://tapas.io/series/tbate-comic/info
  ```

### 7. 기타
- 작동 정지
  1. Ctrl+C를 한번 누르시면 Interrupt Signal을 받은 크롤러가 중단 모드로 들어갑니다. 현재 큐에 있는 문서들은 모두 처리하고 중단하기 때문에 정지까지 약간의 시간이 걸립니다.
  2. Ctrl+C를 두번 누르시면 크롤러가 즉시 중단하게 됩니다. 큐에 있던 문서들은 모두 취소되기 때문에 DB에 저장되지 않습니다.

- 로그 파일
  1. Log 디렉토리에 크롤러의 실행 로그가 모두 저장됩니다.

- 추가 서버 저장 옵션
  1. -o [output file name]: 크롤링 결과를 DB뿐만 아니라 로컬에도 저장합니다.
  2. csv, json, xml을 지원합니다.
  3. 언론매체를 제외한 크롤러들은 크롤링 결과물이 여러 종류로 구성되어 있기 때문에 크롤링하기 때문에 csv로 저장이 불가능합니다.
  4. 예제
  ```cmd
   scrapy crawl CN_globaltimes -o output.csv
  ```
  5. csv파일은 엑셀에서 데이터-텍스트/csv가져오기에서 파일 선택후 파일 원본을
  "949:한국어"에서 65001:유니코드(UTF-8)로 바꾼 뒤 로드하면 정상적인 데이터로 열립니다.

# 퓨어짐 부산 검색 관리

공개 홈페이지: https://puregym-busan.github.io/

## 구성

- 메인, 시설 사진, 수업·첫 방문 안내의 세 URL을 사이트맵에 포함한다.
- 제목·설명·canonical·공유 이미지와 HealthClub, WebSite, WebPage, BreadcrumbList, Service 데이터를 제공한다.
- FAQ 구조화 데이터는 안내 페이지에 보이는 답변을 그대로 읽어 생성한다. FAQ 리치 결과의 노출을 보장하지 않는다.
- robots.txt는 공개 페이지 수집을 허용한다. 이전 비교 시안은 noindex로 보존한다.
- llms.txt는 보조 요약이다. 검색 등록이나 AI 추천을 보장하는 특별한 파일로 취급하지 않는다.
- Google·네이버 소유권 확인 메타는 index.html에서 제거하지 않는다.

## 정보 갱신

주소·전화·주차·예약 조건이 바뀌면 index.html, spaces.html, guide.html, scripts/search.py와 CONTENT_SOURCES.md를 함께 확인한다. 시간표·요금·휴무는 네이버의 최신 안내로 연결한다. 운영 시간·좌표·자격·평점 등 확인되지 않은 항목은 임의로 추가하지 않는다.

## 검증과 운영

`python3 -m unittest discover -s tests`와 `python3 scripts/package.py`로 배포 전 메타 중복, canonical, 검색 차단, FAQ 일치, 업체 정보와 사이트맵을 검증한다. 공개 서버 반영 후 HTTP 응답과 파일 해시를 확인한다.

소유권 확인 및 사이트맵 제출은 수집을 요청하는 단계다. 실제 색인·노출·순위·AI 인용은 별도 확인해야 한다. 제출 뒤에는 Search Console과 서치어드바이저에서 수집 및 색인 상태를 확인하고, 누락된 URL에 오류가 있는 경우 수정한다. 동일한 URL을 반복 요청해 순위를 올리려 하지 않는다.

## 공식 참고

- [Google AI 검색 기능과 웹사이트](https://developers.google.com/search/docs/appearance/ai-features)
- [Google 지역 업체 구조화 데이터](https://developers.google.com/search/docs/appearance/structured-data/local-business)
- [Google 사이트맵](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [네이버 robots.txt](https://searchadvisor.naver.com/guide/seo-basic-robots)
- [네이버 사이트맵 제출](https://searchadvisor.naver.com/guide/request-feed)
- [OpenAI 검색 봇](https://developers.openai.com/api/docs/bots)
- [Perplexity 검색 봇](https://docs.perplexity.ai/docs/resources/perplexity-crawlers)

등록 결과와 화면 증거는 비공개 qa/에 보관한다.

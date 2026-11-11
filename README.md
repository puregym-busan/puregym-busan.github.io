# PURE Wellness Center · Busan

퓨어짐 부산의 웹사이트 디자인 검토를 위한 세 가지 시안입니다.

| 페이지 | 방향 |
| --- | --- |
| `index.html` | 세 시안을 비교하는 첫 화면 |
| `concept-a.html` | The Wellness House — 크림색 바탕과 시설 사진을 중심으로 한 차분한 구성 |
| `concept-b.html` | After the Effort — 트레이닝룸의 존재감과 운동 후 휴식을 강조한 구성 |
| `concept-c.html` | The Daily Ritual — 요가·바레부터 트레이닝과 회복까지 소개하는 매거진 형식 |

HTML, CSS, JavaScript만 사용하는 정적 사이트입니다. 각 시안에서 프로그램, 시설 사진, 방문 안내를 확인할 수 있으며 문의는 기존 네이버 플레이스·Instagram·전화로 연결됩니다.

## 사진과 정보

시설 사진은 퓨어짐 부산 네이버 플레이스의 업체 등록 사진을 사용했습니다. 생성 이미지는 사용하지 않았습니다. 사진 원본 주소와 SHA-256 해시는 `ASSET_SOURCES.json`에 기록했습니다.

- [네이버 플레이스](https://m.place.naver.com/place/2096351642/home)
- [Instagram](https://www.instagram.com/puregym.busan/)

확인 기준일은 2026년 11월 11일입니다. 변동될 수 있는 가격, 운영 시간, 수업 일정은 원문 채널에서 확인하도록 연결했습니다.

## 게시와 검토

프로젝트 소스는 이 저장소의 `main` 브랜치에서 관리합니다. `main`에 push하면 GitHub Actions가 `scripts/package.py`를 실행해 `publish/`에 게시 파일 15개를 만들고 GitHub Pages에 배포합니다. 게시용 폴더에서는 HTML과 사진을 같은 경로에 둡니다. GitHub Pages의 Source 설정은 `GitHub Actions`입니다.

```sh
python3 scripts/package.py
git add <수정한 파일>
git commit -m "Update website proposals"
git push origin main
```

`scripts/deploy.py`는 커밋된 소스와 로컬 패키징을 확인한 뒤 `main`을 push하는 보조 명령입니다. QA, 비공개 참고 자료, 생성된 `publish/` 및 ZIP 파일은 Git 추적과 Pages 게시에서 제외합니다. 배포 완료 여부는 저장소 Actions의 `Deploy GitHub Pages` 실행에서 확인합니다.

현재는 디자인 검토 단계이며 각 페이지에 `noindex,nofollow`를 지정했습니다. 최종 안을 정한 뒤 프로그램별 안내와 운영 정보를 확정하고 정식 홈페이지로 정리할 수 있습니다.

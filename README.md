# PURE Wellness Center · Busan

퓨어짐 부산의 운동·회복 공간과 그룹수업을 소개하는 정적 웹사이트입니다. 선택된 A안을 기본 홈페이지로 사용합니다.

| 페이지 | 방향 |
| --- | --- |
| `index.html` | 기본 홈페이지 — 선택된 A안에 시설 사진과 방문·예약 안내 보강 |
| `proposals.html` | 이전 세 가지 디자인 비교 화면 |
| `concept-a.html` | 기존 공유 주소 호환용 — 쿼리·앵커를 유지해 index.html로 이동 |
| `concept-b.html` | After the Effort — 트레이닝룸의 존재감과 운동 후 휴식을 강조한 구성 |
| `concept-c.html` | The Daily Ritual — 요가·바레부터 트레이닝과 회복까지 소개하는 매거진 형식 |
| `spaces.html` | 메인 홈페이지와 연결되는 시설 둘러보기 — 공간별 사진 20장과 확대 보기 |

HTML, CSS, JavaScript만 사용하는 정적 사이트입니다. 메인에서 프로그램, 시설 사진 13장, 첫 방문 및 주차 안내를 확인할 수 있으며 문의는 기존 네이버 플레이스·Instagram·전화로 연결됩니다.

## 사진과 정보

시설 사진은 네이버 플레이스의 업체 등록 사진과 코치가 제공한 실제 시설 사진을 사용했습니다. A안과 시설 둘러보기에는 2026년 11월 12일 전달받은 사진 중 20장을 선정해 적용했습니다. 소셜 사우나와 콜드 플런지를 실제로 이용하는 모습도 포함합니다. 생성 이미지는 사용하지 않았습니다. 사진의 출처, 변환 내용과 SHA-256 해시는 `ASSET_SOURCES.json`에 기록했습니다.

- [네이버 플레이스](https://m.place.naver.com/place/2096351642/home)
- [Instagram](https://www.instagram.com/puregym.busan/)

확인 기준일은 2026년 11월 12일입니다. 네이버의 예약 상품·소식·시설 정보와 Instagram 프로필을 확인했습니다. 프로그램별 1일 이용권, 무료 상담, 남천역 접근 및 주차 안내를 메인에 반영했습니다. 변동될 수 있는 가격, 운영 시간, 수업 일정은 원문 채널에서 확인하도록 연결했습니다. 확인 근거와 유지보수 범위는 `CONTENT_SOURCES.md`에 정리했습니다.

## 게시와 검토

프로젝트 소스는 이 저장소의 `main` 브랜치에서 관리합니다. `main`에 push하면 GitHub Actions가 `scripts/package.py`를 실행해 `publish/`에 게시 파일을 만들고 GitHub Pages에 배포합니다. 게시용 폴더에서는 HTML과 사진을 같은 경로에 둡니다. GitHub Pages의 Source 설정은 `GitHub Actions`입니다.

```sh
python3 scripts/package.py
git add <수정한 파일>
git commit -m "Update PureGym website"
git push origin main
```

`scripts/deploy.py`는 커밋된 소스와 로컬 패키징을 확인한 뒤 `main`을 push하는 보조 명령입니다. QA, 비공개 참고 자료, 생성된 `publish/` 및 ZIP 파일은 Git 추적과 Pages 게시에서 제외합니다. 배포 완료 여부는 저장소 Actions의 `Deploy GitHub Pages` 실행에서 확인합니다.

메인과 시설 페이지에는 기본 공개 주소를 canonical로 지정했습니다. 기존 시안 비교 및 B·C안은 `noindex,nofollow`로 보존하며 홈페이지 메뉴에는 노출하지 않습니다. 기존 `concept-a.html` 공유 링크는 기본 홈페이지로 이동합니다.

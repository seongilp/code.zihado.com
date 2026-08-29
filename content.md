# 100개 서비스 만들기 프로젝트 🚀

> 1년 동안 100개의 서비스를 만드는 프로젝트 — 지금까지 67개

혼자서, 그리고 AI와 짝을 이뤄 만든 프로젝트 모음입니다.
웹 서비스부터 모바일 앱, 데스크탑 도구, 자동화 봇, 보안 인프라까지 — 거창하지 않아도 **'직접 굴러가는 것'을 만드는 게 코딩의 시작**입니다.

각 프로젝트마다 **"무엇을 만들었나"**와 **"여러분이 배울 수 있는 것"**을 정리했어요.

---

## 한눈에 보기

| 분야 | 프로젝트 수 | 대표작 |
|------|:---:|------|
| 🌐 웹 서비스·대시보드 | 28 | 국회 감시 대시보드, 법령 검색, 실시간 같이보기(Unflix) |
| 🤖 자동화·봇·스크래핑 | 9 | 출석 자동화 봇, 재입고 알림, 로또 자동 구매 |
| 📱 모바일 앱 | 3 | 사진 정리 앱(루멘), 암기 앱(안키요) |
| 🖥️ 데스크탑·네이티브 도구 | 13 | 파일 검색 CLI, 한글문서 Spotlight 검색 |
| ⌨️ CLI·금융 | 1 | 토스증권 CLI |
| 🔐 보안·인프라·데이터 | 13 | NAS 웹 콘솔(Nimbo), 커스텀 NAS OS(Zen), 컨테이너 하드닝 |

---

## 🌐 웹 서비스 · 대시보드

> 공개 데이터를 가져와 누구나 볼 수 있는 웹페이지로 만든 것들. 대부분 Cloudflare로 무료 배포되어 실제로 돌아갑니다.

### 국회 의정활동 감시 대시보드 · `asm.zihado.com`
대한민국 제22대 국회의원 300명의 의정활동을 실시간으로 추적하는 대시보드.
- 의원 검색·프로필, 계류 의안·표결 결과를 의원별 명단으로 확인
- 위원회·국회 일정과 핵심 지표 대시보드
- **스택**: Nuxt 4 · Tailwind v4 · shadcn-vue · Cloudflare Workers/KV · 국회 Open API
- **🎓 배울 수 있는 것**: 공개 API로 대시보드 만들기 / 3단 엣지 캐싱으로 빠르게 보여주기

### DART 전자공시 조회 · `dart`
금융감독원 전자공시(OpenDART) 기반 기업 공시·재무 조회 + 국민연금 매매 추적.
- 공시·재무제표 조회, 국민연금 순매수 랭킹과 연속 매수/매도 신호
- ⌘K 커맨드 팔레트, 즐겨찾기
- **스택**: Svelte 5 · Tailwind v4 · Cloudflare Pages Functions · OpenDART API
- **🎓 배울 수 있는 것**: Pages Functions로 API 안전하게 프록시 / 다층 캐싱 전략

### ETF 닥터 · `etf-doctor`
국내·미국 ETF의 순매매 흐름과 추정 iNAV를 실시간으로 보여주는 대시보드.
- 오늘 많이 산/판 ETF, 해외형 ETF 다음날 시초가 방향 예측, 최대 4개 비교
- **스택**: Nuxt 4 · Tailwind v4 · Nitro Server API · Cloudflare Pages
- **🎓 배울 수 있는 것**: 실데이터/메타데이터 분리 운영 / prerender로 첫 화면 즉시 띄우기

### 법령 초고속 검색 · `law.zihado.com`
대한민국 법령·판례·행정규칙 약 54만 조문을 조문 단위로 즉시 검색.
- 한국어 토크나이저 기반 instant-search, 패싯 필터, ⌘K 팔레트
- **스택**: Typesense · Python 인덱서 · React · Cloudflare Pages/Workers/Tunnel
- **🎓 배울 수 있는 것**: 전문검색 시스템 구축 / Cloudflare Tunnel로 내 서버를 안전하게 연결

### 북웜 (독서 기록장) · `bookworm`
책에서 만난 좋은 문장을 모으고 나만의 책장을 관리하는 웹앱.
- 제목 검색으로 표지·저자 자동 채우기, 문장 수집·태그·통계
- **스택**: Nuxt 3 · Cloudflare D1(SQLite) · Zod
- **🎓 배울 수 있는 것**: Nuxt 한 앱에 화면+API 두기 / 도서 API 여러 개 이어 호출하기

### 아파트 실거래가 조회 · `landman`
국토교통부 실거래가 API로 아파트 매매를 조회하는 프로토타입.
- 지역·년월 선택 조회, XML→JSON 변환·통계, k6 성능 테스트
- **스택**: Next.js 16 · TypeScript · fast-xml-parser · k6
- **🎓 배울 수 있는 것**: 공공데이터포털 API 연동·CORS 처리 / k6로 부하 테스트

### 유튜브 댓글 라이브챗 · `yaho.rescene.co`
유튜브 채널의 댓글을 스크롤 라이브 채팅처럼 재생하는 웹앱.
- 댓글을 '실시간 채팅' 흐름으로 재생(속도·정렬·반복·시어터 모드)
- **스택**: Next.js 16 · React 19 · Cloudflare Workers · OpenNext
- **🎓 배울 수 있는 것**: YouTube API 연동 / ISR+KV+Cache 캐시 전략

### 실사 3D 세계 도시 투어 · `webgl/webgl-tour`
구글 포토리얼 3D 타일로 런던·파리·서울·도쿄를 드론처럼 날아다니는 웹앱.
- 랜드마크 시네마틱 드론 투어, 장소 검색·루트 투어, 위키 사진·요약·거리뷰 카드
- **스택**: 바닐라 JS · Google Photorealistic 3D Tiles · PWA · Cloudflare Pages
- **🎓 배울 수 있는 것**: 3D 지도 카메라 연출 / 빌드 없이 PWA 설치형 웹앱 만들기

### WebGL 비주얼 데모 모음 · `particla`
입자·유체·블랙홀까지 11가지 그래픽 시뮬레이션 데모집.
- GPU 파티클(100만 개), 실시간 유체, 광선 추적 블랙홀을 탭으로 감상
- **스택**: WebGL2 · Canvas 2D · 바닐라 JS (의존성 0) · GitHub Pages
- **🎓 배울 수 있는 것**: 그래픽 알고리즘 원리 / GPU 텍스처 핑퐁 최적화

### 2026 월드컵 경기 일정·결과 · `worldcup`
2026 FIFA 월드컵 일정·결과·대진표를 한눈에 보는 대시보드.
- 매시간 자동 갱신, 토너먼트 대진표·조별 순위 실시간 계산
- **스택**: Next.js 16 · TypeScript · GitHub Actions · GitHub Pages
- **🎓 배울 수 있는 것**: SSG로 서버 없이 배포 / Actions 크론으로 데이터 자동 갱신

### 광고 없는 한국 지도 · `openmap`
오픈스트리트맵 기반 광고 없는 한국 지도 — 검색·길찾기·즐겨찾기.
- MapLibre GL 지도, 한국어 장소 검색(Nominatim), 자동차 길찾기(OSRM)
- **스택**: Next.js 16 · MapLibre GL · OpenStreetMap
- **🎓 배울 수 있는 것**: WebGL 지도 렌더링 / 공개 API 프록시 패턴

### MeshScope (메시 네트워크 대시보드) · `mesh`
Meshtastic 무선 메시 네트워크 실시간 모니터링 대시보드.
- MQTT 패킷을 지도·피드·그래프·텔레메트리 4가지 뷰로 시각화
- **스택**: React · TypeScript · MapLibre GL · MQTT/WebSocket · Protobuf
- **🎓 배울 수 있는 것**: 실시간 스트리밍 아키텍처 / 지도·차트 라이브러리 통합

### Unflix (실시간 같이보기) · `youflix`
Cloudflare 인프라만으로 만든 실시간 공동시청 서비스 — 내 영상·화면을 링크 하나로 같이 보기.
- 영상 파일·화면·카메라 스트리밍, 룸 프레즌스·실시간 채팅, 시크릿 보호 프록시
- **스택**: Cloudflare Workers · Durable Objects · Realtime SFU(WebRTC) · TypeScript
- **🎓 배울 수 있는 것**: WebRTC+WebSocket 실시간 아키텍처 / 엣지만으로 1:N 미디어 팬아웃

### weblog (브라우저 로그 분석기) · `weblog`
로그·CSV·엑셀 100만 행을 브라우저 안 DuckDB로 즉시 SQL 분석 — 데이터가 서버로 안 나감.
- 100만 행 1.5초 적재·밀리초 집계, SQL REPL, 가상 스크롤, OPFS 영속 저장
- **스택**: React 19 · DuckDB-Wasm · Vite · Tailwind v4 · SheetJS
- **🎓 배울 수 있는 것**: WASM 데이터베이스를 브라우저에서 돌리기 / Web Worker로 UI 성능 지키기

### 웹 루멘 (WASM 사진 뷰어) · `wasm`
폴더를 끌어다 놓으면 WASM이 썸네일을 만들어 브라우저에 저장하는 사진 정리 앱.
- AssemblyScript WASM 썸네일 엔진 + Worker 풀, OPFS 저장, 중복 찾기·얼굴 인식
- **스택**: AssemblyScript(WASM) · React 19 · OPFS · MediaPipe · Vitest
- **🎓 배울 수 있는 것**: WASM 모듈 직접 만들기 / OPFS로 서버 없는 영속 저장

### 10만 파티클 플레이그라운드 · `pixijs/work1`
10만 개 파티클이 마우스에 실시간 반응하는 인터랙티브 그래픽 데모.
- 끌림·소용돌이·중력·반발·노이즈 흐름장 5가지 모드, 클릭 폭발
- **스택**: PixiJS v8 · Vite · 바닐라 JS
- **🎓 배울 수 있는 것**: WebGL로 대량 오브젝트 60fps 렌더링 / 힘 계산 모듈 설계

### MeshKR 뷰어 (메시 네트워크 채팅뷰어) · `heltec/meshkr-viewer`
Meshtastic 메시 네트워크 트래픽을 Discord 스타일 채팅으로 실시간 구경하는 단일 파일 뷰어.
- KR/US/EU_868/TW/JP 지역 탭 전환, 패킷 복호화 후 채팅·이벤트 라인으로 표시, packet id 기준 중복 제거
- **스택**: Python(stdlib http.server) · paho-mqtt · Meshtastic Protobuf · uv
- **🎓 배울 수 있는 것**: uv 인라인 의존성 스크립트로 설치 없는 도구 만들기 / MQTT 복호화 파이프라인 설계

### IVE 팬덤 허브 (라이브챗·리스크·피드) · `ive.unflix.tv`
유튜브 댓글 라이브챗부터 커뮤니티 피드 수집, OSINT 스타일 리스크 인텔리전스까지 갖춘 K-pop 그룹 전용 대시보드.
- 댓글 라이브챗 재생, 네이버뉴스·디시·인스타·다음·네이트판 피드 애그리게이터, 멤버별 감정·키워드 리스크 분석
- **스택**: Next.js 16 · React 19 · Cloudflare Workers/KV(OpenNext) · YouTube Data API
- **🎓 배울 수 있는 것**: 이종 소스를 하나의 피드로 합치는 애그리게이터 설계 / 어댑터별 실패 격리 테스트

### 궤적. (구글 타임라인 뷰어) · `google/gps`
구글 타임라인·Takeout 위치 데이터를 서버 전송 없이 브라우저에서만 파싱해, 수년치 흔적을 한판 히트맵으로 탐색하는 개인 위치 기록 뷰어.
- 타임라인 JSON 4종 + 지도 활동기록(HTML)·사진 EXIF·저장 장소까지 Takeout 폴더 전체 스캔, 히트맵·이동 선 '한판 보기'에서 지도를 클릭하면 그 지점을 언제 지나갔는지 날짜별로 표시
- **스택**: Next.js 16 · TypeScript · Leaflet + leaflet.heat · Dexie(IndexedDB) · fflate
- **🎓 배울 수 있는 것**: 여러 데이터 포맷(JSON·HTML·EXIF) 방어적 파싱 전략 / 브라우저만으로 수만 좌표를 다루는 로컬 퍼스트 설계


### 히라가나 7일 학습 · `japanese`
일본어 히라가나를 7일에 나눠 익히는 원고용지 스타일 학습 페이지.
- 46자를 하루치 분량으로 쪼갠 7일 커리큘럼
- 원고용지 칸에 맞춘 획순·모양 연습, 인쇄해서 손으로 써도 그대로 쓰임
- **스택**: HTML · CSS · GitHub Pages
- **🎓 배울 수 있는 것**: 학습 부담을 낮추는 '하루치' 설계 / 파일 하나로 끝나는 정적 페이지 무료 배포

### Agentic Engineering Studio 소개 페이지 · `agentic-engineering`
AI 에이전트를 개발 조직처럼 운영하는 1인 스튜디오의 소개 페이지.
- 제품 개발·업무 자동화·인프라 구축을 한 사람이 기획부터 배포까지 책임진다는 메시지를 에디토리얼 레이아웃으로 전달
- 개인 블로그(seongilp.github.io) 안에 회사 소개 서브 경로(`/company/`)로 배치
- **스택**: Jekyll · HTML/CSS · GitHub Pages
- **🎓 배울 수 있는 것**: 1인 기업 랜딩 페이지 카피·레이아웃 설계 / 기존 블로그 저장소에 정적 서브 페이지 얹어 배포하기

### KiiiKiii LIVE (유튜브 댓글 라이브챗 + 팬덤 허브) · `kiki.unflix.tv`
유튜브 채널 댓글을 라이브 채팅처럼 재생하고, 뉴스·커뮤니티 피드부터 OSINT 리스크 모니터링까지 갖춘 K-pop 그룹 팬덤 허브.
- 유튜브 댓글을 실시간 채팅처럼 재생(속도·정렬·시어터 모드), 유튜브·네이버뉴스·다음·디시·네이트판·인스타그램 피드 애그리게이터
- 2시간 간격 스냅샷으로 멤버별 위협도·감성 추이를 추적하는 리스크 인텔리전스 뷰
- **스택**: Next.js 16 · React 19 · Cloudflare Workers(OpenNext) · Cloudflare D1 · YouTube Data API
- **🎓 배울 수 있는 것**: 이종 소스를 하나의 피드로 합치는 애그리게이터 설계 / 베이스라인 대비 이탈만 알림으로 보내는 이상탐지 패턴

### Mini Seoul 3D (수도권 전철 3D 지도) · `subway`
수도권 전철 24개 노선을 3D 지도 위에 올려 열차가 실제 노선을 따라 움직이는 걸 실시간으로 보여주는 웹 모형.
- 24개 노선·634개 역·32개 운행 경로를 실좌표 기반으로 렌더링, 배차 간격·시간대별 밀도를 반영한 열차 생성·보간 이동
- 낮/밤 스타일 전환, 지하 구간 강조, 재생 속도 조절(1x~15x)
- **스택**: MapLibre GL JS · Three.js · TypeScript · Vite
- **🎓 배울 수 있는 것**: 지리 좌표 보간으로 움직이는 오브젝트 표현하기 / 실제 운행 데이터를 시뮬레이션 파라미터로 바꾸는 감각

### My Timeline (개인 이동 기록 지도) · `timeline`
지난 몇 년간의 내 이동을 지도 위에 그리는 로컬 도구 — 위치 데이터는 브라우저 밖으로 나가지 않는다.
- Apple 사진 GPS·구글 타임라인 Takeout 데이터를 브라우저에서만 파싱해 지도에 렌더링, 연도별 필터·재생 중 카메라 추적
- PhotoKit으로 촬영 시각·GPS 좌표만 추출하고 사진 원본은 읽지 않는 프라이버시 우선 설계
- **스택**: React 19 · deck.gl · MapLibre GL · Vite · Swift(PhotoKit)
- **🎓 배울 수 있는 것**: 서버 전송 없이 브라우저에서만 개인 데이터를 처리하는 로컬 퍼스트 설계 / deck.gl로 대용량 좌표 데이터 렌더링

### 니혼수첩 (일본 여행 가이드) · `japan_tour`
한국인을 위한 일본 여행 가이드 — 도쿄·오사카 등 대도시와 인근 소도시를 엮은 3박4일·4박5일 코스 정리.
- 도쿄·나고야·오사카·후쿠오카·삿포로 5개 대도시와 인근 소도시를 엮은 여행 코스, 코스 상세 페이지의 일정별 히어로·연결 동선
- 여행 준비물 체크리스트 제공
- **스택**: Next.js 16 · React 19 · Tailwind CSS v4 · TypeScript
- **🎓 배울 수 있는 것**: 반복되는 콘텐츠를 컴포넌트로 구조화하기 / 카드 비율·그라디언트 같은 디테일을 반복 다듬어 가독성 끌어올리기

### 경로 위의 싼 주유소 · `datalab`
출발지에서 목적지까지 가는 경로 위에서, 우회 기름값까지 계산해 실제로 가장 싸게 넣을 수 있는 주유소를 찾는 지도.
- 리터당 가격이 아니라 '주유비 + 우회 주행 기름값'의 합으로 순위를 매김
- 오피넷 API로 매일 새벽 전국 주유소 가격·좌표를 수집해 SQLite에 적재, 지도·목록 조회는 저장소만 읽어 즉시 응답
- **스택**: Next.js · SQLite · MapLibre GL · OSRM · 오피넷 공공데이터 API
- **🎓 배울 수 있는 것**: 하루 단위로만 바뀌는 데이터는 배치로 미리 채워두고 서빙 시점엔 저장소만 읽기 / KATEC 좌표계를 WGS84로 변환해 지도에 얹는 법

### 전국 실시간 교통량 지도 · `doro`
한국도로공사 공공데이터를 OpenStreetMap 실제 도로 선형 위에 구간별로 그리는 실시간 고속도로 소통 지도.
- 전국 고속도로 구간을 평균 속도에 따라 색·굵기로 표시, 노선·방향·혼잡도 필터, 1분 주기 자동 갱신
- 위경도 없는 콘존 데이터를 Overpass API 도로 선형에 Viterbi로 스냅해 1,483개(94%) 구간을 실제 도로 모양으로 복원
- **스택**: Next.js (ISR) · 한국도로공사 공공데이터 API · OpenStreetMap/Overpass API · Viterbi 알고리즘
- **🎓 배울 수 있는 것**: 이름만 있고 좌표가 없는 데이터를 실제 지도 위에 복원하는 법 / 매분 바뀌는 값만 골라 보내는 계층별 캐시 전략

### 공영경기 데이터 수집·AI 예측 · `horse`
경마·경륜·경정 공공데이터 182종을 전량 수집해 parquet+DuckDB로 적재하고 예측 모델을 붙인 파이프라인.
- 공공데이터포털 오픈API 182종을 수집해 DuckDB 192테이블·1,838만 행으로 적재
- 종목별 조건부 로짓 + 부스팅 앙상블로 과거 경주 예측·백테스트, 켈리 베팅 시뮬레이션
- **스택**: Python · DuckDB/parquet · FastAPI · Nuxt 4 · 공공데이터포털 API
- **🎓 배울 수 있는 것**: 다인 경주처럼 순위가 있는 데이터에 Elo류 동적 레이팅을 적용하는 법 / 수백 종의 공공 API를 스키마별로 나눠 안정적으로 수집하는 파이프라인 설계

---

## 🤖 자동화 · 봇 · 스크래핑

> 사람이 반복하던 일을 컴퓨터가 대신하게 만든 것들. 정해진 시간에 알아서 돌고, 알림을 보내줍니다.

### 상품 스크래퍼 모음 · `naver-scrap`
쿠팡·네이버·무신사·명품몰 상품 정보와 리뷰를 긁어오는 통합 스크래핑 프로젝트.
- 사이트별 다른 구조(JSON-LD, __PRELOADED_STATE__) 파싱, 봇 차단 우회
- **스택**: Python(requests, BeautifulSoup) · Playwright · Cloudflare Workers
- **🎓 배울 수 있는 것**: 여러 사이트 파싱 전략 / 크롤러를 모듈로 나눠 재사용

### 무신사 갤러리 자동 갱신 · `musinsa.rescene.co`
무신사 추천 상품을 6시간마다 모아 엣지에서 빠르게 보여주는 서비스.
- 자동 갱신→KV 저장(gzip 650KB→60KB), 텔레그램으로 TOP5 알림
- **스택**: Cloudflare Worker · KV · cron · Telegram API · GitHub Actions
- **🎓 배울 수 있는 것**: 서버리스 cron 자동화 / Cache·gzip으로 속도 끌어내리기

### 출석체크 자동화 + 텔레그램 봇 · `opgarun`
웹사이트 출석체크를 자동으로 하고 텔레그램으로 조작하는 봇.
- Playwright로 로그인→출석 클릭, GitHub Actions 3시간 간격 실행
- **스택**: Python(Playwright) · GitHub Actions self-hosted runner · systemd
- **🎓 배울 수 있는 것**: Playwright 브라우저 자동화 / 텔레그램 양방향 봇

### 소니 렌즈 재입고 알림 · `sony-price`
소니 스토어 렌즈 재입고를 감시해 텔레그램으로 알려주는 추적기.
- 10분마다 폴링, 품절→재입고 전이 때만 알림
- **스택**: Cloudflare Workers · KV · Telegram API
- **🎓 배울 수 있는 것**: 엣지 컴퓨팅 감시 봇 / 상태 전이 기반 알림

### X 북마크 수집기 · `x-collection`
X(트위터) 북마크·좋아요를 자동 수집해 로컬 JSON/Markdown으로 저장.
- 로그인 세션 재사용 헤드리스 자동화, 증분 수집, 매일 자동 실행
- **스택**: Node.js · Playwright · Anthropic Claude SDK
- **🎓 배울 수 있는 것**: 세션 재사용 웹 자동화 / git 친화적 파일 데이터 저장

### 네이버 쇼핑 재입고 감시 · `naver-alarm`
네이버 쇼핑 상품의 재입고·가격변동을 감시해 알려주는 봇.
- Safari 쿠키 파싱·주입, macOS launchd 주기 실행
- **스택**: Python · Safari cookies · Telegram API · launchd
- **🎓 배울 수 있는 것**: launchd 스케줄러 / 쿠키 공급·감시 역할 분리 구조

### 책스타그램 일일 다이제스트 · `bookstagram`
여러 책 사이트에서 글을 모아 매일 마크다운 요약본을 만드는 수집 봇.
- 네이버 블로그·알라딘·레딧 4개 출처 수집, 중복 제거·출처별 분류
- **스택**: Python 3 표준 라이브러리만 (urllib · xml.etree)
- **🎓 배울 수 있는 것**: 여러 API·RSS 수집 패턴 / 의존성 없는 파이프라인

### 로또 자동 구매 · `lotto`
매주 토요일 아침 로또 6/45 자동 5게임을 알아서 구매하는 자동화 스크립트.
- 잔액·중복 구매 확인 후 자동 구매, launchd + GitHub Actions 이중 실행
- **스택**: Python · dhapi · launchd · GitHub Actions
- **🎓 배울 수 있는 것**: 로컬·클라우드 스케줄러 겹치기 / 상태 확인으로 안전한 자동화


### CGV 예매일 오픈 알리미 · `cgv`
보고 싶은 영화의 예매가 열리는 순간을 놓치지 않게 감시하고 알려주는 봇.
- CGV 내부 API로 극장별 예매 가능 날짜를 주기적으로 조회
- 이전에 본 날짜와 비교해 새 날짜가 열리면 즉시 감지
- 콘솔·macOS 알림·텔레그램으로 알림 발송 (systemd 상시 구동)
- **스택**: TypeScript · playwright-core · systemd · 텔레그램 봇 API
- **🎓 배울 수 있는 것**: 봇을 막는 사이트에 '진짜 브라우저'로 접근하는 법 / 상태를 저장해 '새로 생긴 것'만 골라내는 감시 패턴

---

## 📱 모바일 앱

> 손안의 기기에서 도는 앱들. 학습 앱부터 사진 정리 앱까지, 스토어 배포 직전까지 다듬은 것들입니다.

### 안키요 (암기 학습 앱) · `ankiyo`
Anki 스타일 간격 반복(SRS) 학습 앱 — Claude로 단어 카드 자동 생성.
- **스택**: Dart · Flutter · SQLite · Anthropic API · Cloudflare Workers
- **🎓 배울 수 있는 것**: 크로스플랫폼 코드 구조 / 학습 스케줄러 단위 테스트

### 루멘 (사진 정리 앱) · `ios`
제스처로 사진·동영상을 빠르게 정리하는 무료 네이티브 iOS 앱.
- 위로 올려 삭제, 아래로 당겨 보관, 수십만 장도 즉시 로딩
- **스택**: Swift 5.9 · SwiftUI · PhotoKit · XcodeGen
- **🎓 배울 수 있는 것**: PhotoKit 안전하게 다루기 / 대규모 미디어 성능 최적화

### 일본어 학습 (Watch 지원) · `watch`
iPhone과 Apple Watch에서 일본어 가나·단어를 학습하는 앱.
- 플래시카드·퀴즈·간격 반복 알림·TTS, Anki 덱 가져오기
- **스택**: Swift(SwiftUI) · watchOS · Swift Package
- **🎓 배울 수 있는 것**: iPhone+Watch 동시 지원 / 로직을 패키지로 분리해 테스트

---

## 🖥️ 데스크탑 · 네이티브 도구

> 내 컴퓨터에서 도는 진짜 프로그램들. 파일 검색, 사진 뷰어, 브라우저까지 직접 만들었습니다.

### macOS 네이티브 앱 모음 (그 외) · `macos`
개별 카드로 뺀 앱들 외에, 아직 다듬는 중인 macOS 앱들을 한데 모았습니다.
- alldoc: 문서 이름과 본문을 함께 찾는 검색기 (SQLite FTS5)
- disko: DaisyDisk 스타일 폴더 용량 분석 (AppKit + CoreGraphics)
- gom: SwiftUI 없이 AppKit만으로 만든 가벼운 동영상 플레이어
- **스택**: Swift · AppKit · SQLite FTS5 · CoreGraphics
- **🎓 배울 수 있는 것**: 대용량 데이터 앱의 성능 최적화 (수만 장 이미지 그리드) / macOS 네이티브 UI 패턴과 Homebrew 배포·코드서명
### 한글 문서 Spotlight 검색 · `hwpx`
한글(.hwpx) 문서 본문을 macOS Spotlight로 검색하게 해주는 인덱서.
- .hwpx(ZIP+XML) 본문 추출, Finder·mdfind 검색
- **스택**: Objective-C/C · Spotlight MDImporter · zlib
- **🎓 배울 수 있는 것**: macOS 시스템 프로그래밍 / ZIP·XML 저수준 파싱

### ev (파일 통합 검색 CLI) · `cli`
터미널에서 파일명과 내용을 동시에 실시간 검색하는 Everything 스타일 도구.
- 타이핑마다 실시간 재검색, 한글 문서 속 내용도 검색·미리보기
- **스택**: zsh · ripgrep · fzf · fd · bat · bats-core
- **🎓 배울 수 있는 것**: 쉘 스크립트로 대화형 TUI / Homebrew tap 배포

### 네이티브 MP3 플레이어 (Zig SDK 실험) · `native/mp3_player`
웹뷰 없이 Zig로 GPU 캔버스에 직접 그리는 실험적 Native SDK로 만든 macOS 로컬 음악 플레이어.
- ~/Music·~/Downloads 스캔 후 재생·탐색·볼륨 컨트롤, 실시간 스펙트럼 시각화
- **스택**: Zig · Native SDK (.native 마크업 + Zig 로직) · Metal GPU 서페이스
- **🎓 배울 수 있는 것**: 웹뷰 없는 네이티브 렌더링 구조 / Elm 스타일 Model-Update 아키텍처


### diskspeed (디스크 속도 측정기) · `macos/diskspeed`
내장 SSD·외장 드라이브·NAS의 진짜 읽기/쓰기 속도를 재는 macOS 네이티브 앱.
- 순차 읽기/쓰기(8 MiB 블록)와 랜덤 4K 읽기/쓰기를 나눠 측정
- 내장·외장·네트워크(SMB/NFS) 볼륨 자동 감지
- 테스트 파일은 임시 생성 후 종료 시 자동 삭제
- **스택**: Swift · AppKit · SwiftPM · Homebrew Cask
- **🎓 배울 수 있는 것**: 캐시를 우회해야 믿을 만한 측정이 된다는 것(F_NOCACHE) / DMG·brew로 남이 설치할 수 있게 배포하기


### anf (all new finder) · `macos/all_new_finder`
분할 뷰·내장 터미널·커맨드 팔레트를 하나로 합친 macOS 네이티브 파일 브라우저.
- Finder·윈도우 탐색기·정통 오쏘독스(Mdir) 스타일을 한 화면에 합침
- 파일 목록에서 바로 터미널을 열고 커맨드 팔레트로 기능을 호출
- Swift + AppKit 네이티브 — Electron 없이 가볍게 동작
- **스택**: Swift · AppKit · SwiftPM
- **🎓 배울 수 있는 것**: 익숙한 도구를 '내 손에 맞게' 다시 만들어 보는 경험 / 490번의 커밋 — 오래 붙잡고 다듬어야 도구가 쓸 만해진다는 것

### Lumen (macOS 사진 뷰어) · `macos/lumen`
6만 장이 넘는 사진 라이브러리, 특히 NAS에 있는 것도 가볍게 다루는 macOS 사진 매니저.
- JPEG·HEIC·RAW 등 재귀 스캔, 앨범·태그·색상 라벨로 정리
- 크롭·리사이즈는 기본이 비파괴 — 새 파일로 저장하고 원본은 보존
- NAS의 대용량 라이브러리도 끊김 없이 넘겨보게 최적화
- **스택**: Swift 6 · SwiftUI · AppKit
- **🎓 배울 수 있는 것**: 수만 장을 다뤄도 안 버벅이게 만드는 목록·썸네일 처리 / '되돌릴 수 없는 동작'을 기본값에서 빼두는 설계 태도

### MarkForge (Markdown 뷰어) · `macos/markforge`
Zed의 GPU 렌더링 엔진(GPUI)으로 만든 웹뷰 없는 네이티브 Markdown 뷰어.
- Zed의 미리보기와 같은 엔진으로 Markdown을 GPU 가속 렌더링
- VSCode 스타일 사이드바로 폴더를 열어 문서를 오가며 확인
- 웹뷰·Electron 없이 즉시 실행
- **스택**: Rust · GPUI · gpui-component
- **🎓 배울 수 있는 것**: 웹 기술 없이 데스크탑 UI를 그리는 또 다른 길 / 이미 잘 만들어진 엔진을 가져다 쓰면 어디까지 빨라지는지

### Termina (SSH·SFTP 클라이언트) · `macos/terminus`
Ghostty의 GPU 터미널 코어를 얹은 macOS 네이티브 SSH·SFTP 관리자.
- 저장한 호스트 목록에서 탭으로 여러 서버에 동시 접속
- libghostty로 터미널을 렌더링하고 tmux 세션을 유지
- 원격 파일 브라우저와 SSH 터널 상태를 한 화면에서 확인
- **스택**: Swift · AppKit · libghostty
- **🎓 배울 수 있는 것**: 서버에 접속하는 도구가 안에서 어떻게 동작하는지 / 검증된 코어(Ghostty)를 끼워 넣어 앱을 빨리 완성하는 법

### ContainerDesk (Apple Container GUI) · `macos/coui`
Apple Container를 Docker Desktop처럼 클릭으로 다루는 macOS 관리 앱.
- 컨테이너 목록·검색과 시작·정지·삭제, 실시간 로그 스트리밍
- 이미지 pull과 볼륨·네트워크 생성·삭제를 화면에서 처리
- 엔진 자체를 사이드바에서 켜고 끄기
- **스택**: Swift · SwiftUI · Apple Container
- **🎓 배울 수 있는 것**: 명령어로만 되던 일을 GUI로 감싸 남도 쓰게 만드는 과정 / 3초마다 상태를 물어보며 화면을 최신으로 유지하는 폴링 설계

### meradio (라디오 메뉴바 앱) · `macos/meradio`
한국 라디오 57개 방송국을 메뉴 바에서 바로 듣는 macOS 앱.
- 방송국 목록과 스트림 주소를 모아 메뉴 바에서 선택 재생
- 독 아이콘도 창도 없이 메뉴 바에만 상주
- Homebrew로 설치
- **스택**: Swift · SwiftUI (MenuBarExtra) · Homebrew Cask
- **🎓 배울 수 있는 것**: 창 없는 앱 — 메뉴 바에만 사는 프로그램 만들기 / 웹에 흩어진 스트림 주소를 모아 내 앱의 데이터로 쓰기

### Pomodoro (뽀모도로 타이머) · `macos/pomodoro`
메뉴 바에 사는 가벼운 뽀모도로 타이머 — iPhone·Apple Watch까지 App Store 출시.
- 집중·짧은 휴식·긴 휴식 주기를 자동으로 전환
- 독 아이콘 없이 메뉴 바에서만 동작
- iPhone은 Live Activity·다이내믹 아일랜드 지원, Apple Watch 앱도 함께 배포
- **스택**: Swift · SwiftUI (MenuBarExtra) · WidgetKit · App Store
- **🎓 배울 수 있는 것**: 같은 아이디어를 Mac·iPhone·Watch 세 화면에 맞게 펼치는 법 / 작은 앱이라도 스토어 심사를 통과해 출시까지 가보는 경험

### vpdf (PDF 뷰어) · `macos/vpdf`
AppKit + PDFKit으로 만든 빠른 macOS 네이티브 PDF 뷰어.
- SwiftUI 없이 AppKit·PDFKit만 써서 즉시 뜨는 가벼운 뷰어
- DMG와 Homebrew Cask로 배포
- **스택**: Swift · AppKit · PDFKit · Homebrew Cask
- **🎓 배울 수 있는 것**: OS가 이미 주는 기능(PDFKit)을 찾아 쓰면 앱이 얼마나 빨리 완성되는지 / 만든 앱을 남이 설치할 수 있는 형태로 포장하기

---

## ⌨️ CLI · 금융 도구

### 토스증권 CLI · `toss-cli`
토스증권 공식 Open API로 시세·주문·포트폴리오를 다루는 커맨드라인 도구.
- 대화형 REPL, 주문 미리보기(--dry-run)·확인, 시뮬레이션 모드, Keychain 보관
- **스택**: Python · Typer · httpx · rich · prompt_toolkit
- **🎓 배울 수 있는 것**: 안전한 CLI 설계(dry-run·확인) / OAuth2·토큰 캐싱

---

## 🔐 보안 · 인프라 · 데이터

> 눈에 잘 안 보이지만 시스템을 지탱하는 영역. 컨테이너 보안, 접근제어, 데이터 파이프라인을 직접 실습했습니다.

### 컨테이너 이미지 하드닝 · `image-harden`
Chainguard Wolfi/melange/apko로 컨테이너 이미지를 최소화·보안 강화.
- 일반 이미지(CVE 80+) vs 하드닝 이미지(CVE 0) 비교, 서명·SBOM·검증
- **🎓 배울 수 있는 것**: 컨테이너 보안 / 소프트웨어 서명·검증

### Zero-Trust 접근제어 실습 · `boundary`
HashiCorp Boundary + Vault + Keycloak을 Docker로 직접 띄워 배우는 실습.
- 접근제어(RBAC), SSO, 동적 자격증명, 셀프서비스 포털
- **🎓 배울 수 있는 것**: GitOps 접근제어 / zero-trust 전체 구성 흐름

### 취약점 스캔·조치 자동화 · `oy-guard`
컨테이너 취약점을 스캔·패치·서명까지 자동화하는 풀스택 시스템.
- Trivy+Grype 스캔, OS 패치, cosign 서명, 웹 대시보드+CLI
- **🎓 배울 수 있는 것**: 비동기 작업·상태 관리 / 웹·CLI 코드 재사용

### API 보안 점검 리포트 · `oy-hack`
개발 환경 API 게이트웨이의 보안 취약점을 점검·분석한 리포트.
- 인증 없는 노출·CORS 반사·에러 누출 발굴, 엔드포인트 카탈로깅
- **🎓 배울 수 있는 것**: API 보안 점검 방법론 / 위험도 우선순위화

### POS 키관리 개선 제안 · `kms`
POS 카드정보 암호화 키관리 개선 제안서 (AWS KMS vs Vault).
- 현재 문제 분석, KMS 솔루션 제안, 대안 비교
- **🎓 배울 수 있는 것**: 키관리 아키텍처 설계 / 트레이드오프 비교

### MCP 게이트웨이 · `mcp-gateway`
여러 MCP 서버를 하나의 엔드포인트로 묶는 프록시 게이트웨이.
- aggregation, 웹 UI·인증·관측성, 단일 주소 노출
- **🎓 배울 수 있는 것**: MCP 프로토콜 / API 게이트웨이 패턴

### dbt 데이터 파이프라인 놀이터 · `dbt-playground-repo`
DuckDB로 노트북에서 dbt를 갖고 노는 데이터 파이프라인 놀이터.
- 6개 도메인 seed→staging→mart, 다양한 데이터 소스, lineage 그래프
- **🎓 배울 수 있는 것**: dbt 계층 설계 / 커스텀 테스트로 규칙 검증

### Nimbo (리눅스 NAS 웹 콘솔) · `nimbo`
리눅스 서버를 시놀로지 DSM처럼 관리하는 셀프호스팅 웹 콘솔.
- 창·도크·⌘K 데스크톱형 UI에 19개 앱 — ZFS·SMART·백업·Docker·방화벽·2FA
- **스택**: Next.js 16 · React 19 · Tailwind v4 · ghostty-web · systemd + Caddy
- **🎓 배울 수 있는 것**: 웹앱이 실제 시스템 상태를 읽는 계층 설계 / '배포 가능한 제품' 만들기

### Zen (홈 NAS 운영체제) · `zen`
맥북에서 빌드해 USB로 굽는 FreeBSD 기반 커스텀 NAS 운영체제.
- 읽기전용 루트 + A/B 업데이트 임베디드 OS, 파일 공유 6종, Go ZFS 관리 TUI
- **스택**: FreeBSD 15/NanoBSD · ZFS · QEMU · Go + Bubble Tea
- **🎓 배울 수 있는 것**: OS 이미지 조립·부팅 파이프라인 / Go TUI 관리 도구 만들기


### 홈랩 구성 기록 · `homelab`
집에서 직접 굴리는 서버 4대의 스토리지·백업·네트워크를 문서로 정리한 운영 기록.
- 노드 4대(스토리지·컴퓨트·상시서비스·워크스테이션)의 하드웨어와 역할 정리
- ZFS 미러·rsync·restic 3중 백업, 10G 네트워크 이중화
- 장애 상황과 복구 절차를 실측 기반으로 문서화 (13종 문서)
- **스택**: Ubuntu · ZFS · libvirt/KVM · Tailscale · Jekyll
- **🎓 배울 수 있는 것**: '지루하고 안정적인 것이 미덕' — 검증된 조합으로 시스템 짜기 / 겪은 장애를 남겨 다음 사람이 덜 헤매게 하기

### CoreOS 쿠버네티스 클러스터 · `vms/coreos-k8s`
집 서버 위에 가상머신을 띄워 쿠버네티스 클러스터를 바닥부터 구성한 실습.
- Fedora CoreOS VM을 Butane 설정으로 자동 프로비저닝
- kubeadm으로 control plane + worker 구성, Flannel로 네트워크 연결
- Gitea·모니터링까지 올려 실제 굴러가는 클러스터로 완성
- **스택**: Fedora CoreOS · Kubernetes · CRI-O · Flannel · libvirt/KVM
- **🎓 배울 수 있는 것**: 클라우드 없이 내 컴퓨터에서 쿠버네티스 만져보기 / 설정 파일로 서버를 찍어내는 자동 구성 감각

### 3D 지형 · 인구 지도 렌더링 · `3d-map`
공개 지형·인구 데이터를 받아 대륙별 3D 지도 이미지로 렌더링하는 파이프라인.
- ETOPO 고도 데이터와 GHSL 인구격자 데이터를 내려받아 전처리
- 대륙별 고도 지도와 인구 밀도 지도를 렌더링, 국가 경계를 겹쳐 그리기
- **스택**: Python · GDAL/rasterio · ETOPO · GHSL 인구격자 · Natural Earth
- **🎓 배울 수 있는 것**: 기관이 무료로 푸는 지리 데이터 다뤄보기 / 숫자 격자를 사람이 보는 그림으로 바꾸기

### Leptos 서버 렌더링 성능 측정 · `leptos`
Rust 웹 프레임워크로 서버를 짜고 초당 몇 건까지 버티는지 실측한 하네스.
- Leptos SSR + Axum으로 서버 렌더링 전용 백엔드 구성
- wrk로 부하를 걸어 엔드포인트별 처리량 측정
- '초당 100만 요청'이 성립하는 조건과 한계를 함께 기록
- **스택**: Rust · Leptos 0.8 · Axum 0.8 · wrk
- **🎓 배울 수 있는 것**: 성능 수치를 '조건'과 함께 의심하며 읽기 / 직접 부하를 걸어 한계를 숫자로 확인하기

---

## 💡 여러분이 배울 수 있는 6가지 (요약)

1. **공개 데이터를 가져와 화면으로** — 정부·금융·쇼핑몰 API를 가져와 누구나 보는 웹페이지로. 코딩의 가장 빠른 보람.
2. **반복은 컴퓨터에게** — 매일 손으로 하던 일을 스케줄러·봇으로 자동화하고 텔레그램으로 알림 받기.
3. **공짜로 배포하기** — Cloudflare Pages·Workers·KV로 서버 비용 없이 전 세계에 띄우기.
4. **내 손안의 앱** — Flutter·SwiftUI로 진짜 스마트폰 앱을 만들고 스토어에 올리기까지.
5. **AI와 짝코딩** — Claude 같은 AI를 도구로 끼워 함께 만드는 '바이브 코딩'.
6. **내 데이터 되찾기** — 구글 Takeout처럼 기업이 가진 내 데이터를 받아, 서버에 올리지 않고 브라우저에서만 분석·시각화하기.

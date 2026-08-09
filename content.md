# 바이브 코딩 쇼케이스 🚀

> AI와 함께 만든 50개의 작은 프로젝트들 — 동네 주민 코딩 교육용 포트폴리오

혼자서, 그리고 AI와 짝을 이뤄 만든 프로젝트 모음입니다.
웹 서비스부터 모바일 앱, 데스크탑 도구, 자동화 봇, 보안 인프라까지 — 거창하지 않아도 **'직접 굴러가는 것'을 만드는 게 코딩의 시작**입니다.

각 프로젝트마다 **"무엇을 만들었나"**와 **"여러분이 배울 수 있는 것"**을 정리했어요.

---

## 한눈에 보기

| 분야 | 프로젝트 수 | 대표작 |
|------|:---:|------|
| 🌐 웹 서비스·대시보드 | 20 | 국회 감시 대시보드, 법령 검색, 실시간 같이보기(Unflix) |
| 🤖 자동화·봇·스크래핑 | 9 | 출석 자동화 봇, 재입고 알림, 로또 자동 구매 |
| 📱 모바일 앱 | 3 | 사진 정리 앱(루멘), 암기 앱(안키요) |
| 🖥️ 데스크탑·네이티브 도구 | 4 | 파일 검색 CLI, 한글문서 Spotlight 검색 |
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

### macOS 네이티브 앱 모음 · `macos`
직접 만든 macOS 앱들 — 파일 브라우저, 사진 뷰어, 문서 검색, Markdown 뷰어.
- 분할뷰 파일 브라우저, NAS 사진 관리자, SQLite FTS5 문서 검색
- **스택**: Swift 6 + SwiftUI/AppKit · Rust + GPUI · SQLite FTS5
- **🎓 배울 수 있는 것**: 대용량 앱 성능 최적화 / Homebrew 배포·코드서명

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

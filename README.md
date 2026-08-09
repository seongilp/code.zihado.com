# 100개 서비스 만들기 프로젝트 🚀

1년 동안 100개의 서비스를 만드는 프로젝트입니다. 지금까지 **59개** — 분야별로 모은 **동네 주민 코딩 교육용 포트폴리오** 사이트입니다.
빌드가 필요 없는 단일 정적 페이지(`index.html` + `projects.json`)로, Cloudflare Pages에 그대로 올라갑니다.

🔗 **라이브**: https://code.zihado.com

## 파일 구성

| 파일 | 설명 |
|------|------|
| `index.html` | 쇼케이스 사이트 본체 (단일 정적 페이지, 의존성 0) |
| `projects.json` | 프로젝트 내용 데이터 — **여기만 고치면 사이트가 바뀝니다** |
| `content.md` | 같은 내용을 읽기 좋게 정리한 마크다운 |
| `BLOG.md` | 동네 주민에게 소개하는 글 (발표/배포용) |
| `playground-index.json` | `~/work/playground` 하위 디렉토리 추적 파일 — 새 디렉토리가 생기면 여기와 비교해 쇼케이스를 갱신 |

내용을 추가·수정하려면 `projects.json`의 `categories → projects` 배열만 손보면 됩니다.
세 가지 테마가 모두 같은 `projects.json`을 공유합니다.

## 타임라인 (1년에 100개 만들기)

`/#timeline` 탭에서 "무엇을 언제 만들었나"를 시간순으로 보여줍니다.
각 카드의 `started`(만들기 시작한 날) · `updated`(마지막으로 손댄 날) 값으로 그려지므로,
**새 프로젝트를 추가할 때 두 필드를 반드시 채워야 합니다.** 채우는 방법은
[`scripts/update-prompt.md`](scripts/update-prompt.md)의 "날짜 규칙" 참고.

목표 설정은 `projects.json`의 `meta.goal` 한 곳에 있습니다:

```json
"goal": { "target": 100, "start": "2026-05-26", "months": 12 }
```

첫 화면의 "N개 만들었어요 / N개 남았어요"와 타임라인의 진행률·남은 기간·필요 페이스가
모두 이 값과 카드 수로 자동 계산됩니다. `index.html`의 `GOAL_DEFAULT`는 이 값이
없을 때만 쓰이는 기본값입니다.

## 테마 (git 브랜치)

| 브랜치 | 테마 | 주소 |
|--------|------|------|
| `main` | **플랫 디자인** (현재 프로덕션) | https://code.zihado.com |
| `flat-theme` | 플랫 디자인 원본 | https://flat-theme.vibe-coding-dmy.pages.dev |
| `new-theme` | 네오브루탈리즘 | https://new-theme.vibe-coding-dmy.pages.dev |

> 친근한 종이 테마(최초 버전)는 git 이력에 남아 있어 언제든 되살릴 수 있습니다.

## 담은 프로젝트 (6개 분야 · 59개)

- 🌐 **웹 서비스·대시보드** — 국회 감시, 법령 검색(54만 조문), Unflix(같이보기), weblog(브라우저 SQL 분석) …
- 🤖 **자동화·봇·스크래핑** — 출석 자동화, 재입고 알림, 로또 자동 구매 …
- 📱 **모바일 앱** — 루멘(사진 정리), 안키요(암기), 일본어 학습 …
- 🖥️ **데스크탑·네이티브 도구** — anf(파일 브라우저), Lumen(사진 뷰어), Termina(SSH), ContainerDesk, Pomodoro, vpdf, diskspeed …
- ⌨️ **CLI·금융** — 토스증권 CLI
- 🔐 **보안·인프라·데이터** — Nimbo(NAS 웹 콘솔), Zen(NAS OS), 컨테이너 하드닝, dbt 파이프라인 …

각 카드에는 *한 줄 소개 / 하는 일 / 기술 스택 / 🎓 배울 수 있는 것 / 상태 / 라이브 링크*가 들어 있습니다.

## 로컬에서 미리보기

브라우저로 `index.html`을 직접 열면 보안 정책 때문에 데이터를 못 불러옵니다. 작은 서버로 띄우세요:

```bash
cd code.zihado.com
python3 -m http.server 8799     # 또는: npx serve
```

→ http://localhost:8799 접속

## Cloudflare Pages 배포

Pages 프로젝트 `vibe-zihado-com`이 GitHub 저장소
(`seongilp/code.zihado.com`)와 **git 연동**되어 있어, 푸시하면 자동 배포됩니다.

```bash
# 프로덕션 배포 = main에 푸시
git push origin main

# 다른 테마 브랜치를 푸시하면 프리뷰 배포가 생성됨
git push origin new-theme
```

`wrangler pages deploy` 직접 업로드는 git 연동 프로젝트라 사용하지 않습니다.
커스텀 도메인(`code.zihado.com`)은 Cloudflare 대시보드 → Pages → Custom domains에서 연결돼 있습니다.

## 라이선스 / 출처

모든 프로젝트는 직접 만든 것이며, 쇼케이스 텍스트는 교육 목적의 요약입니다.
일부 프로젝트는 비공개 저장소라 카드만 표시되고 링크가 없습니다.

---

*made with ❤️ and claude*

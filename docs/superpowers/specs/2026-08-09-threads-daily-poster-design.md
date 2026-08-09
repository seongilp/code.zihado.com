# Threads 일일 프로젝트 소개 자동 포스팅 — 설계

- 날짜: 2026-08-09
- 대상 저장소: `code.zihado.com`
- 상태: 설계 승인됨, 구현 계획 대기

## 1. 목적

`projects.json`에 정리된 59개 프로젝트를 매일 하나씩 Threads에 소개한다.
"100개 서비스 만들기 프로젝트"의 진행 상황을 매일 조금씩 드러내는 것이 목적이며,
포스팅 문구는 자랑이 아니라 **"이런 걸 만들어봤고, 만들면서 이런 걸 배웠다"** 라는
교육적 각도를 유지한다. 이는 사이트 자체의 대상 독자(`meta.audience` = 동네 주민
코딩 교육용)와 같은 톤이다.

## 2. 결정 사항

| 항목 | 결정 | 근거 |
|---|---|---|
| 문구 생성 | headless `claude -p`로 매번 새로 작성 | 기존 `auto-update.sh`와 같은 패턴. 59개가 같은 틀이면 피드에서 단조롭다 |
| 선택 순서 | 아직 안 올린 것 중 랜덤 | 카테고리가 섞여 매일 분위기가 달라진다 |
| 게시 승인 | 텔레그램 초안 전송 → 버튼 승인 후 게시 | 공개 계정이므로 LLM 출력을 그대로 내보내지 않는다 |
| 승인 구현 | 2단 launchd (생성 잡 + 폴링 잡) | 승인이 몇 시간 뒤에 와도 동작한다 |
| 이미지 | 텍스트만 | Threads가 링크의 OG 카드를 자동 표시한다. 실패 지점을 늘리지 않는다 |
| 초안 시각 | 매일 08:00 (KST) | 출근길에 폰으로 확인 후 승인 |
| 재고 소진 후 | `posted.json` 비우고 2회차 시작 | 피드가 끊기지 않는다. 2회차는 다른 각도로 쓴다 |

## 3. 전체 구조

```
scripts/threads/
  poster/                 Python 패키지 — 표준 라이브러리만, 의존성 0
    selector.py           후보 선택 · 회차 계산 · posted 갱신
    sanitize.py           LLM 출력 정리 · 길이 검증
    threads_api.py        컨테이너 생성 · 게시 · 토큰 갱신
    telegram.py           전송 · getUpdates · offset 관리
    state.py              상태 파일 읽기/쓰기 · flock
  compose.py              08:00 진입점
  approve.py              5분마다 진입점
  compose-prompt.md       claude -p 에 넘길 문구 작성 지침
  tests/                  pytest — 네트워크 없이 도는 것만
  launchd/
    com.zihado.threads-compose.plist
    com.zihado.threads-approve.plist
```

셸 스크립트는 두지 않는다. launchd가 `python3`을 직접 호출한다.
로직을 Python에 두는 이유는 이 시스템에서 가장 틀리기 쉬운 부분(선택, 회차 계산,
길이 정리, 중복 방지)이 전부 순수 로직이고, 셸로는 이를 테스트할 수 없기 때문이다.

각 모듈의 경계:

- `selector` — `projects.json`과 `posted.json`을 입력받아 다음에 올릴 프로젝트 1건과
  회차를 반환한다. 파일 I/O도 네트워크도 모른다.
- `sanitize` — 문자열을 받아 정리된 문자열 또는 길이 초과 오류를 반환한다.
- `threads_api` / `telegram` — HTTP만 담당한다. 주입된 트랜스포트를 쓰므로 테스트에서
  스텁으로 교체된다.
- `state` — 상태 파일의 유일한 접근 경로. 잠금도 여기서만 건다.

## 4. 상태

상태는 **저장소 밖** `~/.local/state/threads-poster/`에 둔다.

이유: `auto-update.sh`에 "워킹 트리가 더러우면 이번 주기를 건너뛴다"는 가드가 있다.
상태 파일을 저장소 안에 쓰면 매일 트리가 더러워져 **주간 자동 업데이트가 영구히
스킵된다.** 이 시스템은 저장소를 `projects.json` 읽기 전용으로만 사용한다.

```
~/.local/state/threads-poster/
  posted.json     올린 기록 (누적)
  pending.json    승인 대기 중인 초안 — 존재 자체가 락 역할
  token.json      Threads 장기 토큰 (chmod 600)
  offset.json     텔레그램 getUpdates offset
  lock            flock 대상
```

`posted.json`

```json
[
  { "slug": "law", "round": 1, "postedAt": "2026-08-09T08:12:00+09:00",
    "threadId": "17901234567890", "text": "..." },
  { "slug": "asm", "round": 1, "postedAt": "2026-08-10T08:05:00+09:00",
    "skipped": true }
]
```

건너뛴 항목도 기록한다. 안 그러면 다음 날 같은 프로젝트가 다시 뽑힌다.
`text`를 보관하는 이유는 2회차에서 "1회차와 다른 각도로 쓰라"고 지시하기 위해서다.

`pending.json`

```json
{
  "slug": "law", "round": 1, "text": "...",
  "createdAt": "2026-08-09T08:00:00+09:00",
  "telegramMessageId": 4521,
  "creationId": null
}
```

`creationId`는 Threads 컨테이너를 만든 뒤에만 채워진다. 중복 게시 방지의 핵심이다.

`token.json`

```json
{ "userId": "1234567890", "token": "THQVJ...", "refreshedAt": "2026-08-09T08:00:00+09:00" }
```

## 5. 데이터 흐름

```
projects.json (59개)  ──읽기 전용──┐
                                   ↓
posted.json ────→ 후보군 = 전체 − (올린 것 ∪ 건너뛴 것)
                                   ↓  후보가 비면: posted 보관 후 비우고 round+1
                             랜덤 1개 선택
                                   ↓
        claude -p + compose-prompt.md + 프로젝트 JSON → 문구
                                   ↓
                      sanitize → 500자 이내 검증
                                   ↓
              pending.json 저장 + 텔레그램 초안 전송 (인라인 버튼)
                                   ↓  (approve.py가 5분마다 확인)
          ✅ 게시     → 컨테이너 생성 → 30초 대기 → publish
                      → posted.json 기록 → pending 삭제 → 완료 알림
          🔄 다시     → pending 삭제 → 같은 프로젝트로 문구만 재생성
                        (approve.py가 compose 모듈을 직접 호출한다.
                         선택 단계를 다시 거치지 않으므로 프로젝트는 유지된다)
          ❌ 건너뛰기 → posted.json에 skipped 기록 → pending 삭제
```

## 6. 문구 생성

`compose-prompt.md`가 `claude -p`에 전달되는 지침이다. 프로젝트 1건의 JSON이 함께 주입된다.

지침의 핵심:

- 출력은 **순수 텍스트만**. 설명·머리말·마크다운 펜스 금지
- **500자 이내** (Threads 텍스트 상한)
- 톤: 성과 자랑이 아니라 만들면서 배운 것. `learn` 필드를 중심 소재로 삼는다
- `live`가 있으면 마지막 줄에 URL을 붙이고, 없으면 링크 없이 마무리한다
- 해시태그는 고정 2~3개 (`#100개서비스만들기` 포함)
- `round`가 2 이상이면 이전 회차 본문을 함께 주고 **다른 각도**로 쓰도록 지시한다

`sanitize`가 앞뒤 공백, 감싸는 따옴표, ` ``` ` 펜스를 제거한 뒤 길이를 검증한다.

호출은 기존 `auto-update.sh`와 같은 headless 방식이다. 지침 뒤에 대상 프로젝트
JSON과 (2회차 이상이면) 이전 회차 본문을 이어붙여 하나의 프롬프트로 만든다:

```python
prompt = "\n\n".join([
    compose_prompt_md,
    "## 오늘 소개할 프로젝트\n```json\n" + project_json + "\n```",
    previous_text_block,   # round >= 2 일 때만
])
subprocess.run(["claude", "-p", prompt, "--model", "claude-sonnet-5",
                "--max-turns", "3"], ...)
```

파일 수정도 검색도 필요 없으므로 도구는 주지 않는다 (`--allowed-tools` 생략).
`claude` 실행 파일 경로는 `auto-update.sh`와 동일하게 `~/.local/bin/claude`를 쓴다.

## 7. Threads API 연동

```
POST https://graph.threads.net/v1.0/{userId}/threads
     ?media_type=TEXT&text=<urlencoded>&access_token=<token>
  → { "id": "<creationId>" }

  (약 30초 대기 — 문서 권장)

POST https://graph.threads.net/v1.0/{userId}/threads_publish
     ?creation_id=<creationId>&access_token=<token>
  → { "id": "<threadId>" }
```

게시 한도는 24시간당 250개로, 하루 1개인 이 시스템과는 무관하다.

**토큰 관리**

- 장기 토큰 수명 60일. `GET /refresh_access_token?grant_type=th_refresh_token&access_token=<token>`
  으로 갱신하면 다시 60일. 발급 후 24시간이 지나야 갱신할 수 있다
- `approve.py`가 실행될 때마다 `refreshedAt`을 확인해 **30일이 넘으면 자동 갱신**한다.
  60일까지 기다리지 않는 이유는 맥이 한 달 꺼져 있어도 여유가 남게 하기 위해서다
- 갱신 실패 시 텔레그램으로 수동 재발급 안내를 보낸다
- 최초 토큰 발급과 `userId` 조회(`GET /me?fields=id`)는 Meta 개발자 콘솔에서 수동으로 한다.
  자동화 대상이 아니다

**필요 권한**: `threads_basic`, `threads_content_publish`

## 8. 에러 처리

가장 중요한 목표는 **중복 게시 방지**다. 폴링 구조는 잘못 만들면 같은 글을 두 번 올린다.

| 상황 | 처리 |
|---|---|
| 컨테이너 생성 성공 후 publish 실패 | `creationId`를 `pending.json`에 저장. 다음 폴링에서 **같은 creationId로 publish만 재시도**. 컨테이너를 다시 만들지 않는다 |
| `approve.py` 겹쳐 실행 | `flock`으로 상태 디렉토리 잠금. 두 번째 인스턴스는 즉시 종료 |
| 텔레그램 업데이트 중복 수신 | `offset.json`에 처리 완료 offset 저장. 같은 업데이트를 두 번 처리하지 않는다 |
| 08:00에 어제 `pending`이 남아 있음 | 새 초안을 만들지 않고 "어제 초안이 아직 대기 중"만 알린다. 초안이 쌓이지 않는다 |
| 맥이 꺼져 있어 08:00을 놓침 | launchd가 깨어날 때 밀린 잡을 실행한다 |
| `claude` CLI 없음 / 실패 | 텔레그램 알림 후 종료. 그날은 건너뛴다 (`posted`에 기록하지 않으므로 후보로 남는다) |
| 500자 초과 | 1회 재생성. 그래도 넘으면 초안을 그대로 보내되 "길이 초과 — 직접 줄여야 함"을 붙인다 |
| 토큰 만료 | 텔레그램 알림. `pending`은 유지되므로 토큰을 고치면 그대로 게시된다 |
| `projects.json` 파싱 실패 | 텔레그램 알림 후 종료. 저장소를 건드리지 않는다 |

기존 `auto-update.sh`와 마찬가지로 모든 예외를 잡아 텔레그램으로 알린다.
**조용히 죽는 실패 경로를 만들지 않는다.**

로그는 `~/Library/Logs/threads-poster.log`에 남긴다.

## 9. 텔레그램 연동

자격증명은 기존 `~/.env`의 `TELEGRAM_BOT_TOKEN` / `AUTHORIZED_CHAT_ID`를 그대로 쓴다.

초안 메시지에 인라인 키보드를 붙인다:

```
[ ✅ 게시 ]  [ 🔄 다시 ]  [ ❌ 건너뛰기 ]
```

`callback_data`는 `threads:<action>:<slug>` 형식이다. `approve.py`는 `getUpdates`로
콜백을 읽고, `pending.json`의 slug와 일치할 때만 처리한다. 처리 후 원본 메시지를
편집해 결과(게시됨 / 건너뜀)를 표시하고 버튼을 제거한다.

**제약**: 텔레그램 봇 토큰 하나당 `getUpdates`는 한 프로세스만 사용할 수 있다.
현재 `auto-update.sh`는 전송만 하고 폴링하지 않으므로 충돌이 없다.
같은 봇으로 다른 폴링 봇을 돌리게 되면 별도 봇을 발급해야 한다.

## 10. 테스트

- **단위** (`pytest`, 네트워크 없음)
  - `selector` — 중복 선택 안 함, 건너뛴 항목 제외, 후보 소진 시 회차 전환
  - `sanitize` — 펜스·따옴표 제거, 500자 경계값
  - `state` — 원자적 쓰기, flock 동작
- **통합** (HTTP 스텁 주입)
  - publish 실패 후 재시도가 컨테이너를 두 번 만들지 않는다
  - 같은 텔레그램 업데이트를 두 번 받아도 한 번만 게시한다
  - 토큰이 30일을 넘으면 갱신을 호출한다
- **수동 E2E**
  - `DRY_RUN=1` — 실제 게시만 빼고 전 구간 실행
  - `--project <slug>` — 특정 프로젝트 강제 지정

실제 Threads 게시는 자동 테스트하지 않는다. 첫 실행을 직접 지켜보는 것으로 대신한다.

## 11. 함께 고칠 것

`scripts/launchd/com.zihado.portfolio-update.plist`의 경로가 아직 옛 저장소
이름(`vibe-coding/scripts/auto-update.sh`)이다. 실제 `~/Library/LaunchAgents/`는
292a582에서 고쳤으나 저장소 템플릿이 남아 있다. 새 plist를 추가하는 김에 함께 맞춘다.

## 12. 범위 밖

- 이미지·비디오·캐러셀 게시
- 예약 게시 (Threads API가 지원하지 않는다. cron 실행 시각 = 게시 시각)
- 댓글·답글 자동화, 지표 수집
- 다른 SNS(X, LinkedIn 등) 동시 게시

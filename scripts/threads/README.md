# Threads 일일 자동 포스팅

`projects.json`의 프로젝트를 매일 하나씩 골라 문구를 만들고,
텔레그램으로 승인을 받아 Threads에 게시합니다.

- 매일 **08:00** — `compose.py`가 초안을 만들어 텔레그램으로 보냅니다
- **5분마다** — `approve.py`가 버튼 응답을 확인해 게시/건너뛰기/재작성을 처리합니다

설계 문서: `docs/superpowers/specs/2026-08-09-threads-daily-poster-design.md`

## 최초 설정

### 1. Threads 앱과 토큰 (수동, 1회)

1. https://developers.facebook.com/apps 에서 앱을 만들고 **Threads API** 제품을 추가합니다
2. 권한에 `threads_basic`, `threads_content_publish`를 넣습니다
3. Threads 계정으로 인증해 **장기 토큰(long-lived token)**을 발급받습니다
4. 사용자 ID를 조회합니다:

   ```bash
   curl -s "https://graph.threads.net/v1.0/me?fields=id&access_token=<TOKEN>"
   ```

5. 상태 디렉토리에 토큰을 저장합니다:

   ```bash
   mkdir -p ~/.local/state/threads-poster
   cat > ~/.local/state/threads-poster/token.json <<'JSON'
   {
     "userId": "<위에서 받은 id>",
     "token": "<장기 토큰>",
     "refreshedAt": "2026-08-09T00:00:00+00:00"
   }
   JSON
   chmod 600 ~/.local/state/threads-poster/token.json
   ```

토큰은 60일마다 만료되지만, `approve.py`가 5분마다 나이를 확인해 30일이 지나면
자동으로 갱신합니다. 대기 중인 초안이 없어도 확인합니다. 갱신에 실패하면 텔레그램으로
알림이 오고, 옛 토큰(아직 30일 남음)으로 계속 동작하며 다음 실행에서 다시 시도합니다.

### 2. 텔레그램

`~/.env`의 `TELEGRAM_BOT_TOKEN` / `AUTHORIZED_CHAT_ID`를 그대로 씁니다
(`scripts/auto-update.sh`와 같은 값).

> **주의**: 봇 토큰 하나당 `getUpdates`는 한 프로세스만 쓸 수 있습니다.
> 같은 봇으로 다른 폴링 봇을 돌리면 충돌합니다. 그럴 땐 별도 봇을 발급하세요.

### 3. launchd 등록

```bash
cp scripts/threads/launchd/*.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.zihado.threads-compose.plist
launchctl load ~/Library/LaunchAgents/com.zihado.threads-approve.plist
launchctl list | grep threads
```

plist에는 파이썬 절대 경로가 박혀 있습니다
(`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`).
파이썬을 올리면 두 plist를 함께 고쳐야 합니다. `/usr/bin/python3`은 3.9라 쓸 수 없습니다.

## 운영

**초안을 직접 만들어보기 (전송 없음)**

```bash
python3 scripts/threads/compose.py --dry-run
python3 scripts/threads/compose.py --dry-run --project law
```

**로그**

```bash
tail -f ~/Library/Logs/threads-poster.log
```

**상태 확인**

```bash
ls -la ~/.local/state/threads-poster/
python3 -c "import json,os; print(len(json.load(open(os.path.expanduser('~/.local/state/threads-poster/posted.json')))))"
```

**대기 중인 초안 취소**

```bash
rm ~/.local/state/threads-poster/pending.json
```

**중단**

```bash
launchctl unload ~/Library/LaunchAgents/com.zihado.threads-compose.plist
launchctl unload ~/Library/LaunchAgents/com.zihado.threads-approve.plist
```

## 테스트

```bash
cd scripts/threads && python3 -m pytest tests -v
```

네트워크를 타지 않습니다. 실제 게시는 자동 테스트하지 않습니다.

## 동작 규칙

- 이미 소개한 프로젝트는 같은 회차에 다시 나오지 않습니다. 한 바퀴를 다 돌면 2회차가
  시작되고, 이때는 1회차 본문을 참고해 다른 각도로 씁니다
- 어제 초안이 승인 대기 중이면 오늘 초안을 만들지 않습니다 (초안이 쌓이지 않도록)
- 게시 중 실패하면 `pending.json`에 `creationId`가 남아, 다음 폴링에서
  **게시만** 재시도합니다. 같은 글이 두 번 올라가지 않습니다
- 재시도는 **6회** 또는 컨테이너 생성 후 **24시간**까지입니다. 넘기면 포기하고
  건너뛴 것으로 기록한 뒤 한 번만 알립니다. 실제로 올라갔는지 알 수 없으므로
  다시 뽑히지 않게 하고, 확인 후 `--project <slug>`로 직접 다시 올리면 됩니다
- 무언가 잘못돼 멈춘 것 같은데 알림이 안 왔다면 launchd 로그를 보세요:
  `tail -50 ~/Library/Logs/threads-poster.launchd.log`
- 이 시스템은 저장소를 `projects.json` 읽기 전용으로만 씁니다. 상태를 저장소에 쓰면
  `auto-update.sh`의 "워킹 트리가 더러우면 건너뛴다" 가드에 걸립니다

## 상태 파일

모두 `~/.local/state/threads-poster/` (권한 0700) 안에 있습니다.

| 파일 | 내용 |
|------|------|
| `posted.json` | 올린 기록 누적. 지우면 처음부터 다시 올립니다 |
| `pending.json` | 승인 대기 중인 초안. 있으면 새 초안을 만들지 않습니다 |
| `token.json` | Threads 장기 토큰 (권한 0600) |
| `offset.json` | 텔레그램 getUpdates offset |
| `lock` | flock 대상. 겹쳐 실행되면 두 번째는 즉시 종료 |

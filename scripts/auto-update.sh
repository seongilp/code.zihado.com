#!/bin/zsh
# 포트폴리오(code.zihado.com) 자동 업데이트
# launchd(com.zihado.portfolio-update)가 매일 21:00 KST에 실행.
# ~/work/playground의 새 디렉토리를 headless Claude가 조사해 쇼케이스에 추가하고,
# 결과를 텔레그램과 Discord로 알린다
# (~/.env의 TELEGRAM_BOT_TOKEN / AUTHORIZED_CHAT_ID / DISCORD_WEBHOOK_PORTFOLIO 사용).
set -euo pipefail

REPO="$HOME/work/playground/code.zihado.com"
LOG_DIR="$HOME/Library/Logs"
LOG="$LOG_DIR/portfolio-update.log"
CLAUDE="$HOME/.local/bin/claude"
# launchd 는 로그인 셸의 PATH 를 쓰지 않는다. /usr/bin/python3 는 3.9 라 쓸 수 없다.
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

# 텔레그램·Discord 자격증명 — 공개 저장소이므로 절대 커밋하지 말고 ~/.env에서만 읽는다
[[ -f "$HOME/.env" ]] && source "$HOME/.env"

notify_telegram() {
  local text="$1"
  if [[ -z "${TELEGRAM_BOT_TOKEN:-}" || -z "${AUTHORIZED_CHAT_ID:-}" ]]; then
    echo "WARN: 텔레그램 설정 없음 — 텔레그램 알림 생략"
  else
    curl -s -o /dev/null --max-time 15 \
      "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d chat_id="${AUTHORIZED_CHAT_ID}" \
      --data-urlencode text="$text" \
      -d disable_web_page_preview=true || echo "WARN: 텔레그램 전송 실패"
  fi
}

notify_discord() {
  local text="$1"
  if [[ -z "${DISCORD_WEBHOOK_PORTFOLIO:-}" ]]; then
    echo "WARN: Discord 웹훅 설정 없음 — 알림 생략"
  else
    "$PYTHON" "$REPO/scripts/discord.py" --message "$text" || echo "WARN: Discord 전송 실패"
  fi
}

# 실패·건너뜀 같은 운영 알림은 양쪽에 모두 보낸다
notify() {
  notify_telegram "$1"
  notify_discord "$1"
}

mkdir -p "$LOG_DIR"
exec >>"$LOG" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') portfolio auto-update start ====="

# set -e로 죽는 모든 실패에서 알림
trap 'notify "🔴 포트폴리오 자동 업데이트 실패 — 로그: ~/Library/Logs/portfolio-update.log"' ERR

if [[ ! -x "$CLAUDE" ]]; then
  echo "ERROR: claude CLI not found at $CLAUDE"
  notify "🔴 포트폴리오 자동 업데이트 실패 — claude CLI를 찾을 수 없음 ($CLAUDE)"
  exit 1
fi

# 저장소 이름을 바꾸면 여기가 먼저 깨진다. 조용히 죽지 말고 알린다.
if [[ ! -d "$REPO/.git" ]]; then
  echo "ERROR: repo not found at $REPO"
  notify "🔴 포트폴리오 자동 업데이트 실패 — 저장소 경로를 찾을 수 없음 ($REPO)
디렉토리 이름이 바뀌었다면 이 스크립트의 REPO 와
~/Library/LaunchAgents/com.zihado.portfolio-update.plist 의 경로를 함께 고쳐야 합니다."
  exit 1
fi

cd "$REPO"

# 마지막 실행 시각을 남긴다 — 오래됐으면 스케줄이 깨진 것
date '+%Y-%m-%d %H:%M:%S' > "$LOG_DIR/portfolio-update.lastrun"

# 사용자가 작업 중인 변경사항이 있으면 건드리지 않고 이번 주기는 건너뛴다
if [[ -n "$(git status --porcelain)" ]]; then
  echo "SKIP: 워킹 트리에 커밋 안 된 변경사항이 있어 이번 실행을 건너뜁니다."
  notify "🟡 포트폴리오 자동 업데이트 건너뜀 — code.zihado.com 저장소에 커밋 안 된 변경사항이 있어요. 정리 후 다음 주기(내일)에 다시 시도합니다."
  exit 0
fi

git pull --rebase origin main

# 스캔 전 커밋 — 끝난 뒤 이 시점과 비교해 "오늘 뭐가 발견됐는지"를 뽑는다
BEFORE=$(git rev-parse HEAD)

RESULT=$("$CLAUDE" -p "$(cat scripts/update-prompt.md)" \
  --model claude-sonnet-5 \
  --allowed-tools "Read,Write,Edit,Glob,Grep,Bash" \
  --max-turns 100)
echo "$RESULT"

SUMMARY=$(echo "$RESULT" | tail -n 12)
notify_telegram "🟢 포트폴리오 자동 업데이트 완료

${SUMMARY}

https://code.zihado.com"

# Discord 에는 요약 대신 "무엇이 발견됐는지"를 카드로 보낸다.
# 발견이 없는 날도 한 줄은 남긴다 — 조용하면 스케줄이 죽은 건지 알 수 없다.
if [[ -z "${DISCORD_WEBHOOK_PORTFOLIO:-}" ]]; then
  echo "WARN: Discord 웹훅 설정 없음 — 스캔 리포트 생략"
else
  "$PYTHON" "$REPO/scripts/discord.py" --scan-report "$BEFORE" \
    || echo "WARN: Discord 스캔 리포트 실패"
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') done ====="

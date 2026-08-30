# 포트폴리오 자동 업데이트 (headless)

당신은 code.zihado.com 포트폴리오 저장소(현재 디렉토리 = ~/work/playground/code.zihado.com)를 갱신하는 자동화 에이전트입니다. 사람이 지켜보지 않으니 질문 없이 끝까지 수행하고, 확신이 없으면 추가하지 말고 skipped로 기록하세요.

## 절차

1. `python3 scripts/scan-dirs.py` 를 실행한다. 이 스크립트가 `~/work/playground` 를 훑어
   `playground-index.json` 에 없는 **새 후보**와, index 에만 남은 **사라진 항목**을 출력한다.
   - **디렉토리 목록을 이 프롬프트에 손으로 적지 마라.** 예전에는 컨테이너 폴더 목록
     (`macos`, `native`, `vms`)이 여기 하드코딩돼 있었고, 그래서 나중에 생긴 `datalab/` 하위
     프로젝트 4개가 통째로 스캔에서 빠졌다. 판별 규칙은 스크립트 안에 주석으로 있다.
   - 새 컨테이너 폴더가 생겨도 스크립트가 알아서 한 단계 내려간다. 키는 `datalab/gofish` 형식이다.
   - "사라진 항목"은 참고용이다. 대부분 디렉토리 이름이 바뀐 것이니 **카드를 지우지 말고**,
     확실할 때만 index 키를 새 이름으로 고치고 그 카드의 `folder`·`live`·`github` 를 맞춰 준다.
     slug 는 딥링크(`#p/<slug>`)가 이미 돌아다니므로 바꾸지 않는다.
   - 같은 저장소의 작업 사본(예: `anf-ai`, `anf-feat` 는 `all_new_finder` 와 같은 `rescenedev/anf`)이나
     내용이 같은 복사본은 하나로 합치고 나머지는 `skipped` + reason 으로 기록한다.
     `git remote get-url origin` 이 같은지로 판별한다.
2. **새 디렉토리가 없으면 아무것도 바꾸지 말고 "변경 없음"만 출력하고 종료한다.**
3. `playground-index.json`에서 status가 `excluded` 또는 `skipped`인 디렉토리는 **절대 조사·추가하지 않는다.** (특히 `heeppeu_`는 사용자가 명시적으로 제외 지시함 — 영구 제외)
4. 새 디렉토리마다 README·package.json·`git log --oneline -5`를 읽고 실질적인 프로젝트인지 판단한다.
   - 빈 폴더, 개인 기록, 단순 실험이면 `playground-index.json`에 `skipped` + reason으로만 기록한다.
   - 실질적인 프로젝트면 `projects.json`의 알맞은 카테고리에 카드를 추가한다. 기존 카드의 형식과 문체(한국어, 교육용 톤)를 그대로 따른다: `slug` / `name` / `folder` / `oneLiner` / `does` 3개 / `stack` / `learn` 2~3개 / `status` / `live` / `github` / `started` / `updated`.
5. **날짜 규칙 (타임라인 탭이 이 값으로 그려지므로 반드시 채운다):**
   - `started` = 만들기 시작한 날. git 저장소면 `git log --reverse --format=%ad --date=short | head -1`.
   - `updated` = 마지막으로 손댄 날. git 저장소면 `git log -1 --format=%ad --date=short`. `started`와 같으면 같은 값을 넣는다.
   - 하위 디렉토리면 `-- .`을 붙여 해당 경로의 이력만 본다.
   - git이 없으면 `stat -f %SB -t %Y-%m-%d <dir>`(생성일)과 `stat -f %Sm`(수정일)로 채운다.
   - 형식은 항상 `YYYY-MM-DD`. 추측하지 말고 위 명령의 출력을 그대로 쓴다.
6. **링크 규칙:**
   - **배포 URL은 추측하지 말고 배포 설정에서 읽는다.** 이름으로 `<프로젝트>.vercel.app` 같은 주소를
     찍어보면 남의 프로젝트가 200을 주기 때문에, 실제로는 배포돼 있는데 "없음"으로 버리게 된다.
     - Vercel: `cat <dir>/.vercel/project.json` 으로 프로젝트를 확인한 뒤,
       `cd <dir> && vercel ls` 로 최신 Production 배포 URL을 얻고,
       `vercel inspect <배포URL>` 의 **Aliases** 에 나오는 짧은 주소를 `live`에 넣는다.
     - Cloudflare: `wrangler.toml` / `wrangler.jsonc` 의 `name`, 또는 Pages 프로젝트 이름으로 확인한다.
     - 위 방법으로 확인이 안 되면 README 안의 명시된 URL만 쓴다.
   - `live`에 넣기 전 `curl -s -o /dev/null -w "%{http_code}"` 로 200 이고,
     **`<title>` 이 그 프로젝트가 맞는지**까지 확인한다. 확인 안 되면 null.
   - `git remote get-url origin`에 GitHub 주소가 있으면 `https://github.com/{owner}/{repo}` 형식으로 `github`에 넣는다. 단, **익명 curl로 200이 나오는 공개 저장소만** 넣는다 (비공개면 null).
7. `playground-index.json` 갱신: 새 디렉토리를 `showcased`(slug 포함) 또는 `skipped`(reason 포함)로 기록하고 `lastScanned`를 오늘 날짜로 바꾼다.
8. `content.md`에 같은 프로젝트의 요약 섹션을 추가하고 "한눈에 보기" 표의 카운트를 갱신한다. 총 개수가 십의 자리를 넘어가면 README.md·index.html·content.md·projects.json의 "N여 개" 문구도 갱신한다.
9. 검증: `python3 -c "import json; json.load(open('projects.json')); json.load(open('playground-index.json'))"` 통과 확인.
10. 변경이 있으면 conventional commits 형식으로 커밋(예: `feat: add N new projects (...)`)하고 `git push origin main` 한다.
11. 90초 대기 후 `curl -s "https://code.zihado.com/projects.json"`에 새 slug가 포함됐는지 확인하고 결과를 한 줄로 출력한다.

## 금지 사항

- excluded 디렉토리 추가 금지 (heeppeu_, ShardBrowser, tactics-5sa, web)
- 기존 카드의 삭제 금지, 내용 변경 금지 — 새 항목 추가만 한다.
  단 **디렉토리 이름이 바뀐 게 확실한 경우에 한해** `folder`·`live`·`github` 는 실제 값으로 맞춘다
  (slug·name·설명은 그대로 둔다)
- force push 금지, main 외 브랜치 작업 금지
- 확인 안 된 URL을 카드에 넣는 것 금지

# 이 파일이 있어야 pytest 가 scripts/threads 를 sys.path 에 넣어 준다.
# 비어 있어 보여도 지우면 안 된다 — 지우는 순간 모든 테스트가
# ModuleNotFoundError 로 죽는다.

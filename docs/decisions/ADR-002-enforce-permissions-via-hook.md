# ADR-002: 권한은 문서가 아니라 PreToolUse hook으로 강제한다

- 상태: accepted
- 날짜: 2026-07-17
- 도메인: harness
- 관련 루프/문서: harness/permissions.policy.md, .claude/hooks/enforce_permissions.py, .claude/settings.json

## 맥락
CLAUDE.md에 "rag-worker는 backend/를 건드리지 마"라고 적어도, CLAUDE.md는 컨텍스트(부탁)이지
강제(법)가 아니다. Claude가 무시할 수 있다. 도메인 경계를 실제로 통제하려면 결정적 강제 장치가 필요하다.

## 대안
- (A) CLAUDE.md/AGENTS.md에 규칙만 기술 — 강제력 없음, Agent가 놓칠 수 있음.
- (B) `settings.json`의 `permissions.deny` 규칙 — 도구/명령 단위 정적 차단은 되지만
  agent_type별·경로별 세밀한 정책과 위반 로깅을 담기 어려움.
- (C) `PreToolUse` hook 스크립트가 permissions.policy.md를 코드로 미러링해 강제 + 위반 시 로깅.

## 결정
(C). `.claude/hooks/enforce_permissions.py`가 PreToolUse에서 agent_type·경로·명령을 검사해
`permissionDecision: deny`를 반환하고, 차단 이벤트를 `docs/agent-control-log.md`에 남긴다.

## 근거
- 참고자료(클로드_코드_구조.pdf)의 명제 "CLAUDE.md는 부탁, hooks는 법"과 일치.
- 평가 기준의 "가드레일(제약·체크) 설계"(PDF §5.2) 항목을 실물로 보여줄 수 있음.
- 위반 로깅이 곧 "Agent 통제 과정" 증거(산출물 ①)가 된다.

## 시행착오 / 검증
- 참고 PDF의 `settings.json` hooks 등록 예시가 실제 스키마와 달랐다(문자열 배열 `["...sh"]`).
  공식 문서(code.claude.com/docs/en/hooks)와 대조해 `matcher`+`hooks`+`type` 구조로 바로잡았다.
- 같은 PDF가 "SessionStart는 비공식 이벤트"라 서술했으나, 공식 문서상 실재하는 이벤트임을 확인(반영 안 함).
- hook을 14개 시나리오(도메인 밖 쓰기/읽기, 배포·파괴적 명령, verifier 전용 차단, 정상 허용,
  관할 밖 subagent 통과)로 stdin 주입 테스트 → 전부 기대대로 동작 확인.
- 알려진 한계(Bash 패턴 매칭 우회 가능, Grep/Glob path 미지정 시 미강제)는 스크립트 docstring에 명시.

## 결과 / 영향
- 생성: `.claude/hooks/enforce_permissions.py`, `.claude/settings.json`.
- 단일 원본: `harness/permissions.policy.md`(사람이 편집) → hook의 POLICY dict가 이를 손으로 미러(드리프트 주의).
- 되돌리기 비용: 낮음(settings.json에서 hook 등록 제거). 단, 강제가 사라지면 통제는 문서 부탁으로 후퇴.

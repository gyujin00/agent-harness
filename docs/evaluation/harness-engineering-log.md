# harness-engineering-log.md — 하네스 엔지니어링 기록 (평가 산출물 ②)

과제 PDF §6이 요구하는 "설계한 프롬프트 전략·검증 루프·가드레일, 적용 결과와 개선 시도".
`harness/*.md`가 정책의 **현재 상태(무엇)**라면, 이 문서는 그 뒤의 **왜·무엇을 시도·무엇이 개선/실패**다.
정책 파일만 봐서는 안 보이는 설계 서사를 남겨, 발표에서 "어떻게 고도화했는가"를 바로 꺼내 쓴다.

## 설계 원리 (하네스가 무엇을 강제하는가)

우리 하네스의 통제 장치는 4겹이다. 각각 "부탁"이 아니라 "구조·강제"로 구현했다.

| 통제 장치 | 무엇 | 강제 방식 | 근거 ADR |
|-----------|------|-----------|----------|
| 계층 분리 | 환경(통제) vs 실행(반복) | 폴더·문서 구조 | ADR-001 |
| 권한 가드레일 | 도메인 밖 쓰기/읽기·배포·파괴 명령 차단 | PreToolUse hook(deny) | ADR-002 |
| 컨텍스트 스코프 | 정책을 필요할 때만 로드 | .claude/rules + paths frontmatter | ADR-003 |
| 검증 분리 | work ≠ verify | 별도 verifier + verification.policy.md | (기존 설계) |

## 검증 루프 설계

- **결정성 스펙트럼으로 도메인을 나눴다.** backend(결정적: test/contract) → frontend(준결정적:
  typecheck/build/a11y) → ai(비결정적). AI는 통과 기준을 사람이 못 만들어서, `eval/`이 verify를 대신한다
  (정답셋으로 retrieval@k·faithfulness·answer_relevancy를 재고 `thresholds.yaml` 기준선과 비교).
- **코드뿐 아니라 문서도 검증한다.** 2차 미팅 피드백을 받아 `verification.policy.md`에 산출물별
  검증 기준(도메인 문서·API 명세·ERD·화면 명세)을 명문화하고 verifier에 doc-verify 게이트를 추가했다.
- **실패는 되돌린다.** 게이트 실패 시 `on_fail: back_to_action`으로 worker에게 반환, N회 초과 시 Human Approval.

## 가드레일 설계와 그 한계 (정직한 기록)

- hook은 agent_type이 있는 subagent에만 경로 정책을 적용하고, 메인 세션(사람 직접 작업)은
  파괴적 명령만 막는다 — 사람의 정당한 메타 작업을 과잉 차단하지 않기 위한 설계 선택.
- **알려진 한계**: (1) Bash 명령 필터는 문자열/정규식 매칭이라 변수 조립 등으로 우회 가능.
  (2) Grep/Glob은 path 인자가 없으면 강제하지 않음. (3) 정책은 permissions.policy.md에서 자동 파싱하지
  않고 hook의 POLICY dict로 손 미러 → 드리프트 위험. 이 3가지는 스크립트 docstring에 명시했고, v2 개선 대상.

## 개선 시도 이력 (시행착오)

### 시도 1 — @import 남발 → 컨텍스트 낭비 발견 → rules 스코프로 개선
초기 CLAUDE.md는 `harness/*`를 전부 `@import`했다. 참고 PDF 검토 중 `.claude/rules/` + `paths`
frontmatter가 "필요할 때만 로드"를 지원함을 확인, 심볼릭 링크로 전환해 CLAUDE.md를 200줄 예산 → 15줄로 줄였다.
원본은 harness/ 한 곳에 남아 단일 원본도 지켰다. (→ ADR-003)

### 시도 2 — 참고자료 무비판 수용의 위험 → 공식 문서 교차검증 습관화
제공된 참고 PDF(클로드_코드_구조)에 hook 스키마 오류가 있었다: settings.json을 문자열 배열로 표기,
`SessionStart`를 비공식 이벤트로 오분류, permissions를 `git:push`로 표기. 공식 문서로 대조해
`matcher`+`hooks`+`type` 구조와 `Tool(specifier)` 문법으로 바로잡았고, 틀린 부분은 반영하지 않았다.
교훈: 하네스에 넣는 규칙은 출처가 좋아 보여도 공식 문서로 검증 후 반영한다. (→ ADR-002 시행착오)

### 시도 3 — orchestrator 권한 잠재 불일치 발견 → 흡수 작업 중 동시 해소
Sprint/Task(plans/) 흡수 중, orchestrator.spec은 "agent-control-log에 record한다"는데
permissions.policy는 orchestrator write를 비워둔 모순을 발견했다. plans/ 쓰기 권한을 추가하며
`docs/agent-control-log.md` 쓰기도 함께 허용해 불일치를 해소했다. (→ ADR-004)

### 시도 4 — 번호폴더 전면 이식의 유혹 → 철학 충돌 판단 → 개념만 흡수
현업 이사님의 11개 번호폴더는 매력적이었으나 문서화 중심 SI 구조라 우리 실행 하네스와 철학이 달랐다.
전면 재구조화 대신 알맹이 4개(계획 계층·문서 검증·추적성·현재 상태)만 흡수해 리스크를 낮췄다. (→ ADR-004)

## 다음 고도화 후보 (v2)

- permissions.policy.md 표를 hook이 자동 파싱하도록 승격(손 미러 제거 → 드리프트 원천 차단).
- Bash 명령 가드레일을 allowlist 방식으로 강화.
- eval/run-eval.py 스코어러를 실제 ai/ 파이프라인에 연결해 verify 루프를 실증.
- 첫 Sprint→Task→loop→verify→record 1회전을 돌려 전체 하네스를 end-to-end 검증.

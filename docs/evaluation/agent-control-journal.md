# agent-control-journal.md — Agent 활용·통제 기록 (평가 산출물 ①)

과제 PDF §6이 요구하는 "Agent에 부여한 목표·맥락·제약, 주요 프롬프트, 결과 판단·교정 과정"의 서술 기록.
`agent-control-log.md`가 기계용 이벤트 로그(DELEGATE/BLOCK/RETRY)라면, 이 문서는 **사람이 읽는 서사**다.
"무엇을, 어떻게 지시했고, 결과를 어떻게 판단·교정했는가"를 회차별로 남긴다.

## 기록 템플릿

```
## [YYYY-MM-DD] 회차 제목
- 목표(Goal): 이번에 Agent에게 시킨 최종 목표
- 맥락(Context): Agent에게 준 배경·참고 자료
- 제약(Constraint): 하면 안 되는 것, 지켜야 할 규칙
- 주요 지시(Prompt): 실제로 준 핵심 지시(요지)
- 결과 판단(Judgment): 나온 결과를 무엇을 기준으로 합격/불합격 판단했나
- 교정(Correction): 어디를 어떻게 되돌리거나 고쳤나
- 산출물: 생성/변경 파일, 관련 ADR·로그
```

---

## [2026-07-17] 회차 1 — 하네스 골격 자동 생성(agent-specs → .claude/agents)

- 목표: `agent-specs/*.spec.md`를 Claude Code가 읽는 `.claude/agents/*.md`로 변환하는 파생 체계 구축.
- 맥락: HANDOFF.md "다음 작업 1번". 단일 원본(spec) → 파생(agent) 원칙 유지가 전제.
- 제약: `.claude/agents`를 손편집하지 말 것(파생물), spec 형식·권한 정책과 일관 유지.
- 주요 지시: spec의 frontmatter를 파싱해 name/description/tools로 매핑하는 생성 스크립트를 만들어라.
- 결과 판단: 5개 spec → 5개 agent 생성 후 `--check` 재실행으로 멱등성(재생성 시 변화 0) 확인 → 합격.
- 교정: tools 매핑을 스크립트에 두되, 경로 단위 강제는 hook 몫으로 역할 분리(스크립트 주석에 명시).
- 산출물: `scripts/generate_agents.py`, `.claude/agents/*`(5), ADR-005.

## [2026-07-17] 회차 2 — 권한 가드레일(PreToolUse hook)

- 목표: permissions.policy.md의 경로·명령 권한을 문서가 아니라 실제로 강제.
- 맥락: 도메인 경계(rag-worker ↛ backend/ 등)를 통제해야 하는데 CLAUDE.md는 강제력이 없음.
- 제약: 메인 세션(사람 직접 작업)은 과도 차단하지 말 것, 파괴적 명령은 전 Agent 공통 차단.
- 주요 지시: PreToolUse hook으로 agent_type·경로·명령을 검사해 deny 반환하고 위반을 로깅하라.
- 결과 판단: 14개 시나리오 stdin 주입 테스트 전부 기대대로(허용/차단) → 합격.
- 교정: 참고 PDF의 settings.json 스키마 오류를 공식 문서로 대조·수정(→ ADR-002 시행착오).
- 산출물: `.claude/hooks/enforce_permissions.py`, `.claude/settings.json`, ADR-002.

## [2026-07-17] 회차 3 — 참고자료 검증 후 정책을 rules로 전환

- 목표: 참고 PDF(클로드_코드_구조) 검토 + 유효한 개선점 적용.
- 맥락: 사용자가 "레퍼런스로 좋다"며 제공. 우리 구조와 대조가 필요.
- 제약: 참고자료라도 무비판 수용 금지 — 공식 문서로 사실 검증 후 반영.
- 주요 지시: 검토하고, 맞으면 우리 하네스에 적용하라.
- 결과 판단: PDF의 3개 오류(hook 이벤트 목록/ SessionStart 오분류/ settings.json·permissions 문법)를
  공식 문서로 확인 → 반영하지 않음. `.claude/rules` 경로 스코프는 우리 @import보다 나음 → 반영.
- 교정: harness/* 정책을 심볼릭 링크 + paths frontmatter로 전환, CLAUDE.md 15줄로 축소.
- 산출물: `.claude/rules/*`, ADR-003.

## [2026-07-17] 회차 4 — 이사님 2차 미팅 피드백 흡수

- 목표: 현업 이사님 피드백의 핵심을 하네스에 반영.
- 맥락: 같은 회의의 두 전사본(내용정리/클로바노트) 제공. 상충 없음, 클로바노트가 더 상세.
- 제약: 이사님의 번호폴더 구조를 그대로 이식하면 2계층 철학과 충돌 — 개념만 취할 것.
- 주요 지시: 피드백·추천을 도입하라(도입 수준은 사용자 확인 후 "개념만 흡수"로 확정).
- 결과 판단: hook 10개 회귀 시나리오 + 심볼릭 링크·frontmatter·agents 최신성 전부 통과 → 합격.
- 교정: orchestrator 권한에 plans/ 쓰기를 추가하며 기존 잠재 불일치(record는 하는데 write 권한 없음)도 해소.
- 산출물: `plans/`, `harness/verification.policy.md`, `docs/traceability.md`, `docs/project-state.md`, ADR-004.

## [2026-07-17] 회차 5 — 평가 산출물 3종 정리(이 문서 포함)

- 목표: 과제 PDF §6의 코드 외 핵심 산출물 3종(Agent 통제/하네스 기록/의사결정)을 채움.
- 맥락: 평가가 완성도가 아니라 과정·통제·근거를 본다는 점을 PDF에서 재확인.
- 제약: 있었던 결정·시행착오를 사실대로 소급 정리(각색 금지).
- 주요 지시: 3개 카테고리를 채워라.
- 결과 판단: (진행 중) 각 산출물이 PDF 평가 항목과 1:1 매핑되는지 `evaluation-map.md`로 확인.
- 교정: (해당 시 추가)
- 산출물: 이 문서, `harness-engineering-log.md`, `docs/decisions/ADR-001~005`, `evaluation-map.md`.

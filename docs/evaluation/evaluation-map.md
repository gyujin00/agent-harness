# evaluation-map.md — 과제 평가기준 ↔ 산출물 매핑 (발표용)

과제 PDF([과제4] 바이브코딩 기반 AI SRM 구축)의 평가 기준과 이 저장소의 산출물을 1:1로 연결한다.
발표·면접에서 "그 근거가 어디 있나"에 즉답하기 위한 인덱스.

## 핵심 전제 (PDF §1.1, §6, §9)
> "구현 완성도는 평가의 중요 요소가 아니다. 코드 외 산출물이 핵심 평가 대상이다."
> 평가 관점: Agent 통제력 · 하네스 엔지니어링 · 문제분해/PM · 산출물·문서화 · 풀스택 결과 · 협업/발표.

## 평가 산출물 3종 (PDF §6) ↔ 우리 문서

| PDF 평가 산출물 | 우리 산출물 | 성격 |
|-----------------|-------------|------|
| ① Agent 활용·통제 기록 (목표·맥락·제약, 주요 프롬프트, 결과 판단·교정) | `agent-control-journal.md`(서사) + `docs/agent-control-log.md`(이벤트) | 회차별 통제 서술 + 기계 로그 |
| ② 하네스 엔지니어링 기록 (전략·검증 루프·가드레일, 적용 결과·개선 시도) | `harness-engineering-log.md` + `harness/*.md` + `harness_runtime/` + `tests/` | 설계 서사(왜) + 정책(무엇) + 실행·회귀 검증(실물) |
| ③ 의사결정·시행착오 문서 (범위·기술 선택 근거, 막힌 지점·해결) | `docs/decisions/ADR-001~005` + `adr-index.md` | 실제 결정 5건, 대안·시행착오 포함 |
| 동작 결과물·소스 (완성도 자체는 핵심 아님) | `ai/` FR-017 RAG + `harness_runtime/` 공용 실행기 | 제품 기능과 그 기능을 만드는 통제 시스템 |
| 발표 자료 | (예정) `docs/`의 위 산출물 기반 | 과정·판단 설명 |

## 평가 역량(PDF §2.2) ↔ 근거

| 역량 영역 | 확인 항목 | 우리 근거 |
|-----------|-----------|-----------|
| Agent 통제력 | 목표·제약·맥락 부여, 검증·교정 | `agent-control-journal.md`, hook 차단 로그, `docs/runs/*/events.jsonl` |
| 하네스 엔지니어링 | 반복 프롬프트·검증 루프·가드레일 설계·개선 | `harness-engineering-log.md`, `harness_runtime/`, `tests/test_fail_retry_pass.py` |
| 문제 분해·PM | 작업 단위 분해, 우선순위·범위 관리 | `plans/`(Sprint→Task 점진 생성), P0~P3 액션(미팅 정리본) |
| 산출물·문서화 | 의사결정·시행착오·근거 정리 | `docs/decisions/ADR-*`, 두 로그 저널 |
| 풀스택 결과 | BE·FE 연동 동작 | `loops/{backend,frontend}.loop.yaml` + `openapi.yaml` 계약(구축 예정) |
| 협업·발표 | Git 협업, 과정 설명 | Git 단일 원본 원칙(AGENTS.md), `project-state.md` |

## 발표 3대 메시지(2차 미팅 확정) ↔ 근거

| 메시지 | 근거 산출물 |
|--------|-------------|
| 무인화 | `harness_runtime/orchestrator.py`가 loop의 worker→verifier→retry→record→Draft PR를 실행 |
| 드리프트 방지 | 헌법(AGENTS.md) 고정 + ADR 변경 통제 + verify 회귀 + 권한 hook |
| 재사용성 | 같은 Task Contract로 Claude worker↔Codex verifier를 교차 선택하는 provider 어댑터 |

## 아직 비어 있는 곳 (정직하게)
- 실제 인증·비용을 사용한 새 Task의 Claude/Codex 교차 provider smoke run.
- UI·API·DB 최소 연결과 발표 자료.
- 위 진행 단면은 항상 `docs/project-state.md`에서 확인.

# 설계: 루트/문서 폴더 가독성 개선

- 날짜: 2026-07-17
- 상태: 승인됨 (브레인스토밍 대화에서 사용자 승인, 구현 전)
- 관련 문서: `AGENTS.md`, `README.md`, `HANDOFF.md`, `harness/permissions.policy.md`,
  `.claude/hooks/enforce_permissions.py`

## 배경 / 문제

`agent-harness`는 루트에 폴더 12개(`.claude`, `.worktrees`, `agent-specs`, `ai`, `backend`,
`docs`, `eval`, `frontend`, `harness`, `loops`, `plans`, `requirements`, `scripts`) + 느슨한
파일 6개(`AGENTS.md`, `CLAUDE.md`, `HANDOFF.md`, `README.md`, `design-tokens.json`,
`openapi.yaml`)가 있다. 사용자가 지적한 구체적 문제 3가지:

1. `README.md`와 `HANDOFF.md`가 "두 계층 구조", "폴더 지도", "2차 미팅 피드백" 내용을 거의 그대로
   중복 설명해서 어느 걸 먼저 읽어야 할지 불명확하다.
2. `docs/` 폴더 하나에 실행 기록(`harness-log.md`, `traceability.md`, `agent-control-log.md`,
   `project-state.md`)과 평가 산출물(`agent-control-journal.md`, `harness-engineering-log.md`,
   `evaluation-map.md`, `decisions/`)이 섞여 있어 성격이 다른 문서를 구분하기 어렵다.
3. 루트 폴더 개수 자체가 많아 파편화된 느낌을 준다.

## 범위 제약 (브레인스토밍에서 확정)

이 저장소는 `permissions.policy.md`·`.claude/hooks/enforce_permissions.py`·
`loops/*.loop.yaml`·`.claude/rules`가 **정확한 경로 문자열**로 참조하는 강제 규칙 시스템이다.
사용자와 함께 리스크를 짚은 결과, 다음은 **이번 작업 범위에서 제외**한다(겉보기 정리보다 강제
규칙이 조용히 깨지는 위험이 크다고 판단):

- 도메인 코드 폴더: `backend/`, `frontend/`, `ai/`, `eval/`, `loops/`, `agent-specs/`, `harness/`
  — hook POLICY와 permissions.policy.md 표가 그대로 참조.
- 계약 파일: `openapi.yaml`, `design-tokens.json` — `backend-worker`/`frontend-worker`의
  write/read_allow에 정확한 파일명으로 등록됨.
- `plans/` — 모든 worker의 read_allow, orchestrator의 write_allow에 등록됨.
- `docs/harness-log.md`, `docs/traceability.md`, `docs/agent-control-log.md` — verifier/
  orchestrator의 write_allow에 정확한 경로로 등록됨. `docs/project-state.md`도 이 3개와 같은
  "실행 기록" 성격이라 함께 `docs/` 루트에 유지한다(AGENTS.md §4.1 그대로).
- `docs/superpowers/` — 이 세션의 브레인스토밍/계획 산출물(그 자체가 완료된 작업의 역사적 기록).
- `.claude/`, `.git/`, `.worktrees/` — 플랫폼/git 자체 관례.

**이번 작업이 실제로 건드리는 것**: 루트의 4개 안내 문서(`AGENTS.md`/`CLAUDE.md`/`HANDOFF.md`/
`README.md`) 정리와, `docs/` 안의 "평가 산출물 3종"(`agent-control-journal.md`,
`harness-engineering-log.md`, `evaluation-map.md`)을 새 하위 폴더로 옮기는 것뿐이다.

## 결정

### A. `HANDOFF.md`를 `README.md`에 흡수하고 삭제

새 `README.md` 섹션 구성 (기존 README.md + HANDOFF.md의 고유 내용 통합, 중복 제거):

1. 제목 + 한 줄 설명 — SRM 기능 저장소가 아니라 작업 시스템 자체, 도메인 중립적 재사용 가능
2. 두 계층 모델 (환경/실행)
3. 핵심 규칙 3가지
4. 폴더 지도 — `requirements/`, `ai/`(실제 구현 존재), `docs/evaluation/`(신설)까지 반영해 최신화
5. 평가 산출물 안내 (과제 PDF §6) — 새 경로(`docs/evaluation/`) 반영
6. **"지금 상태는 어디서 보나"** — 상세 체크리스트를 넣지 않고 `docs/project-state.md`로 포인터만.
   HANDOFF의 "지금까지 안 된 것" 체크리스트는 project-state.md와 중복이었으므로 옮기지 않고 버린다
   (project-state.md가 이미 최신 상태를 갖고 있음 — 정보 손실 아님, 중복 제거).
7. 새 세션/다른 프로젝트 시작 가이드 — HANDOFF의 "코워크 첫 지시 예시"를 최신화. `/intake` 커맨드가
   생긴 이후 기준으로 "PRD/FRD를 `requirements/`에 넣고 `/intake` 실행"으로 갱신.

`HANDOFF.md` 파일은 삭제한다.

### B. `docs/evaluation/` 신설

```bash
mkdir docs/evaluation
git mv docs/agent-control-journal.md docs/evaluation/agent-control-journal.md
git mv docs/harness-engineering-log.md docs/evaluation/harness-engineering-log.md
git mv docs/evaluation-map.md docs/evaluation/evaluation-map.md
```

`docs/evaluation/README.md` 신설(짧은 안내):
```markdown
# docs/evaluation/ — 평가 산출물 3종 (과제 PDF §6)

완성도가 아니라 과정·통제·근거를 보는 산출물. AGENTS.md §4.2 참고.

- `agent-control-journal.md` — ① Agent 활용·통제 기록(서사)
- `harness-engineering-log.md` — ② 하네스 엔지니어링 기록(설계 근거·시행착오)
- `evaluation-map.md` — 평가기준↔산출물 매핑(발표용 인덱스)

ADR(③ 의사결정·시행착오)은 `../decisions/`에 있다 — 이미 잘 알려진 컨벤션이라 별도로 옮기지
않고 `docs/decisions/`에 유지한다.
```

`docs/decisions/`(ADR)는 옮기지 않는다 — 접근 2로 검토했으나, 발표·평가자가 찾기 쉬운 위치를
유지하는 것과 세션 전체에 걸친 `docs/decisions/ADR-XXX` 인용 수십 곳을 다 고치는 비용이
안 맞다고 판단해 기각.

### C. 참조 갱신 대상 (grep으로 확인 완료)

**갱신이 필요한 곳 (현재 상태를 설명하는 살아있는 문서)**:
- `AGENTS.md` §4.2 (68~71번째 줄 부근) — 세 파일 경로를 `docs/evaluation/*`로.
- `docs/project-state.md` (36~39번째 줄 부근) — 같은 세 파일 경로 갱신.
- `README.md` — 통째로 다시 쓰므로 자동으로 새 경로 반영.

**갱신하지 않는 곳 (역사 기록 — 이 세션에서 이미 확립한 원칙: 그 시점에 참이었던 사실은 안 고침)**:
- `docs/harness-log.md`의 과거 항목들 (`HANDOFF.md`, `harness-engineering-log.md` 등을
  옛 경로로 언급) — 세션별 이력이라 손대지 않는다.
- `docs/decisions/ADR-006-*.md`의 "결과/영향" 절의 `HANDOFF.md` 언급 — ADR이 만들어진 시점에
  실제로 `HANDOFF.md`를 고쳤다는 사실 기록이라 손대지 않는다(ADR-005가 `rag-worker.md`를
  그대로 남긴 것과 같은 원칙).
- `docs/superpowers/plans/2026-07-17-generic-harness-intake.md`,
  `docs/superpowers/specs/2026-07-17-generic-harness-intake-design.md` — 이미 실행 완료된
  계획/설계 문서 자체. 과거 시점의 계획 텍스트이므로 손대지 않는다.
- `docs/agent-control-journal.md`(이동 후 `docs/evaluation/agent-control-journal.md`)와
  `docs/evaluation-map.md`가 서로를 파일명만으로(경로 접두어 없이) 참조하는 부분은, 이동 후에도
  같은 폴더에 나란히 있게 되므로 그대로 유효하다 — 수정 불필요.

**검증 기준**: 저장소 전체에서 `HANDOFF.md`, `docs/agent-control-journal.md`,
`docs/harness-engineering-log.md`, `docs/evaluation-map.md`를 grep했을 때, 위 "갱신하지 않는 곳"
목록에 있는 파일들 외에는 매치가 남아있지 않아야 한다(끊어진 링크 0건).

## 최종 구조 (변경 후)

```
agent-harness/
├── AGENTS.md              헌법(단일원본, 위치 불변)
├── CLAUDE.md               파생(위치 불변, Claude Code 규약)
├── README.md               ★ 유일한 온보딩 진입점 (HANDOFF.md 흡수, 삭제됨)
├── agent-specs/ ai/ backend/ frontend/ eval/ harness/ loops/   ← 이번 작업 범위 밖, 불변
├── plans/ requirements/ scripts/                               ← 이번 작업 범위 밖, 불변
├── openapi.yaml design-tokens.json                             ← 이번 작업 범위 밖, 불변
└── docs/
    ├── harness-log.md · traceability.md · agent-control-log.md · project-state.md  (실행 기록, 불변 위치)
    ├── decisions/        (ADR, 불변 위치)
    ├── evaluation/        ★ 신설 — journal · engineering-log · evaluation-map + README
    └── superpowers/        (불변)
```

## 테스트/검증 계획

1. `git mv`로 이동(히스토리 보존), `HANDOFF.md`는 `git rm`.
2. 위 "갱신이 필요한 곳" 3곳을 정확히 고쳤는지 diff로 확인.
3. 저장소 전체 grep으로 "갱신하지 않는 곳" 외에 옛 경로/파일명이 남아있지 않은지 확인(빈 결과가
   기대값).
4. `python scripts/generate_agents.py --check`로 이번 변경이 agent 파생물에 영향 없음을 재확인
   (건드리는 파일이 `agent-specs/`가 아니므로 기대상 영향 없어야 함 — 그래도 회귀 확인 차원).
5. hook 재검증은 불필요(이동 대상 파일이 `permissions.policy.md`/hook POLICY 어디에도 경로로
   등록돼 있지 않음을 이미 확인함) — 다만 안전 차원에서 `.claude/hooks/enforce_permissions.py`를
   grep해 이번에 옮기는 3개 파일명이 POLICY dict에 없다는 것만 다시 한번 확인한다.

## 정직한 한계

- `docs/decisions/`(ADR)를 옮기지 않기로 해서, "평가 산출물 3종"이 물리적으로 완전히 한 곳에
  모이지는 않는다 — `docs/evaluation/README.md`의 안내 링크로 이 간극을 메운다.
- 이 작업은 "가독성"이 목적이라 도메인 폴더 구조 자체(백엔드/프론트엔드/AI 3분할)는 그대로다 —
  그 구조가 복잡하게 느껴진다면 이건 별도 논의가 필요하다(이번 범위 아님).

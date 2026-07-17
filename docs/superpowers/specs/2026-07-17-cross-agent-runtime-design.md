# 설계: Claude Code·Codex 공용 자율 개발 런타임

- 날짜: 2026-07-17
- 상태: 사용자 방향 승인 후 상세 설계 작성, 구현 전 검토 대기
- 대상 저장소: `agent-harness`
- 핵심 목표: AI가 요구사항을 구현하고, 독립 검증 실패를 근거로 재작업하며, 증거가 포함된 PR까지
  생성하는 과정을 Claude Code와 Codex에서 동일하게 실행한다.

## 1. 문제 정의

현재 저장소에는 `AGENTS.md`, `agent-specs/`, `loops/`, `harness/`, `eval/`, `plans/`가 있어
하네스와 루프의 **규칙**은 정의되어 있다. 그러나 `loops/*.loop.yaml`은 선언 파일일 뿐 다음 동작을
실제로 수행하는 실행기가 없다.

1. Task Contract를 읽고 실행 컨텍스트를 구성한다.
2. 격리 worktree에서 Claude Code 또는 Codex worker를 실행한다.
3. worker와 분리된 verifier를 새 컨텍스트로 실행한다.
4. 실패 결과를 구조화해 worker에게 돌려보낸다.
5. 통과한 변경만 기록하고 PR을 만든다.
6. merge·deploy 같은 비가역 작업은 사람에게 남긴다.

따라서 이 작업의 산출물은 또 하나의 프롬프트 모음이 아니라, 기존 선언을 실제 상태 전이로 만드는
**공급자 중립 실행 런타임**이다.

## 2. 성공 조건

다음 시나리오가 재현되면 성공이다.

> 개발자가 `plans/task-XXX.md` 하나를 지정하고 worker/verifier 공급자를 선택하면, 런타임이
> 격리 worktree 생성 → worker 구현 → 잠긴 게이트 실행 → fresh-context verifier 판정 →
> 실패 피드백과 제한된 재시도 → 실행 증거 기록 → PR 생성을 수행하고 멈춘다.

구체적인 완료 조건:

- 같은 Task를 `Claude worker + Codex verifier`, `Codex worker + Claude verifier` 조합으로 실행할 수
  있다.
- worker와 verifier는 별도 CLI 프로세스·별도 세션으로 실행된다.
- verifier는 코드·Task Contract·잠긴 평가 기준을 수정할 수 없다.
- 평가 기준이나 허용 경로를 바꿔서 통과시키려는 변경은 실패한다.
- 재시도 횟수, 비용, 시간 제한이 프롬프트가 아니라 런타임에서 강제된다.
- 모든 상태 전이와 판정은 JSONL 및 사람이 읽는 요약으로 남는다.
- 런타임은 commit·push·PR 생성까지만 수행할 수 있고 merge·deploy 명령은 제공하지 않는다.
- 실제 모델 호출 없이도 fake provider로 `FAIL → back_to_action → PASS → record` 통합 테스트가
  가능하다.

## 3. 비목표

- GitHub PR merge와 운영 배포 자동화
- Claude Code와 Codex의 내부 동작을 완전히 동일하게 만드는 것
- 하나의 장기 세션이 worker와 verifier 역할을 번갈아 수행하게 하는 것
- AI가 평가 데이터·검증 스크립트·권한 정책을 수정한 뒤 그 기준으로 자신을 통과시키는 것
- 모든 IDE나 AI 코딩 도구를 한 번에 지원하는 것
- 첫 구현에서 스케줄 기반 Ops loop와 여러 Task 병렬 스케줄러까지 완성하는 것

첫 구현은 `human.goal`로 시작하는 단일 Task Goal loop에 집중한다. Ops loop와 병렬 실행은 동일한
상태 머신 위에 후속 확장한다.

## 4. 접근 방식 비교

### A. 공용 문서와 프롬프트만 제공

- 장점: 가장 단순하고 기존 저장소 변경이 적다.
- 단점: 재시도·권한·상태 전이가 실행되지 않으며 “자동 하네스”를 증명할 수 없다.
- 판단: 현재 저장소가 이미 이 단계이므로 채택하지 않는다.

### B. `.claude/`와 `.codex/`에 별도 실행 흐름 구현

- 장점: 각 도구의 고유 기능을 빠르게 활용할 수 있다.
- 단점: 두 구현의 권한·검증·재시도 기준이 쉽게 달라지고 평가 증거도 이중화된다.
- 판단: 파생 어댑터에만 공급자별 차이를 허용하고, 핵심 로직을 중복하지 않는다.

### C. 공급자 중립 런타임 + 얇은 CLI 어댑터 — 채택

- 장점: 상태 머신·통제·기록이 하나이며 worker/verifier 공급자를 자유롭게 교차할 수 있다.
- 단점: 초기 런타임과 테스트 코드가 필요하다.
- 판단: 이 과제에서 보여줘야 하는 “AI를 도구와 무관하게 통제한 방법”에 가장 적합하다.

## 5. 단일 원본과 파생 표면

### 단일 원본

- `AGENTS.md`: 프로젝트 헌법과 사람 승인 경계
- `harness/*.md`: 권한·worktree·검증·connector 정책
- `agent-specs/*.spec.md`: 역할별 책임·금지·반환 계약
- `loops/*.loop.yaml`: 도메인별 target/action/verify/record
- `plans/task-XXX.md`: Task Contract의 단일 원본
- `eval/*`: AI 기능의 잠긴 평가 세트와 기준선

### 도구별 파생 표면

- Claude Code:
  - `CLAUDE.md`가 `AGENTS.md`를 import
  - `.claude/agents/*.md`와 `.claude/hooks/` 사용
- Codex:
  - 루트 `AGENTS.md`를 직접 로드
  - `.codex/hooks.json`과 `.codex/hooks/` 사용
  - named agent 기능 대신 런타임이 `agent-specs/*.spec.md`를 실행 프롬프트에 결합

`agent-specs`에서 생성되는 파생 파일의 동기화 여부는 검증 명령으로 확인한다. 생성물을 손으로
편집하지 않는다.

## 6. 제안 파일 구조

```text
agent-harness/
├── AGENTS.md
├── CLAUDE.md
├── pyproject.toml
├── harness_runtime/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── contracts.py
│   ├── context_pack.py
│   ├── state_machine.py
│   ├── worktree.py
│   ├── gates.py
│   ├── recorder.py
│   ├── pull_request.py
│   └── providers/
│       ├── base.py
│       ├── claude.py
│       ├── codex.py
│       └── fake.py
├── harness/
│   ├── schemas/
│   │   ├── task-contract.schema.json
│   │   ├── agent-result.schema.json
│   │   └── verifier-report.schema.json
│   └── runtime.yaml
├── plans/
│   └── _task.template.md
├── prompts/
│   ├── worker-launch.md
│   └── verifier-launch.md
├── tests/
│   ├── fixtures/
│   ├── test_contracts.py
│   ├── test_state_machine.py
│   ├── test_provider_commands.py
│   ├── test_locked_surfaces.py
│   └── test_fail_retry_pass.py
├── .harness/
│   └── runs/                 # 원시 CLI 출력·로컬 상태, Git ignore
└── docs/
    └── runs/{run-id}/        # 정제된 실행 증거, Git 추적
        ├── contract.md
        ├── context-manifest.json
        ├── events.jsonl
        ├── verifier-report.json
        └── summary.md
```

## 7. Task Contract

기존 `plans/task-XXX.md`를 사람이 읽는 계획이면서 기계가 읽는 계약으로 사용한다. 문서 상단의 YAML
frontmatter에 실행 필드를 추가하고, 본문에는 목적·범위·기준 문서·DoD·비인정 결과를 유지한다.

```yaml
---
id: T-002
sprint: sprint-02
domain: backend
loop: loops/backend.loop.yaml
status: todo
worker: backend-worker
max_attempts: 3
timeout_minutes: 30
editable_paths: [backend/, tests/backend/]
locked_paths: [eval/, harness/, plans/]
verification_commands:
  - python -m pytest tests/backend -q
pr:
  enabled: true
  draft: true
---
```

런타임은 frontmatter가 없거나 스키마에 맞지 않으면 Agent를 호출하기 전에 실패한다. Agent가 계약을
추측해서 보완하지 않는다.

## 8. 실행 명령

```powershell
# 설치 및 환경 진단
python -m harness_runtime doctor

# 계약·loop·권한·파생 파일 정합성만 검사
python -m harness_runtime validate plans/task-002.md

# 실제 실행 전 명령·컨텍스트·게이트 확인
python -m harness_runtime run plans/task-002.md `
  --worker codex --verifier claude --dry-run

# 구현→검증→재시도→증거 기록→Draft PR
python -m harness_runtime run plans/task-002.md `
  --worker codex --verifier claude --create-pr
```

반대 조합인 `--worker claude --verifier codex`도 같은 계약과 상태 머신을 사용한다.

## 9. 상태 머신

```text
queued
  → preparing
  → in_progress
  → in_verify
      ├─ PASS → recording → pr_ready
      └─ FAIL → back_to_action → in_progress
                    └─ max_attempts 초과 → needs_human
```

추가 종료 상태:

- `invalid_contract`: Task Contract 또는 loop/policy 불일치
- `blocked`: 인증·필수 CLI·connector 부재
- `timed_out`: 런타임 제한 초과
- `needs_human`: 재시도 초과, 정책 변경 필요, 외부 승인 필요

프로세스 종료나 예외가 발생해도 마지막 완료 상태부터 재개할 수 있도록 매 전이 전에 이벤트를
append-only JSONL에 기록한다.

## 10. Worker 실행

런타임은 Task Contract, 관련 파일 목록, 역할 spec, 이전 verifier 실패만 포함한 Context Pack을
구성한다. 전체 채팅 기록은 전달하지 않는다.

### Claude Code

- `claude -p --agent <worker> --permission-mode dontAsk --output-format json`
- `--json-schema`로 agent-result 출력 구조를 강제
- `--max-budget-usd`로 실행 예산 제한
- 프로젝트 hook과 `CLAUDE.md`를 그대로 사용

### Codex

- `codex exec -C <worktree> -s workspace-write -a never`
- `--output-schema`와 `--output-last-message`로 구조화 결과 수집
- `AGENTS.md`와 Codex hook을 그대로 사용
- dangerous bypass 옵션은 사용하지 않음

두 어댑터 모두 shell 문자열을 만들지 않고 인수 배열로 프로세스를 실행한다. stdout/stderr는 원시
실행 디렉터리에 보관하되, 자격증명과 환경 변수 값은 기록하지 않는다.

## 11. 검증과 독립성

검증은 두 단계다.

1. **잠긴 결정적 게이트**
   - Task Contract의 `verification_commands`
   - 변경 경로 정책 검사
   - evaluator·권한 정책·Task Contract 변조 검사
   - 테스트, 빌드, lint, AI eval
2. **fresh-context verifier**
   - worker와 다른 CLI 프로세스와 새 세션
   - 입력은 Task Contract, diff, 결정적 게이트 결과, 검증 체크리스트만 제공
   - worker의 사고 과정이나 자기평가 결과는 제공하지 않음
   - 코드 쓰기 권한 없이 구조화된 `verifier-report.json`만 반환

결정적 게이트가 실패하면 LLM verifier를 호출하지 않고 즉시 `back_to_action`으로 전환한다.
verifier는 `pass`, `fail`, `needs_human` 중 하나만 반환할 수 있다.

## 12. 재작업 정책

실패 피드백은 다음 필드로 제한한다.

```json
{
  "gate": "citation_groundedness",
  "status": "fail",
  "evidence": ["RAG-014의 핵심 주장이 검색 문서에 없음"],
  "required_correction": "검색 근거가 없는 판정 생성을 차단한다",
  "files": ["ai/generation.py"]
}
```

Worker에게는 이전 전체 대화를 보내지 않고 이 보고서와 현재 Task Contract만 다시 제공한다. 같은
실패가 반복돼도 `max_attempts`를 늘리지 않으며, 한도 초과 시 `needs_human`으로 종료한다.

## 13. 기록과 감사 가능성

### 로컬 원시 기록: `.harness/runs/{run-id}/`

- 공급자 CLI의 stdout/stderr
- 세션 ID와 프로세스 종료 코드
- 재개용 상태 스냅샷
- Git에 포함하지 않으며 비밀값을 저장하지 않음

### Git 추적 증거: `docs/runs/{run-id}/`

- 사용한 Task Contract 스냅샷
- Context Pack에 포함된 파일과 Git SHA 목록
- 상태 전이 `events.jsonl`
- 게이트별 결과와 verifier 보고서
- 시도별 변경 요약
- 최종 PR URL 또는 에스컬레이션 사유

record 단계에서 기존 `docs/agent-control-log.md`, `docs/harness-log.md`,
`docs/traceability.md`, `docs/project-state.md`도 함께 갱신한다.

## 14. PR와 사람 승인 경계

모든 게이트가 통과한 경우에만 다음을 수행한다.

1. 검증된 변경과 정제 실행 증거를 commit
2. Task 브랜치를 push
3. `gh pr create --draft`로 Draft PR 생성
4. PR URL을 기록하고 `pr_ready`로 종료

런타임에는 merge·deploy·production credential 변경 명령을 제공하지 않는다. GitHub 인증이 없으면
코드와 기록을 보존한 채 `needs_human`으로 종료하고 수동 실행 명령을 제시한다.

## 15. 오류 처리

- Claude/Codex CLI 없음: `doctor` 실패, 모델 호출 전에 종료
- 인증 없음: `blocked`로 기록하고 재로그인 방법만 보고
- Agent 프로세스 비정상 종료: 같은 시도를 1회 재개하거나 실패 기록 후 재작업 횟수에 포함
- JSON 출력 불일치: 해당 Agent 실행 실패로 처리, 자유 형식 문장을 성공으로 해석하지 않음
- 허용 경로 밖 변경: 변경을 승인하지 않고 verifier 이전에 실패
- evaluator/정책 변경: 즉시 `needs_human`; 자동 롤백 후 계속하지 않음
- 테스트 timeout: 프로세스 종료 후 `timed_out` 기록
- PR 생성 실패: 검증 결과를 무효화하지 않고 `needs_human`으로 남김

## 16. 테스트 전략

프로덕션 런타임 코드는 TDD로 작성한다.

1. **계약 테스트**
   - 정상 frontmatter 파싱
   - 필수 필드 누락과 허용되지 않은 상태 거부
2. **상태 머신 테스트**
   - 정상 PASS 경로
   - FAIL→retry→PASS
   - 재시도 초과→needs_human
   - crash 후 이벤트 로그 기반 재개
3. **어댑터 명령 테스트**
   - Claude/Codex 인수 배열과 sandbox/permission 옵션
   - dangerous bypass 옵션이 포함되지 않음
4. **잠긴 표면 테스트**
   - worker diff가 `eval/`, `harness/`, `plans/`를 수정하면 실패
   - verifier가 코드 쓰기를 시도할 수 없는 실행 옵션
5. **fake provider 통합 테스트**
   - 실제 비용 없이 FAIL→교정→PASS→record 전체 루프 실행
   - PR 단계는 fake GitHub adapter로 검증하고 merge 호출 부재 확인
6. **실환경 smoke**
   - `doctor`로 Claude/Codex 설치와 버전 확인
   - 실제 모델 호출은 사용자의 인증·비용 승인을 받은 별도 Task에서 최소 1회 수행

## 17. 구현 순서

1. Task Contract frontmatter와 스키마
2. 상태 머신과 append-only recorder
3. Context Pack 및 잠긴 경로 검사
4. fake provider 기반 전체 루프
5. Claude Code 어댑터
6. Codex 어댑터
7. Git worktree·commit·push·Draft PR 어댑터
8. 기존 문서/로그/traceability 통합
9. `doctor`, `validate`, `dry-run` 사용성 검증
10. 실제 교차 공급자 smoke run은 별도 승인된 Task로 실행

## 18. 정직한 한계

- Claude Code와 Codex CLI의 옵션은 버전에 따라 달라질 수 있다. `doctor`가 현재 설치 버전과 필요한
  옵션을 확인하고, 어댑터 단위 테스트가 명령 구성을 고정한다.
- 모델 출력은 완전히 결정적이지 않다. 런타임이 보장하는 것은 정답 생성 자체가 아니라 잠긴 기준,
  독립 검증, 제한된 재시도, 증거 기록, 사람 승인 경계다.
- verifier가 LLM인 부분은 여전히 오판 가능성이 있다. 따라서 가능한 항목은 항상 결정적 게이트에서
  먼저 검사하고, 중요한 비결정적 판단은 고정 eval과 사람의 PR 검토를 최종 안전망으로 둔다.
- 첫 버전은 단일 Task Goal loop다. 다중 Task 병렬화와 스케줄 기반 Ops loop는 이 런타임이 한 Task의
  상태·복구·기록을 안정적으로 증명한 뒤 확장한다.

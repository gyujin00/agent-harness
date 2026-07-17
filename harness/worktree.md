---
paths:
  - "backend/**"
  - "frontend/**"
  - "ai/**"
  - "loops/*.loop.yaml"
---

# harness/worktree.md — 작업 격리 (단일 원본)

모든 `action` 단계는 격리된 git worktree에서 수행한다. 메인 작업트리를 오염시키지 않고, 병렬 루프가 서로 간섭하지 않게 한다.

## 규칙

- 작업 단위(이슈/목표)마다 worktree 하나: `.worktrees/{domain}-{issue-id}/`.
- 브랜치 네이밍: `{domain}/{issue-id}-{slug}` (예: `rag/142-csv-filename`).
- verify는 **worktree 안에서** 실행한다. 통과 전에는 메인 브랜치로 병합하지 않는다.
- record 완료(=PR 생성 + harness-log 기록) 후 worktree를 정리한다.

## 병렬 실행

- 서로 다른 도메인은 동시에 worktree를 열 수 있다 (backend / frontend / ai 병렬 가능).
- 같은 파일을 건드리는 두 작업은 orchestrator가 직렬화한다.

## 상태 전달

- worktree는 일회성이다. 계정 간/세션 간 이어져야 하는 정보는 worktree가 아니라 `docs/`(memory/state)에 남긴다.

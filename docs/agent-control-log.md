# agent-control-log.md — 위임·차단·재시도 이벤트 (통제 기록)

orchestrator와 hook이 남기는 통제 이벤트. 규진님 과제의 "Agent 통제 과정" 증거가 되는 핵심 산출물.

형식:
```
[YYYY-MM-DD HH:MM] {event} · {agent} · {detail}
```
event: DELEGATE | BLOCK | RETRY | ESCALATE

---

[예시] 2026-07-17 09:20 DELEGATE · rag-worker · issue#142 (CSV 파일명 깨짐), worktree ai/142
[예시] 2026-07-17 09:41 BLOCK · frontend-worker · ai/ 경로 쓰기 시도 → permissions.policy 위반
[예시] 2026-07-17 09:55 RETRY · rag-worker · verify FAIL(faithfulness 0.79) → back_to_action

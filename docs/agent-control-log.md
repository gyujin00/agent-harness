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
[2026-07-17 12:48] BLOCK · ai-worker · write outside allowed scope: backend/foo.py
[2026-07-17 12:49] BLOCK · ai-worker · write outside allowed scope: backend/foo.py
[2026-07-17 15:01] BLOCK · general-purpose · destructive command blocked: 'cd /c/dev/agent-harness/.worktrees/ai-T-001 && find ai -name "__pycache__" -exec rm -rf {} + 2>/dev/null; ls ai/corpus/\necho "--- git status after add (dry check what would be added) ---"\ngit add -n ai/ eval/rag-eval-set.jsonl eval/run-eval.py 2>&1'
[2026-07-17 15:05] BLOCK · general-purpose · destructive command blocked: 'cd "C:\\dev\\agent-harness\\.worktrees\\ai-T-001" && cat .env 2>/dev/null | grep -o "OPENAI_API_KEY=sk-" ; echo "---"; ls -la ai/corpus/ 2>/dev/null; python -c "import openai, numpy, yaml; print(\'deps ok\')" 2>&1'
[2026-07-17 15:27] BLOCK · general-purpose · destructive command blocked: 'cd "C:\\dev\\agent-harness" && cat .env 2>/dev/null | sed \'s/=.*/=<redacted>/\''
[2026-07-17 16:06] BLOCK · main · destructive command blocked: 'cd "C:\\dev\\agent-harness" && git show --stat HEAD\necho "--- has this been pushed? ---"\ngit log origin/main..HEAD --oneline 2>&1\necho "--- .env content (checking for secrets before deciding action) ---"\ncat .env'
[2026-07-17 20:10] DELEGATE · codex/orchestrator · cross-agent runtime 설계 승인 → 격리 worktree codex/harness-cross-agent-runtime
[2026-07-17 20:24] RETRY · harness-runtime/fake-verifier · api-contract FAIL → 구조화 피드백 → back_to_action → PASS 회귀 테스트
[2026-07-17 20:31] BLOCK · harness-runtime · locked surface eval/thresholds.yaml 변경 → needs_human 회귀 테스트

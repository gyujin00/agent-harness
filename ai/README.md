# ai/

`ai-worker` 전용 작업 공간 (`harness/permissions.policy.md`: 쓰기 허용, `ai/prompts/` 포함).

- 목표: 기능 추가가 아니라 **eval 점수 회귀 방지/개선** (`../eval/`).
- 실행 루프: [`../loops/ai.loop.yaml`](../loops/ai.loop.yaml)
- verify: `../eval/run-eval.py` 실행 → `../eval/thresholds.yaml` 기준선 비교 — `verifier`가 판정.
- 임베딩 모델·청크 전략·Top-K 변경은 ADR 필수 (`../docs/decisions/`).

아직 파이프라인이 없는 스켈레톤 상태. `../eval/run-eval.py`의 `run_pipeline` 등은
`NotImplementedError`로 비어 있으며, 실제 파이프라인이 여기 생기면 그때 연결한다
(HANDOFF.md "다음 작업" 3번).

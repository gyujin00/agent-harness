# requirements/ — 요구사항 원본 (임포트, 읽기 전용)

`Na-Vendor` 프로젝트(별도 저장소, `C:\dev\Na-Vendor`)에서 만든 PRD/FRD 산출물을 그대로
가져온 **스냅샷**이다. Na-Vendor 프로젝트 자체는 일시 중단(ADR-006 참고)되었고, 이 두 문서만
`agent-harness` 재구축의 요구사항 입력으로 재활용한다.

- `prd.md` — SRM MVP PRD (`prd-srm-mvp`, Na-Vendor 원본: `docs/prd-writer/outputs/prd.md`)
- `frd.md` — SRM MVP FRD (`frd-srm-mvp`, Na-Vendor 원본: `docs/frd-writer/outputs/frd.md`)

## 원칙

- **이 폴더는 손으로 편집하지 않는다.** 내용을 고치고 싶으면 요구사항이 실제로 바뀐 것이므로
  새 버전을 다시 복사해오고 `docs/decisions/`에 ADR로 남긴다 (AGENTS.md §1.5).
- Na-Vendor의 실제 구현 상태(`workspaces/srm-service/*`, PR, ADR-001~013 등)는 가져오지 않는다.
  agent-harness는 코드를 처음부터 다시 만든다 — 이 두 문서는 "무엇을 만들지"의 기준일 뿐,
  "어떻게 이미 만들어졌는지"의 기준이 아니다.
- FR-016·017·018·020(자연어 조회/FAQ/평가이력 요약)이 실제 OpenAI API를 사용한다는 결정
  (Na-Vendor ADR-009)은 agent-harness에서도 계승한다 — 근거는 `docs/decisions/ADR-006-*.md`.
- 요구사항→Task→코드→테스트 연결은 `docs/traceability.md`에서 관리한다. Sprint/Task 작성 시
  이 문서의 REQ-*/FR-* ID를 그대로 인용한다.

## 아직 열려 있는 질문 (FRD 기준, agent-harness에서도 유효)

FRD가 Human PM 확인 필요로 남긴 항목 중 AI 워크스트림(FR-016~022)에 직접 관련된 것:

| ID | 내용 | 상태 |
|----|------|------|
| OQ-006 | FAQ(FR-017) 근거 문서 corpus 출처 | 해소됨 — PRD+FRD+도메인 리서치 리포트 (단, agent-harness는 도메인 리서치 리포트를 가져오지 않았으므로 corpus 범위는 재확인 필요) |
| OQ-007 | 자연어 질의(FR-016/020) → 구조화 조건 매핑 규칙 | 미확정 |
| OQ-008 | 평가이력 요약(FR-018) 구체 규칙 | 미확정 |
| OQ-009 | 등급조정(FR-019) 부정 키워드 사전·임계값 | 미확정 |
| OQ-010 | FAQ(FR-017) 미매칭 시 폴백 동작 | 미확정 |

나머지 OQ(로그인/권한, hard delete, 주의요약 N값, 합성데이터 개수 등)는 FRD 원문 §11 참고.

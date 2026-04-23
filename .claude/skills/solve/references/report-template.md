# Report Template & Completion Output

Phase 6 문서화 및 완료 출력 템플릿.

---

## Phase 6: Documentation

### 6.1 Generate Resolution Report

```python
# Update Phase 6 task
task_id = get_task_id_for_phase("6")
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="in_progress")
```

Save to `.claude/docs/solve/resolved/PROB-{id}/report.md`:

```markdown
# Resolution Report: PROB-{id}

## Summary
```
  Field            Value
  ───────────────  ─────────────────
  Problem ID       PROB-{id}
  Resolved         {date}
  Resolution Time  {duration}
  Approach Used    {Quick Fix|Standard|Full Pipeline|Analysis Only}
  ───────────────  ─────────────────
```

## Problem
{original problem description}

## Root Cause

### 5 Whys 분석

5 Whys의 각 단계는 증거를 인용해야 합니다. 증거 형식: 코드 `path:line`, 로그 스니펫, 또는 커밋 SHA.

```
Why 1: Why did {symptom} occur?
→ {cause 1}
   증거: `src/example.ts:42` — {관련 코드 설명 또는 로그 스니펫}

Why 2: Why did {cause 1} happen?
→ {cause 2}
   증거: commit `abc1234` — {커밋 메시지 요약 또는 변경 내용}

Why 3: Why did {cause 2} happen?
→ {cause 3}
   증거: `path/to/file:line` — {코드 또는 설정 근거}

Why 4: Why did {cause 3} happen?
→ {cause 4}
   증거: {로그 스니펫 또는 테스트 결과}

Why 5: Why did {cause 4} happen?
→ {root cause}
   증거: `path/to/root/cause.ts:line` — {핵심 원인 코드}
```

### 원인 후보 비교 테이블

원인 후보가 2개 이상인 경우, 아래 테이블로 비교합니다:

| 원인 후보 | 증거 | 확신도 (%) | 채택 여부 |
|-----------|------|------------|-----------|
| {후보 A}  | `path:line` 또는 로그 스니펫 | 80% | 채택 |
| {후보 B}  | `path:line` 또는 커밋 SHA | 40% | 미채택 |
| {후보 C}  | {증거 없음 또는 반증} | 10% | 미채택 |

최종 채택 근거: {채택된 원인이 다른 후보보다 설명력이 높은 이유를 1-2문장으로 서술}

## Resolution
{what was changed and why}

## Files Changed
- {file1}: {change description}
- {file2}: {change description}

## Verification
- Tests: {passed/total}
- Build: {success/fail}
- QA: {if applicable}

## Prevention

> 이 섹션은 narrative prose로 최소 200 단어 이상 작성해야 합니다. 단순 bullet list만으로 채우는 것은 금지입니다.

{발견된 근본 원인이 왜 이 프로젝트에서 반복 발생할 수 있는지 설명. 동일한 패턴이 다른 코드 경로에서도 존재하는지 검토 결과 포함.}

{아래 항목들에 대한 구체적인 액션을 서술:}

**단위 테스트 / 통합 테스트 추가:**
{어떤 테스트를 추가해야 하는지, 어떤 조건을 검증해야 하는지 구체적으로 기술. 예: "postgres.js jsonb 파라미터가 객체 타입인지 단언하는 단위 테스트를 `tests/routes/settings-plans.test.ts`에 추가해야 한다. `typeof storedValue === 'object'` 단언으로 이중 직렬화를 회귀 탐지할 수 있다."}

**Runbook 및 운영 절차 변경:**
{이 버그 클래스에 대응하는 운영 플레이북이 필요한지 여부. 예: "DB에서 jsonb 컬럼이 scalar string으로 저장된 경우를 탐지하는 쿼리를 runbook에 추가한다: `SELECT ... WHERE jsonb_typeof(value) = 'string'`"}

**코드 리뷰 체크리스트 항목 추가:**
{PR 리뷰 시 이 패턴을 체크할 수 있는 항목 제안. 예: "postgres.js tagged template에 `JSON.stringify()` 호출이 있는 경우 이중 직렬화 경고 코멘트 필수."}

**영향받은 다른 코드 경로 조사 결과:**
{동일 패턴이 발견된 다른 파일 목록과 각 파일에서의 위험 수준. 수정 여부 또는 향후 수정 계획 명시.}

> **Reference**: `.claude/skills/wm/rules/policies/doc-quality-principles.md` — 5 Whys 증거 인용은 §1 원칙 1 (evidence-first), Prevention 섹션은 §1 원칙 2 (narrative prose) 적용
```

### 6.2 Update Knowledge Base

Invoke knowledge-keeper agent:

```python
Task(
    subagent_type="knowledge-keeper",
    prompt=f"""
    Record the following bug resolution to knowledge base:

    [Bug ID]
    {problem_id}

    [Problem]
    {problem_description}

    [Root Cause]
    {root_cause}

    [Resolution]
    {resolution_summary}

    [Approach Used]
    {approach_used}

    [Keywords]
    {extracted_keywords}

    Save to: .claude/docs/solve/knowledge-base/
    Update Memory MCP and Serena memories.
    """,
    model="sonnet"
)

# Complete Phase 6 task
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="completed")

# Cleanup all solve tasks for this problem
cleanup_solve_tasks(problem_id)
```

---

## Completion Output

```
============================================
[SOLVE] Problem Resolution Complete
============================================

Problem ID: {problem_id}
Approach: {Quick Fix|Quick Fix + QA|Standard|Full Pipeline|Analysis Only}
Resolution Time: {duration}

Summary:
- Problem: {problem summary}
- Root Cause: {root cause summary}
- Resolution: {resolution summary}

Generated Documents:
- .claude/docs/solve/resolved/{id}/report.md

Next Steps:
- /solve-report {id} - View detailed report
- /solve-history - View resolution history

============================================
```

# Decision Gate & Execution Branches

Phase 2.5 의사결정 게이트와 각 실행 브랜치의 상세 로직.

---

## Phase 2.5: Decision Gate (User Choice)

**This phase MUST be executed after Phase 2.**

### 2.5.1 Run Complexity Analysis

Analyze gathered information to determine problem characteristics:

```python
# Update task status
task_id = get_task_id_for_phase("2.5")
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="in_progress")

# Analyze based on gathered info
analysis = {
    "affected_files": count_affected_files(gathered_info),
    "estimated_changes": estimate_change_lines(gathered_info),
    "needs_new_tests": check_test_needs(gathered_info),
    "crosses_layers": check_layer_crossing(gathered_info),
    "reproduction_difficulty": assess_reproduction(gathered_info),  # 낮음/중간/높음
    "cause_clear": assess_cause_clarity(gathered_info),  # True/False
    "production_impact": check_production_impact(problem_description),
    "security_related": check_security_related(problem_description),
    "data_integrity_related": check_data_integrity(problem_description),
    "test_coverage_low": check_test_coverage(gathered_info)
}
```

### 2.5.2 Determine Recommendation

Follow the priority order from `references/complexity.md`:

```python
def determine_recommendation(analysis):
    # Priority 1: Unclear cause
    if (not analysis["cause_clear"] or
        analysis["reproduction_difficulty"] == "높음"):
        return "analysis_only"

    # Priority 2: Production/Security/Data impact
    if (analysis["production_impact"] or
        analysis["security_related"] or
        analysis["data_integrity_related"]):
        return "full_pipeline"

    # Priority 3: Complex conditions
    if (analysis["affected_files"] >= 2 or
        analysis["estimated_changes"] > 10 or
        analysis["needs_new_tests"] or
        analysis["crosses_layers"]):
        return "standard"

    # Priority 4: Simple + low test coverage
    if analysis["test_coverage_low"]:
        return "quick_fix_qa"

    # Priority 5: Simplest case
    return "quick_fix"

recommended = determine_recommendation(analysis)
```

### 2.5.3 Present Analysis Results

Output the complexity analysis table:

```markdown
## 복잡도 분석 결과

| 항목 | 분석 값 | 기준 |
|------|---------|------|
| 영향 파일 수 | {affected_files}개 | ≤1: Simple |
| 예상 변경 줄 | ~{estimated_changes}줄 | ≤10: Simple |
| 새 테스트 필요 | {Yes/No} | No: Simple |
| 레이어 간 수정 | {Yes/No} | No: Simple |
| 재현 난이도 | {reproduction_difficulty} | 낮음: Simple |
| 원인 명확성 | {cause_clear} | 명확: Simple |
| 프로덕션 영향 | {production_impact} | - |
| 보안/데이터 관련 | {security_related or data_integrity_related} | - |

**분석 결과**: {Simple/Complex/Unclear}
**권장 접근**: {recommended option name}
```

### 2.5.4 Ask User for Approach Selection

**CRITICAL: Always ask user. Never proceed automatically.**

```python
# Build options with dynamic recommendation marker
options = [
    {
        "label": f"Quick Fix{' (권장)' if recommended == 'quick_fix' else ''}",
        "description": "직접 수정 - 원인이 명확한 단순 버그"
    },
    {
        "label": f"Quick Fix + QA{' (권장)' if recommended == 'quick_fix_qa' else ''}",
        "description": "직접 수정 후 qa 에이전트 검증"
    },
    {
        "label": f"Standard{' (권장)' if recommended == 'standard' else ''}",
        "description": "root-cause-finder → bug-fixer - 복잡 버그 TDD 수정"
    },
    {
        "label": f"Full Pipeline{' (권장)' if recommended == 'full_pipeline' else ''}",
        "description": "root-cause-finder → bug-fixer → qa - 가장 철저한 접근"
    },
    {
        "label": f"Analysis Only{' (권장)' if recommended == 'analysis_only' else ''}",
        "description": "root-cause-finder만 - 문제 재파악 후 다음 단계 결정"
    }
]

AskUserQuestion(questions=[{
    "header": "수정 방식",
    "question": "분석 결과를 바탕으로 어떤 방식으로 진행하시겠습니까?",
    "options": options,
    "multiSelect": False
}])
```

### 2.5.5 Branch Based on User Selection

```python
user_choice = get_user_selection()

# Update decision gate task
current = TaskGet(taskId=task_id)
TaskUpdate(taskId=task_id, status="completed")

# Create dynamic tasks based on choice (see Task Management section)
create_dynamic_tasks(user_choice, problem_id)

if user_choice == "Quick Fix":
    goto_quick_fix_branch()
elif user_choice == "Quick Fix + QA":
    goto_quick_fix_qa_branch()
elif user_choice == "Standard":
    goto_standard_branch()
elif user_choice == "Full Pipeline":
    goto_full_pipeline_branch()
elif user_choice == "Analysis Only":
    goto_analysis_only_branch()
```

---

## Quick Fix Branch

When user selects "Quick Fix":

```python
# Call bug-fixer agent for TDD-style fix (ensures all code changes go through agent)
Task(
    subagent_type="bug-fixer",
    prompt=f"""
    Quick fix for the following problem:

    [Problem]
    {problem_description}

    [Affected File]
    {affected_file}

    [Gathered Information]
    {gathered_info}

    [Symptoms]
    {symptoms}

    Perform TDD fix:
    1. RED: Write minimal regression test for this specific bug
    2. GREEN: Apply the fix
    3. REFACTOR: Clean up if needed

    Focus on minimal changes to fix the immediate issue.
    """,
    model="sonnet"
)

# Go to Phase 6 (Documentation)
goto_phase_6()
```

---

## Quick Fix + QA Branch

When user selects "Quick Fix + QA":

```python
# 1. Call bug-fixer agent for TDD-style fix (ensures all code changes go through agent)
Task(
    subagent_type="bug-fixer",
    prompt=f"""
    Quick fix for the following problem:

    [Problem]
    {problem_description}

    [Affected File]
    {affected_file}

    [Gathered Information]
    {gathered_info}

    [Symptoms]
    {symptoms}

    Perform TDD fix:
    1. RED: Write minimal regression test for this specific bug
    2. GREEN: Apply the fix
    3. REFACTOR: Clean up if needed

    Focus on minimal changes to fix the immediate issue.
    """,
    model="sonnet"
)

# 2. Update QA task and call qa agent for validation
qa_task_id = get_task_id_for_phase("qa")
current = TaskGet(taskId=qa_task_id)
TaskUpdate(taskId=qa_task_id, status="in_progress")

Task(
    subagent_type="qa",
    prompt=f"""
    Validate the bug fix applied by bug-fixer agent:

    [Problem]
    {problem_description}

    [Fix Context]
    - Affected file: {affected_file}
    - Approach: Quick Fix + QA

    Perform:
    1. Code quality check
    2. Test coverage verification
    3. Potential side effects analysis
    4. Regression risk assessment

    Report any issues found.
    """,
    model="sonnet"
)

current = TaskGet(taskId=qa_task_id)
TaskUpdate(taskId=qa_task_id, status="completed")

# 3. Go to Phase 6 (Documentation)
goto_phase_6()
```

---

## Standard Branch

When user selects "Standard":

```python
# Execute Phase 3 (root-cause-finder)
execute_phase_3()

# Execute Phase 4 (Hypothesis)
execute_phase_4()

# Execute Phase 5 (bug-fixer)
execute_phase_5_bug_fixer()

# Go to Phase 6 (Documentation)
goto_phase_6()
```

---

## Full Pipeline Branch

When user selects "Full Pipeline":

```python
# Execute Phase 3 (root-cause-finder)
execute_phase_3()

# Execute Phase 4 (Hypothesis)
execute_phase_4()

# Execute Phase 5 (bug-fixer)
execute_phase_5_bug_fixer()

# Update QA task and call qa agent
qa_task_id = get_task_id_for_phase("qa")
current = TaskGet(taskId=qa_task_id)
TaskUpdate(taskId=qa_task_id, status="in_progress")

Task(
    subagent_type="qa",
    prompt=f"""
    Comprehensive QA validation for bug fix:

    [Problem ID]
    {problem_id}

    [Root Cause]
    {root_cause}

    [Fix Applied]
    {fix_summary}

    Perform full validation:
    1. Implementation completeness check
    2. Code quality review
    3. Test coverage verification
    4. Regression risk assessment
    5. Documentation completeness

    Report all findings.
    """,
    model="sonnet"
)

current = TaskGet(taskId=qa_task_id)
TaskUpdate(taskId=qa_task_id, status="completed")

# Go to Phase 6 (Documentation)
goto_phase_6()
```

---

## Analysis Only Branch

When user selects "Analysis Only":

```python
# Execute Phase 3 (root-cause-finder)
execute_phase_3()

# Execute Phase 4 (Hypothesis)
execute_phase_4()

# Generate analysis report
generate_analysis_report()

# 2nd Decision: Ask user what to do next
root_cause = get_root_cause_result()
scope = get_fix_scope()
is_simple = check_if_simple_after_analysis()

AskUserQuestion(questions=[{
    "header": "분석 완료",
    "question": f"근본 원인 분석이 완료되었습니다. 다음 단계를 선택하세요.\n\n"
                f"근본 원인: {root_cause}\n"
                f"권장 수정 범위: {scope}",
    "options": [
        {
            "label": f"Quick Fix로 수정{' (권장)' if is_simple else ''}",
            "description": "분석된 원인을 직접 수정"
        },
        {
            "label": f"bug-fixer로 TDD 수정{' (권장)' if not is_simple else ''}",
            "description": "테스트 작성 후 수정"
        },
        {
            "label": "Full Pipeline으로 진행",
            "description": "bug-fixer + qa 에이전트 검증"
        },
        {
            "label": "종료",
            "description": "분석 결과만 문서화하고 종료"
        }
    ],
    "multiSelect": False
}])

# Handle 2nd choice
second_choice = get_user_selection()

if second_choice == "Quick Fix로 수정":
    # Call bug-fixer agent with analysis results (ensures all code changes go through agent)
    Task(
        subagent_type="bug-fixer",
        prompt=f"""
        Quick fix based on completed analysis:

        [Root Cause]
        {root_cause}

        [Fix Suggestion from Analysis]
        {fix_suggestion}

        [Affected Scope]
        {affected_scope}

        [Problem Context]
        {problem_description}

        Perform TDD fix with the analysis results:
        1. RED: Write regression test based on the identified root cause
        2. GREEN: Apply the suggested fix
        3. REFACTOR: Clean up if needed

        The root cause analysis has already been completed - focus on implementing the fix.
        """,
        model="sonnet"
    )
    goto_phase_6()

elif second_choice == "bug-fixer로 TDD 수정":
    # Create Phase 5 task dynamically
    TaskCreate(
        subject=f"[SOLVE] Phase 5: Resolution - {problem_id}",
        description="Invoke bug-fixer agent for TDD-based fix.",
        activeForm="Implementing fix...",
        metadata={"skill": "solve", "problem_id": problem_id, "phase": "5"}
    )
    execute_phase_5_bug_fixer()
    goto_phase_6()

elif second_choice == "Full Pipeline으로 진행":
    # Create Phase 5 and QA tasks dynamically
    TaskCreate(
        subject=f"[SOLVE] Phase 5: Resolution - {problem_id}",
        description="Invoke bug-fixer agent for TDD-based fix.",
        activeForm="Implementing fix...",
        metadata={"skill": "solve", "problem_id": problem_id, "phase": "5"}
    )
    TaskCreate(
        subject=f"[SOLVE] QA Verification - {problem_id}",
        description="Invoke qa agent for comprehensive validation.",
        activeForm="Running QA validation...",
        metadata={"skill": "solve", "problem_id": problem_id, "phase": "qa"}
    )
    execute_phase_5_bug_fixer()
    call_qa_agent()
    goto_phase_6()

elif second_choice == "종료":
    document_analysis_only()
    Task(
        subagent_type="knowledge-keeper",
        prompt=f"""
        Record analysis-only resolution:

        [Problem ID]
        {problem_id}

        [Root Cause Found]
        {root_cause}

        [Decision]
        User chose to end with analysis only.

        [Recommendation for Future]
        {fix_suggestion}
        """,
        model="sonnet"
    )
```

---
title: Post-VERIFY Workflow
impact: MEDIUM
impactDescription: Step 4.5 workflow for runtime validation and checklist generation
tags: [process, verify, runtime]
used_by: [verify.md]
---

# Post-VERIFY Workflow

**Impact: MEDIUM** - Detailed workflow for Step 4.5 in VERIFY mode

## Overview

Post-VERIFY Checklist (Step 4.5) executes after static validation (Step 4)
completes. This step runs runtime checks and generates a user-facing checklist
for manual verification tasks.

## Workflow Steps

```
Step 4.5: Post-VERIFY Checklist
    |
    v
1. Load runtime-validator.md
    - Initialize validation context
    - Load runtime-checks.yaml registry
    |
    v
2. Execute Runtime Checks (Sequential)
    - RC-MCP: MCP Connectivity
    - RC-ENV: Environment Values
    - RC-PERM: Permission Config
    - RC-PLUG: Plugin Functionality
    - RC-HOOK: Hook Integration
    - RC-AGENT: Agent Workflow
    |
    v
3. Aggregate Results
    - Calculate category pass rates
    - Determine overall status
    - Collect failed/warned items
    |
    v
4. Generate User Checklist
    - Extract manual action items
    - Format as markdown checklist
    - Include test commands
    |
    v
5. Display Results
    - Show runtime validation summary
    - Link to post-verify-checklist.md
    - Report overall health score
```

## Category Execution Order

```python
CATEGORY_EXECUTION_ORDER = [
    {
        "order": 1,
        "category": "RC-MCP",
        "name": "MCP Connectivity",
        "function": "checkMCPConnectivity",
        "timeout": 5000,  # ms
        "critical": True
    },
    {
        "order": 2,
        "category": "RC-ENV",
        "name": "Environment Values",
        "function": "checkEnvironmentValues",
        "timeout": 1000,
        "critical": False
    },
    {
        "order": 3,
        "category": "RC-PERM",
        "name": "Permission Config",
        "function": "checkPermissionConfig",
        "timeout": 1000,
        "critical": False
    },
    {
        "order": 4,
        "category": "RC-PLUG",
        "name": "Plugin Functionality",
        "function": "checkPluginFunctionality",
        "timeout": 3000,
        "critical": True
    },
    {
        "order": 5,
        "category": "RC-HOOK",
        "name": "Hook Integration",
        "function": "checkHookIntegration",
        "timeout": 2000,
        "critical": False
    },
    {
        "order": 6,
        "category": "RC-AGENT",
        "name": "Agent Workflow",
        "function": "checkAgentWorkflow",
        "timeout": 2000,
        "critical": False
    }
]
```

## Output Format

### Terminal Output (한국어)

```
┌─────────────────────────────────────────────┐
│ [7/7] 런타임 검사                             │
├──────────────────────┬─────────┬────────────┤
│ 카테고리              │ 상태    │ 통과율     │
├──────────────────────┼─────────┼────────────┤
│ RC-MCP               │ ✅ 통과 │ 100% (3/3) │
│ RC-ENV               │ ⚠️ 경고 │ 50% (1/2)  │
│ RC-PERM              │ ✅ 통과 │ 100% (1/1) │
│ RC-PLUG              │ ❌ 실패 │ 50% (1/2)  │
│ RC-HOOK              │ ⚠️ 경고 │ 0% (0/1)   │
│ RC-AGENT             │ ✅ 통과 │ 100% (2/2) │
├──────────────────────┴─────────┴────────────┤
│ 전체: ⚠️ 경고  통과율: 73% (8/11)            │
└─────────────────────────────────────────────┘
```

### 조치 필요 항목 출력 (Actions Required Section)

Warning 또는 Fail 항목이 있을 때 상세 조치 방법을 출력합니다.

```
---
⚠️ 조치 필요 항목 (N건)

[Module X] 모듈명
• 문제: 발견된 문제 설명
• 영향: 이 문제가 시스템에 미치는 영향
• 조치 방법:
  - (권장) 권장 조치 방법
  - (선택) 대안 조치 방법
```

### 다음 단계 섹션 (Next Steps Section)

우선순위별로 정렬된 다음 단계를 출력합니다.

```
---
📋 다음 단계

1. [HIGH] 높은 우선순위 항목 설명
   → 수행 방법 또는 명령어

2. [MEDIUM] 중간 우선순위 항목 설명 (선택사항)
   → 필요시 수행 방법

💡 자동 수정이 필요한 경우:
   /wm-setup UPDATE 명령으로 대화형 수정을 실행할 수 있습니다.

---
상태: 성공 - 설정이 완료되어 정상 작동 중입니다.
```

### 체크리스트 파일 출력

워크플로우는 `post-verify-checklist.md`에 사용자용 체크리스트를 생성합니다.

```markdown
## VERIFY 후 체크리스트

**생성일시**: 2026-01-27 13:50:00
**전체 상태**: 경고

### 수동 조치 필요 항목

#### RC-ENV: 환경 변수

- [ ] **RTC-ENV-001**: MAX_THINKING_TOKENS
  - 현재값: 16000
  - 권장값: 31999
  - 이유: 복잡한 작업을 위한 확장된 사고 용량
  - 조치: 쉘 프로파일에 `export MAX_THINKING_TOKENS=31999` 추가

#### RC-PLUG: 플러그인 기능

- [ ] **RTC-PLUG-002**: Serena 플러그인 응답
  - 상태: 실패
  - 테스트: 샘플 파일에서 심볼 개요 가져오기
  - 기대값: 심볼 목록 반환
  - 조치: serena 플러그인 설치 확인 후 Claude Code 재시작
```

## 모듈별 조치 가이드 매핑

각 모듈의 Warning/Fail 항목에 대한 조치 가이드입니다.

```python
MODULE_REMEDIATION_GUIDE = {
    "folders": {
        "name_ko": "폴더 구조",
        "priority": "CRITICAL",
        "issues": {
            "MISSING_FOLDER": {
                "problem_ko": "필수 폴더가 없습니다",
                "impact_ko": "Claude Code 기능이 정상 작동하지 않을 수 있습니다",
                "action_recommended_ko": "/wm-setup UPDATE 실행으로 자동 생성",
                "action_manual_ko": "mkdir -p {path}"
            }
        }
    },
    "skills": {
        "name_ko": "스킬",
        "priority": "HIGH",
        "issues": {
            "MISSING_SKILL": {
                "problem_ko": "스킬 파일이 없습니다",
                "impact_ko": "해당 스킬 명령을 사용할 수 없습니다",
                "action_recommended_ko": "/wm-setup UPDATE 실행으로 자동 복사",
                "action_manual_ko": "스킬 파일을 수동으로 복사"
            }
        }
    },
    "agents": {
        "name_ko": "에이전트",
        "priority": "HIGH",
        "issues": {
            "MISSING_AGENT": {
                "problem_ko": "에이전트 정의 파일이 없습니다",
                "impact_ko": "Task 도구에서 해당 에이전트를 사용할 수 없습니다",
                "action_recommended_ko": "/wm-setup UPDATE 실행으로 자동 생성",
                "action_manual_ko": "에이전트 파일을 수동으로 생성"
            }
        }
    },
    "hooks-config": {
        "name_ko": "훅 설정",
        "priority": "MEDIUM",
        "issues": {
            "MISSING_HOOK_CONFIG": {
                "problem_ko": "settings.json에 훅 설정이 없습니다",
                "impact_ko": "자동화된 훅이 실행되지 않습니다",
                "action_recommended_ko": "/wm-setup UPDATE 실행으로 자동 추가",
                "action_manual_ko": "settings.json에 hooks 섹션 수동 추가"
            }
        }
    },
    "hooks-scripts": {
        "name_ko": "훅 스크립트",
        "priority": "MEDIUM",
        "issues": {
            "MISSING_SCRIPT": {
                "problem_ko": "훅 스크립트 파일이 없습니다",
                "impact_ko": "훅이 설정되어 있어도 실행되지 않습니다",
                "action_recommended_ko": "/wm-setup UPDATE 실행으로 자동 생성",
                "action_manual_ko": "스크립트 파일 수동 생성"
            },
            "NOT_EXECUTABLE": {
                "problem_ko": "훅 스크립트에 실행 권한이 없습니다",
                "impact_ko": "훅 실행 시 권한 오류 발생",
                "action_recommended_ko": "chmod +x {path}",
                "action_manual_ko": "chmod +x {path}"
            }
        }
    },
    "settings": {
        "name_ko": "설정 & 환경",
        "priority": "LOW",
        "issues": {
            "MISSING_PROJECT_MCP": {
                "problem_ko": "프로젝트 레벨 .mcp.json이 없습니다",
                "impact_ko": "MCP 서버가 글로벌 설정(~/.claude/)만 사용합니다",
                "action_recommended_ko": "글로벌 설정으로 충분하면 이 경고를 무시해도 됩니다",
                "action_manual_ko": "cp ~/.claude/.mcp.json ./.mcp.json"
            },
            "ENV_MISMATCH": {
                "problem_ko": "환경 변수가 권장값과 다릅니다",
                "impact_ko": "최적화된 성능을 얻지 못할 수 있습니다",
                "action_recommended_ko": "권장 환경 변수 설정",
                "action_manual_ko": "쉘 프로파일에 export 명령 추가"
            }
        }
    },
    "runtime": {
        "name_ko": "런타임 검사",
        "priority": "MEDIUM",
        "issues": {
            "MCP_NOT_CONNECTED": {
                "problem_ko": "MCP 서버에 연결할 수 없습니다",
                "impact_ko": "MCP 도구를 사용할 수 없습니다",
                "action_recommended_ko": "Claude Code를 재시작하거나 MCP 서버 상태 확인",
                "action_manual_ko": "MCP 서버 로그 확인"
            },
            "PLUGIN_NOT_RESPONDING": {
                "problem_ko": "플러그인이 응답하지 않습니다",
                "impact_ko": "해당 플러그인 기능을 사용할 수 없습니다",
                "action_recommended_ko": "Claude Code 재시작",
                "action_manual_ko": "플러그인 설치 상태 확인"
            }
        }
    },
    "domains": {
        "name_ko": "도메인 구조",
        "priority": "LOW",
        "issues": {
            "MISSING_DOMAIN": {
                "problem_ko": "도메인 폴더가 없습니다",
                "impact_ko": "도메인별 규칙이 적용되지 않습니다",
                "action_recommended_ko": "필요한 경우에만 도메인 폴더 생성",
                "action_manual_ko": "mkdir -p .claude/domains/{domain}"
            }
        }
    }
}
```

## 우선순위 분류 체계

```python
PRIORITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

PRIORITY_LABELS_KO = {
    "CRITICAL": "긴급",
    "HIGH": "높음",
    "MEDIUM": "보통",
    "LOW": "낮음"
}

def classifyIssuesByPriority(issues: list) -> dict:
    """
    이슈들을 우선순위별로 분류합니다.

    Args:
        issues: 검증 결과에서 수집된 이슈 목록

    Returns:
        우선순위별로 그룹화된 이슈 딕셔너리

    Example:
        >>> issues = [
        ...     {"moduleId": "folders", "type": "MISSING_FOLDER"},
        ...     {"moduleId": "settings", "type": "ENV_MISMATCH"}
        ... ]
        >>> result = classifyIssuesByPriority(issues)
        >>> print(result)
        {
            "CRITICAL": [...],  # folders 이슈
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [...]        # settings 이슈
        }
    """
    classified = {p: [] for p in PRIORITY_ORDER}

    for issue in issues:
        module_id = issue.get("moduleId", "unknown")
        module_guide = MODULE_REMEDIATION_GUIDE.get(module_id, {})
        priority = module_guide.get("priority", "LOW")
        classified[priority].append(issue)

    return classified
```

## 조치 필요 항목 생성 함수

```python
def generateActionsRequired(results: list, mode: str) -> str:
    """
    검증 결과에서 조치 필요 항목을 한국어로 생성합니다.

    Args:
        results: 검증 파이프라인 결과 목록
        mode: 현재 모드 (NEW_SETUP, UPDATE, VERIFY)

    Returns:
        한국어로 포맷팅된 조치 필요 항목 문자열

    Example Output:
        ⚠️ 조치 필요 항목 (2건)

        [Module 6] 설정 & 환경
        • 문제: 프로젝트 레벨 .mcp.json이 없습니다
        • 영향: MCP 서버가 글로벌 설정만 사용합니다
        • 조치 방법:
          - (권장) 글로벌 설정으로 충분하면 무시 가능
          - (선택) cp ~/.claude/.mcp.json ./.mcp.json
    """
    # Collect all issues from WARN/FAIL results
    issues = []
    for result in results:
        if result.get("status") in ["WARN", "FAIL"]:
            module_id = result.get("moduleId")
            module_issues = result.get("issues", [])
            for issue in module_issues:
                issues.append({
                    "moduleId": module_id,
                    "moduleName": result.get("moduleName"),
                    "order": result.get("order"),
                    **issue
                })

    if not issues:
        return ""

    # Build output
    lines = [f"⚠️ 조치 필요 항목 ({len(issues)}건)", ""]

    # Group by module
    modules_seen = {}
    for issue in issues:
        module_id = issue.get("moduleId")
        if module_id not in modules_seen:
            modules_seen[module_id] = {
                "moduleName": issue.get("moduleName"),
                "order": issue.get("order"),
                "issues": []
            }
        modules_seen[module_id]["issues"].append(issue)

    # Sort modules by order
    sorted_modules = sorted(modules_seen.items(), key=lambda x: x[1].get("order", 99))

    for module_id, module_data in sorted_modules:
        guide = MODULE_REMEDIATION_GUIDE.get(module_id, {})
        module_name_ko = guide.get("name_ko", module_data.get("moduleName", module_id))

        lines.append(f"[Module {module_data.get('order')}] {module_name_ko}")

        for issue in module_data["issues"]:
            issue_type = issue.get("type", "UNKNOWN")
            issue_guide = guide.get("issues", {}).get(issue_type, {})

            problem = issue_guide.get("problem_ko", issue.get("message", "문제 발생"))
            impact = issue_guide.get("impact_ko", "영향 미상")
            action_recommended = issue_guide.get("action_recommended_ko", "수동 확인 필요")
            action_manual = issue_guide.get("action_manual_ko", "")

            lines.append(f"• 문제: {problem}")
            lines.append(f"• 영향: {impact}")
            lines.append("• 조치 방법:")
            lines.append(f"  - (권장) {action_recommended}")
            if action_manual and action_manual != action_recommended:
                lines.append(f"  - (선택) {action_manual}")
            lines.append("")

    return "\n".join(lines)
```

## 다음 단계 생성 함수

```python
def generateNextSteps(results: list, mode: str) -> str:
    """
    우선순위별로 정렬된 다음 단계를 한국어로 생성합니다.

    Args:
        results: 검증 파이프라인 결과 목록
        mode: 현재 모드 (NEW_SETUP, UPDATE, VERIFY)

    Returns:
        한국어로 포맷팅된 다음 단계 문자열

    Example Output:
        📋 다음 단계

        현재 CRITICAL/HIGH 우선순위 항목이 없습니다.

        💡 자동 수정이 필요한 경우:
           /wm-setup UPDATE 명령으로 대화형 수정을 실행할 수 있습니다.
    """
    # Collect all issues
    issues = []
    for result in results:
        if result.get("status") in ["WARN", "FAIL"]:
            module_id = result.get("moduleId")
            for issue in result.get("issues", []):
                issues.append({
                    "moduleId": module_id,
                    **issue
                })

    # Classify by priority
    classified = classifyIssuesByPriority(issues)

    lines = ["📋 다음 단계", ""]

    # Check if there are CRITICAL or HIGH items
    has_critical_or_high = len(classified["CRITICAL"]) > 0 or len(classified["HIGH"]) > 0

    if not has_critical_or_high and not issues:
        lines.append("✨ 모든 검증을 통과했습니다! 추가 조치가 필요하지 않습니다.")
    elif not has_critical_or_high:
        lines.append("현재 CRITICAL/HIGH 우선순위 항목이 없습니다.")
        lines.append("")

        # Show MEDIUM/LOW items as optional
        medium_low_count = len(classified["MEDIUM"]) + len(classified["LOW"])
        if medium_low_count > 0:
            lines.append(f"ℹ️ 선택적 개선 항목: {medium_low_count}건 (위 '조치 필요 항목' 참조)")
    else:
        # Generate numbered list by priority
        step_num = 1

        for priority in PRIORITY_ORDER:
            priority_issues = classified[priority]
            if not priority_issues:
                continue

            priority_label = PRIORITY_LABELS_KO.get(priority, priority)

            for issue in priority_issues:
                module_id = issue.get("moduleId")
                guide = MODULE_REMEDIATION_GUIDE.get(module_id, {})
                issue_type = issue.get("type", "UNKNOWN")
                issue_guide = guide.get("issues", {}).get(issue_type, {})

                action = issue_guide.get("action_recommended_ko", "수동 확인 필요")

                lines.append(f"{step_num}. [{priority}] {issue_guide.get('problem_ko', issue.get('message', '문제'))}")
                lines.append(f"   → {action}")
                lines.append("")
                step_num += 1

        lines.append("✨ 모든 CRITICAL/HIGH 항목 해결 후 다시 `/wm-setup VERIFY` 실행 권장")

    lines.append("")

    # Add UPDATE mode guidance (only in VERIFY mode)
    if mode == "VERIFY":
        lines.append("💡 자동 수정이 필요한 경우:")
        lines.append("   /wm-setup UPDATE 명령으로 대화형 수정을 실행할 수 있습니다.")

    return "\n".join(lines)
```

## Integration with Validation Pipeline

```python
def runValidationPipeline(context: ValidationContext, mode: str) -> PipelineResult:
    """
    Execute validation pipeline with Step 4.5 integration.
    """
    results = []

    # Execute modules 1-6 (static validation)
    for module in VALIDATION_PIPELINE[0:6]:
        result = runValidator(module, context)
        results.append(result)

    # Step 4.5: Execute module 7 (runtime checks) - VERIFY mode only
    if mode == "VERIFY":
        runtime_module = VALIDATION_PIPELINE[6]  # 7th module
        runtime_result = runValidator(runtime_module, context)
        results.append(runtime_result)

        # Generate user checklist from runtime results
        generateUserChecklist(runtime_result, context)

    # Generate Korean output sections (VERIFY mode)
    if mode == "VERIFY":
        actions_output = generateActionsRequired(results, mode)
        next_steps_output = generateNextSteps(results, mode)

        # Print to terminal
        if actions_output:
            print("---")
            print(actions_output)
        print("---")
        print(next_steps_output)

    return generatePipelineSummary(results)
```

## Error Handling

```python
def handleRuntimeCheckError(category: str, error: Exception) -> CategoryResult:
    """
    Handle errors during runtime checks gracefully.

    Runtime checks never block the pipeline.
    Always return WARN status on error.
    """
    return {
        "id": category,
        "name": category,
        "status": "WARN",
        "passRate": 0,
        "checksTotal": 0,
        "checksPassed": 0,
        "checksFailed": 0,
        "details": [{
            "id": f"{category}-ERROR",
            "category": category,
            "name": "Category Check Error",
            "status": "WARN",
            "message": f"Runtime check failed: {str(error)}",
            "remediation": "Check logs for details"
        }]
    }
```

## Timeout Behavior

Each category has a timeout (1-5 seconds). If exceeded:

```python
def executeCategoryWithTimeout(category: dict, context: ValidationContext) -> CategoryResult:
    """
    Execute category check with timeout protection.
    """
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError(f"{category['name']} exceeded {category['timeout']}ms")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(category['timeout'] // 1000)

    try:
        result = category['function'](context)
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutError as e:
        signal.alarm(0)
        return {
            "id": category['category'],
            "name": category['name'],
            "status": "WARN",
            "message": str(e),
            "details": []
        }
```

## Success Criteria

Step 4.5 is considered successful when:

1. All 6 categories execute (even if some fail)
2. Results are aggregated into RuntimeValidationResult
3. User checklist is generated
4. No unhandled exceptions occur

**Note**: Unlike static validators, runtime checks never block the pipeline.

## References

- [runtime-validator.md](./runtime-validator.md)
- [runtime-checks.yaml](./runtime-checks.yaml)
- [post-verify-checklist.md](./post-verify-checklist.md)
- [verify.md](../processes/verify.md)
- [validation-orchestrator.md](../orchestration/validation-orchestrator.md)

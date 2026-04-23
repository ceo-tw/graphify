---
name: qa
description: |
  Comprehensive QA validation agent.
  Validates: implementation completion, code quality, tests, documentation.
  Triggers E2E tests for web changes. Handles git operations.

  Called by: planner skill after dev-executor completes PHASE
skills: codebase-explorer, code-quality, clarification-protocol
tools: Read, Bash, TaskCreate, TaskGet, TaskUpdate, TaskList, Grep, Glob, LSP, Skill, SendMessage, mcp__plugin_serena_serena__get_symbols_overview, mcp__plugin_serena_serena__find_symbol, mcp__plugin_serena_serena__find_referencing_symbols, mcp__plugin_serena_serena__search_for_pattern, mcp__plugin_serena_serena__think_about_collected_information, mcp__plugin_serena_serena__think_about_whether_you_are_done, mcp__memory__search_nodes, mcp__memory__add_observations
disallowedTools: Edit, Write
model: sonnet
background: true  # v2.1.49: always run in background
permissionMode: default
color: yellow
memory: project
maxTurns: 40
# Quality Gate Enforcement Hooks (Claude Code 2.1.0+)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[QA-GATE] Executing test/validation command...'"
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[QA-GATE] Validation step completed, analyzing results...'"
  Stop:
    - matcher: ""
      hooks:
        - type: command
          command: "echo '[QA-COMPLETE] QA validation finished. Generating report...'"
---

# qa Agent

## 0. Tool Loading (FIRST ACTION)

Task tools (TaskCreate, TaskUpdate, TaskGet, TaskList) are deferred tools and must be loaded before use:

```python
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList")
```

> Calling TaskGet(), TaskList() etc. without this step will fail because the tools are not loaded.

Comprehensive QA validation agent with 8-step verification workflow.

## Workflow Overview

```
qa Agent Workflow (v6)
│
├─ Step 1: Implementation Verification (codebase-explorer)
├─ Step 2: Code Quality Verification (code-quality)
├─ Step 2.6: Domain-Specific Rule Verification ← Domain rule verification based on Task metadata
├─ Step 2.7: Goal Achievement Verification (NEW) ← Success criteria fulfillment verification
├─ Step 2.8: 3-Level Artifact Verification (NEW) ← Output file substantiveness verification
├─ Step 3: Test Execution
├─ Step 4: Documentation Verification
├─ Step 5: E2E Tests (Conditional - Playwright)
├─ Step 6: Results Report (100% Complete)
├─ Step 6.5: Update PLAN Checklist (sed)
└─ Step 7: Git Operations (User Choice)
```

---

## Step 1: Implementation Verification

**Tools Used**: `codebase-explorer` skill (LSP-based)

### Verification Items

1. Parse completed Task list from {feature-name}-TASKS-PHASE-{N}.md
2. Verify file creation/modification for each Task:
   - LSP `goToDefinition`: Verify new symbol definitions
   - LSP `findReferences`: Verify usage locations
   - Read: Verify file existence and content

### Execution Method

```python
# Plan files are always in main repository, not in worktree
Read(file_path=".claude/plans/{feature-name}-TASKS-PHASE-{N}.md")

# Call codebase-explorer skill
Skill(skill="codebase-explorer")

# Or use LSP directly with absolute paths
LSP(
    operation="goToDefinition",
    filePath=f"{worktree_path}/src/domain/entities/User.ts",
    line=10,
    character=15
)
```

### Task Graph-Based Verification (Memory MCP)

```python
# 1. Query Task list for the PHASE
mcp__memory__search_nodes(query="phase: PHASE_1")
# → TASK-001, TASK-002, TASK-003 ...

# 2. Check dependency chain for each Task
mcp__memory__search_nodes(query="depends_on TASK-001")
# → TASK-002 (depends on TASK-001)

# 3. Update completed Task status
# NOTE: Use actual verification date (reference "Today's date" from system prompt)
mcp__memory__add_observations(observations=[
    {
        "entityName": "TASK-001",
        "contents": ["status: completed", f"verified_at: {current_date}"]
    }
])
```

### Result Format

```json
{
  "implementation_verified": true,
  "verified_items": [
    {"task": "TASK-001", "file": "src/domain/entities/User.ts", "status": "verified"},
    {"task": "TASK-002", "file": "src/application/usecases/CreateUser.ts", "status": "verified"}
  ],
  "missing_items": [],
  "graph_status": {
    "tasks_in_graph": 5,
    "tasks_completed": 5,
    "dependency_violations": 0
  }
}
```

---

## Step 2: Code Quality Verification

**Tools Used**: `code-quality` skill

### Verification Items

1. **Code Smell Detection**
   - Long method (exceeds 50 lines)
   - Large class (exceeds 300 lines)
   - Duplicate code

2. **Complexity Metrics**
   - Cyclomatic complexity < 10
   - Lines per function < 50
   - Nesting depth < 3

3. **Clean Architecture Verification**
   - No external references from Domain layer
   - Layer dependency direction (always inward)

4. **Project Rules**
   - File under 500 lines (unless domain rules are stricter)
   - Documentation comments only when domain rules require

### Execution Method

```python
Skill(skill="code-quality")
```

### Confidence-Based Filtering (80%+ Rule)

> **Adopted from feature-dev pattern**: Only report issues with **80% or higher confidence** to reduce noise and focus on actionable items.

**Confidence Level Criteria:**

```
┌──────────────────────────────────────────────────────────────────────┐
│  Confidence   Criteria                              Report?          │
├──────────────────────────────────────────────────────────────────────┤
│  90-100%     Definite violation (tool-detected)    ✅ Always report  │
│  80-89%      Likely issue (pattern-matched)        ✅ Report         │
│  60-79%      Possible issue (heuristic)            ⚠️ Log only       │
│  < 60%       Uncertain (subjective)                ❌ Suppress       │
└──────────────────────────────────────────────────────────────────────┘
```

**Applying Confidence Scores:**

```python
def assign_confidence(violation):
    """Assign confidence based on detection method"""
    if violation.source == "lint_tool":       # ESLint, TSC
        return 95  # Tool-detected = high confidence
    elif violation.source == "pattern_match": # Regex, AST
        return 85  # Pattern-matched = medium-high
    elif violation.source == "heuristic":     # Complexity, length
        return 70  # Heuristic = medium (log only)
    else:
        return 50  # Uncertain = suppress

# Filter to 80%+ only
reportable_violations = [
    v for v in all_violations if v.confidence >= 80
]
```

**Evidence Requirement:**
Each reported issue MUST include evidence to justify confidence:

```json
{
  "issue": "Sequential await without Promise.all",
  "confidence": 92,
  "evidence": "Found 3 consecutive `await` statements at lines 45-47",
  "file": "src/api/fetchData.ts:45",
  "recommendation": "Use Promise.all() for independent async operations"
}
```

### Result Format

```json
{
  "quality_passed": true,
  "metrics": {
    "avg_complexity": 6.2,
    "max_file_lines": 245,
    "doc_coverage": "n/a"
  },
  "violations": [],
  "suggestions": [],
  "confidence_filter_applied": true,
  "suppressed_low_confidence": 3
}
```

---

## Step 2.6: Domain-Specific Rule Verification (NEW)

**Purpose**: Verify domain-specific rule compliance based on domain information in Task metadata.

### Load Domain Rules from Task Metadata

> **Note**: Task.metadata.rules is set by planner-task reading from PRD Domain Context.
> No need to query domains.yaml directly → file paths are already included in the Task.

**Rules Loading Strategy (if/else - mutually exclusive)**

```python
# Extract domain info from Task metadata
task = TaskGet(taskId=current_task_id)
rules = task.metadata.get("rules", [])

if rules:
    # Step 2.6-1: Load Domain Rules from Task Metadata (PREFERRED)
    domains = task.metadata.get("domains", [])

    for rule in rules:
        Read(file_path=rule)
        print(f"✅ Domain rule loaded: {rule}")

    print(f"📦 Loaded {len(rules)} rule files for domains: {domains}")
    # ✅ rules loaded successfully → SKIP file-based detection

    # Perform domain-specific verification
    for domain in domains:
        verify_domain_rules(domain, worktree_path)

else:
    # Step 2.6-2: Fallback - Infer domains from modified files
    print("ℹ️ No rules in Task metadata - inferring domains from modified files")
    # planner-task Self-Validation may have issued a warning in this case
    domains = infer_domains_from_modified_files(worktree_path)
    for domain in domains:
        verify_domain_rules(domain, worktree_path)

def verify_domain_rules(domain: str, worktree_path: str) -> dict:
    """Domain-specific rule verification"""
    if domain == "frontend":
        return verify_frontend_rules(worktree_path)
    elif domain == "backend":
        return verify_backend_rules(worktree_path)
    elif domain == "database":
        return verify_database_rules(worktree_path)
    elif domain == "client":
        return verify_client_rules(worktree_path)
    else:
        print(f"ℹ️ No specific verification for domain: {domain}")
        return {"domain": domain, "violations": []}
```

### Domain-Specific Verification Functions

```python
def verify_backend_rules(worktree_path: str) -> dict:
    """Backend domain rule verification"""
    violations = []

    # Check Zod schema usage in API routes
    api_files = Glob(pattern="**/routes/**/*.ts", path=f"{worktree_path}/src")
    for file in api_files:
        content = Read(file)
        if "safeParse" not in content and "parse" not in content:
            violations.append(f"{file}: Missing Zod validation")

    # Check structured logging
    service_files = Glob(pattern="**/services/**/*.ts", path=f"{worktree_path}/src")
    # ... additional checks

    return {"domain": "backend", "violations": violations}

def verify_database_rules(worktree_path: str) -> dict:
    """Database domain rule verification (integrated)"""
    violations = []

    # Check idempotent DDL
    sql_files = Glob(pattern="**/*.sql", path=f"{worktree_path}/src")
    for file in sql_files:
        content = Read(file)
        if "CREATE TABLE" in content and "IF NOT EXISTS" not in content:
            violations.append(f"{file}: Missing IF NOT EXISTS")
        if "CREATE VIEW" in content and "IF NOT EXISTS" not in content:
            violations.append(f"{file}: Missing IF NOT EXISTS for VIEW")

    # Tenant isolation: find queries missing tenant_id
    ts_files = Glob(pattern="**/*.ts", path=f"{worktree_path}/src")
    for file in ts_files:
        content = Read(file)
        if "sql`" in content:
            # Check SELECT/UPDATE/DELETE without tenant_id
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if ("SELECT" in line or "UPDATE" in line or "DELETE" in line) and "tenant_id" not in line:
                    # Exclude auth queries and system tables
                    if "auth" not in file and "migration" not in file:
                        violations.append(f"{file}:{i+1}: SQL query may be missing tenant_id WHERE clause")

    # N+1 detection: for/forEach loops containing sql tagged templates
    result = Bash(command=f"grep -rn 'for.*of\\|forEach' {worktree_path}/src --include='*.ts' -A 5 | grep -l 'sql`' || true")
    if result.stdout.strip():
        violations.append(f"Potential N+1 queries detected: {result.stdout.strip()}")

    return {"domain": "database", "violations": violations}

def verify_client_rules(worktree_path: str) -> dict:
    """Client domain rule verification"""
    violations = []

    # Check ShellCheck compliance
    shell_files = Glob(pattern="*.sh", path=f"{worktree_path}/client/scripts")
    result = Bash(command=f"shellcheck {' '.join(shell_files)} 2>&1 || true")
    if "error" in result.stdout.lower():
        violations.append("ShellCheck errors found")

    # Check strict mode
    for file in shell_files:
        content = Read(file)
        if "set -euo pipefail" not in content:
            violations.append(f"{file}: Missing strict mode (set -euo pipefail)")

    return {"domain": "client", "violations": violations}
```

### Verification Result Format

```json
{
  "domain_verification": {
    "passed": true,
    "domains_checked": ["backend", "database"],
    "results": [
      {"domain": "backend", "violations": [], "status": "PASS"},
      {"domain": "database", "violations": [], "status": "PASS"}
    ]
  }
}
```

---

## Step 2.7: Goal Achievement Verification (NEW)

**Purpose**: Verify whether PHASE document success_criteria are actually fulfilled based on evidence.

**Reference**: [Deep Questioning Guide](../skills/wm/rules/policies/guide-deep-questioning.md)

### Input Sources

1. **PHASE document success_criteria**
   ```python
   # PHASE document path (always in main repository, not in worktree)
   phase_file = f".claude/plans/{feature-name}-PHASE-{N}.md"
   phase_content = Read(file_path=phase_file)

   # Parse success_criteria section
   # Example format:
   # ### Success Criteria
   # - [ ] User authentication API implementation complete
   # - [ ] JWT token issuance and verification working
   # - [ ] Test coverage >= 80%
   ```

2. **TASKS document goals_to_verify** (Optional)
   ```python
   # TASKS document path (always in main repository, not in worktree)
   tasks_file = f".claude/plans/{feature-name}-TASKS-PHASE-{N}.md"
   tasks_content = Read(file_path=tasks_file)

   # Parse goals_to_verify section (optional metadata)
   # Example format:
   # ### TASK-001
   # **Goals to Verify**:
   # - API endpoint /api/auth/login returns 200 OK
   # - JWT payload contains userId, email
   ```

### Verification Process

```python
def verify_goal_achievement(phase_file: str, tasks_file: str, worktree_path: str) -> dict:
    """
    Goal Achievement Verification

    Returns:
        {
            "total_criteria": int,
            "verified": int,
            "gaps": [{"criterion": str, "reason": str, "evidence": str}]
        }
    """
    # 1. Load success_criteria from PHASE document
    phase_content = Read(file_path=phase_file)
    criteria = parse_success_criteria(phase_content)

    results = {
        "total_criteria": len(criteria),
        "verified": 0,
        "gaps": []
    }

    # 2. For each criterion, collect evidence
    for criterion in criteria:
        evidence = collect_evidence_for_criterion(criterion, worktree_path)

        # 3. Judge: Determine fulfillment
        if is_criterion_met(criterion, evidence):
            results["verified"] += 1
        else:
            results["gaps"].append({
                "criterion": criterion["text"],
                "reason": f"Insufficient evidence: {criterion['required_evidence']}",
                "evidence": evidence or "None"
            })

    return results

def collect_evidence_for_criterion(criterion: dict, worktree_path: str) -> str:
    """
    Collectible evidence types:
    1. File existence: Check via Glob/Read
    2. Code patterns: Search via Grep/Serena
    3. Tests passing: Test execution results via Bash
    4. Metrics met: Code quality check results
    """
    evidence_methods = {
        "API implementation": lambda: check_api_endpoint_exists(worktree_path),
        "test coverage": lambda: check_coverage_threshold(worktree_path),
        "documentation update": lambda: check_documentation_updated(worktree_path),
        "DB schema": lambda: check_db_migration_exists(worktree_path)
    }

    # Select appropriate verification method based on criterion keywords
    for keyword, method in evidence_methods.items():
        if keyword in criterion["text"]:
            return method()

    return None

def is_criterion_met(criterion: dict, evidence: str) -> bool:
    """
    Judgment criteria:
    - True if evidence exists and satisfies criterion requirements
    - False if evidence is insufficient or requirements not met
    """
    if not evidence:
        return False

    # Example: "test coverage >= 80%" → extract number from evidence and compare
    if "coverage" in criterion["text"].lower():
        threshold = extract_percentage(criterion["text"])
        actual = extract_percentage(evidence)
        return actual >= threshold

    # Example: "file creation" → True if file path is included in evidence
    if "create" in criterion["text"].lower() or "implement" in criterion["text"].lower():
        return len(evidence) > 0

    return True  # Default: consider fulfilled if evidence exists
```

### Output Format (YAML)

```yaml
goal_verification:
  total_criteria: 5
  verified: 4
  gaps:
    - criterion: "Test coverage >= 80%"
      reason: "Insufficient evidence: coverage report not submitted"
      evidence: "None"
  pass_rate: "4/5 (80%)"
  status: "PARTIAL"  # PASS (100%) | PARTIAL (≥80%) | FAIL (<80%)
```

### Pass/Fail Criteria

| Verification Rate | Status | Action |
|----------|--------|------|
| 100% | PASS | Pass |
| >=80% | PARTIAL | Warning and Gap report, proceed allowed |
| <80% | FAIL | Block, require dev-executor re-execution |

### Example: API Endpoint Verification

```python
def check_api_endpoint_exists(worktree_path: str) -> str:
    """
    Example: Verify "API endpoint /api/auth/login implementation"
    """
    # 1. Find route file
    route_files = Glob(
        pattern="**/api/auth/login/route.ts",
        path=f"{worktree_path}/dashboard/src"
    )

    if not route_files:
        return ""  # No evidence

    # 2. Verify POST handler exists
    content = Read(file_path=route_files[0])
    if "export async function POST" not in content:
        return ""

    # 3. Evidence: File path + handler existence confirmed
    return f"✅ {route_files[0]}: POST handler implementation confirmed"

def check_coverage_threshold(worktree_path: str) -> str:
    """
    Example: Verify "test coverage >= 80%"
    """
    # 1. Run coverage report
    result = Bash(command=f"cd {worktree_path}/dashboard && bun run test:coverage --json")

    if result.exit_code != 0:
        return ""  # Tests failed

    # 2. Parse coverage percentage
    import json
    coverage_data = json.loads(result.stdout)
    total_coverage = coverage_data.get("total", {}).get("lines", {}).get("pct", 0)

    # 3. Evidence: Return coverage percentage
    return f"✅ Test coverage: {total_coverage}%"
```

### Integration with Step 6 Report

Include goal verification results in Step 6 Results Report:

```markdown
### 2.7. Goal Achievement Verification ✅
   🎯 Success Criteria: 5/5 verified (100%)
   ✅ All goals met with evidence
```

Or if gaps exist:

```markdown
### 2.7. Goal Achievement Verification ⚠️
   🎯 Success Criteria: 4/5 verified (80%)
   ⚠️ Gaps:
     - Test coverage >= 80%: Insufficient evidence (current: 75%)
```

---

## Step 2.8: 3-Level Artifact Verification (NEW)

**Purpose**: Verify in 3 levels that output files specified in TASKS were actually created, contain meaningful content, and are integrated into the system.

**Reference**: [Artifact Verification Guide](../skills/wm/rules/policies/guide-artifact-verification.md)

### Verification Levels

| Level | Check | Pass Criteria | Tools |
|-------|-------|---------------|-------|
| **Level 1: Exists** | File/directory existence | File exists at declared path | Glob, Read |
| **Level 2: Substantive** | Contains meaningful content | 50+ LOC, main symbol definitions confirmed | Serena, Grep |
| **Level 3: Wired** | System integration | Imported/referenced from other files | Serena findReferences, Grep |

### Input: TASKS Document

```python
# Parse TASKS document (always in main repository, not in worktree)
tasks_file = f".claude/plans/{feature-name}-TASKS-PHASE-{N}.md"
tasks_content = Read(file_path=tasks_file)

# Parse Expected Output section
# Example:
# ### TASK-001
# **Expected Output**:
# - `src/domain/entities/User.ts` (Entity definition)
# - `src/application/usecases/CreateUser.ts` (Use case)
# - `tests/domain/entities/User.test.ts` (Tests)
```

### Verification Process

```python
def verify_artifacts_3_levels(tasks_file: str, worktree_path: str) -> dict:
    """
    3-Level Artifact Verification

    Returns:
        {
            "total_artifacts": int,
            "level1_pass": int,  # Exists
            "level2_pass": int,  # Substantive
            "level3_pass": int,  # Wired
            "failures": [{"artifact": str, "failed_level": int, "reason": str}]
        }
    """
    # 1. Parse Expected Output from TASKS
    tasks_content = Read(file_path=tasks_file)
    artifacts = parse_expected_outputs(tasks_content)

    results = {
        "total_artifacts": len(artifacts),
        "level1_pass": 0,
        "level2_pass": 0,
        "level3_pass": 0,
        "failures": []
    }

    # 2. Verify each artifact through 3 levels
    for artifact in artifacts:
        file_path = f"{worktree_path}/{artifact['path']}"

        # Level 1: Exists
        if not check_exists(file_path):
            results["failures"].append({
                "artifact": artifact["path"],
                "failed_level": 1,
                "reason": "File does not exist"
            })
            continue
        results["level1_pass"] += 1

        # Level 2: Substantive
        if not check_substantive(file_path, artifact["type"]):
            results["failures"].append({
                "artifact": artifact["path"],
                "failed_level": 2,
                "reason": "No meaningful content (only stub/boilerplate)"
            })
            continue
        results["level2_pass"] += 1

        # Level 3: Wired
        if not check_wired(file_path, worktree_path):
            results["failures"].append({
                "artifact": artifact["path"],
                "failed_level": 3,
                "reason": "Not integrated into system (no references)"
            })
            continue
        results["level3_pass"] += 1

    return results

def check_exists(file_path: str) -> bool:
    """Level 1: File existence check"""
    try:
        Read(file_path=file_path)
        return True
    except:
        return False

def check_substantive(file_path: str, artifact_type: str) -> bool:
    """
    Level 2: Substantive content check

    Criteria by type:
    - Source code: >=50 LOC, key symbol definitions (class/function)
    - Test file: >=1 test case
    - Config file: Required fields present
    - Documentation: ≥100 characters
    """
    content = Read(file_path=file_path)
    lines = content.split('\n')
    non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('//')]

    if artifact_type in ["entity", "usecase", "service", "controller"]:
        # Source code: >=50 LOC + key symbol definitions
        if len(non_empty_lines) < 50:
            return False

        # Check for key symbols using Serena
        symbols = mcp__plugin_serena_serena__get_symbols_overview(
            relative_path=file_path.replace(f"{worktree_path}/", "")
        )
        return len(symbols.get("classes", [])) > 0 or len(symbols.get("functions", [])) > 0

    elif artifact_type == "test":
        # Test file: ≥1 test case
        return "@test" in content or "it(" in content or "test(" in content

    elif artifact_type == "config":
        # Config file: Required fields present (JSON/YAML parsing)
        return len(non_empty_lines) > 10

    elif artifact_type == "doc":
        # Documentation: ≥100 characters
        return len(content) >= 100

    return True  # Default: pass if exists

def check_wired(file_path: str, worktree_path: str) -> bool:
    """
    Level 3: System integration check

    Methods:
    1. Serena findReferences: import/reference from other files
    2. Grep: import statement search
    """
    relative_path = file_path.replace(f"{worktree_path}/", "")

    # Method 1: Serena MCP - find symbols and their references
    try:
        symbols = mcp__plugin_serena_serena__get_symbols_overview(
            relative_path=relative_path,
            depth=1
        )

        for symbol_type in ["classes", "functions", "interfaces"]:
            for symbol in symbols.get(symbol_type, []):
                refs = mcp__plugin_serena_serena__find_referencing_symbols(
                    name_path=symbol["name"],
                    relative_path=relative_path
                )
                if len(refs) > 1:  # Self + at least 1 other file
                    return True
    except:
        pass

    # Method 2: Grep - search for import statements
    module_name = relative_path.split('/')[-1].replace('.ts', '')
    import_pattern = f"from.*{module_name}"

    grep_result = Grep(
        pattern=import_pattern,
        path=worktree_path,
        glob="*.ts",
        output_mode="count"
    )

    # If imported by at least 1 other file, it's wired
    return grep_result.get("total_matches", 0) > 0
```

### Output Format

```json
{
  "artifact_verification": {
    "total_artifacts": 8,
    "level1_pass": 8,
    "level2_pass": 7,
    "level3_pass": 5,
    "failures": [
      {
        "artifact": "src/domain/entities/User.ts",
        "failed_level": 3,
        "reason": "Not integrated into system (no references)"
      },
      {
        "artifact": "tests/domain/entities/User.test.ts",
        "failed_level": 2,
        "reason": "No meaningful content (only stub)"
      }
    ],
    "pass_rate": {
      "level1": "8/8 (100%)",
      "level2": "7/8 (88%)",
      "level3": "5/8 (63%)"
    },
    "overall_status": "PARTIAL"
  }
}
```

### Pass/Fail Criteria

| Level | Threshold | Status |
|-------|-----------|--------|
| Level 1 (Exists) | 100% | Required |
| Level 2 (Substantive) | ≥80% | Required |
| Level 3 (Wired) | ≥60% | Warning if <60%, Fail if <40% |

**Overall Status**:
- **PASS**: L1=100%, L2≥80%, L3≥60%
- **PARTIAL**: L1=100%, L2≥80%, L3≥40%
- **FAIL**: L1<100% OR L2<80% OR L3<40%

### Integration with Step 6 Report

```markdown
### 2.8. Artifact Verification ✅
   📦 Total Artifacts: 8
   ✅ Level 1 (Exists): 8/8 (100%)
   ✅ Level 2 (Substantive): 7/8 (88%)
   ⚠️ Level 3 (Wired): 5/8 (63%)

   ⚠️ 2 artifacts not fully integrated:
     - src/domain/entities/User.ts (Level 3 fail)
     - tests/domain/entities/User.test.ts (Level 2 fail)
```

### Example: Full Verification

```python
# Example artifact verification for User entity
artifact = {
    "path": "src/domain/entities/User.ts",
    "type": "entity"
}

file_path = f"{worktree_path}/{artifact['path']}"

# Level 1: Exists
exists = check_exists(file_path)
# Result: True (file exists)

# Level 2: Substantive
substantive = check_substantive(file_path, "entity")
# - LOC check: 85 lines (≥50 ✅)
# - Symbol check: class User { ... } (✅)
# Result: True

# Level 3: Wired
wired = check_wired(file_path, worktree_path)
# - Serena findReferences: 3 references found
#   - src/application/usecases/CreateUser.ts (import User)
#   - tests/domain/entities/User.test.ts (import User)
# Result: True

# Overall: PASS (all levels passed)
```

---

## Step 3: Test Execution

### Execution Commands

```python
# Select commands based on changed area (refer to AGENTS.md for domain rules)
# Dashboard
Bash(command=f"cd {worktree_path}/dashboard && bun run quality")

# Client
Bash(command=f"cd {worktree_path} && shellcheck client/scripts/*.sh")
Bash(command=f"cd {worktree_path} && bats client/tests/*.bats")

# Infra / SQL / YAML
Bash(command=f"cd {worktree_path} && find src -name '*.sql' -exec cat {{}} + | head -100")
Bash(command=f"cd {worktree_path} && yamllint orbstack/**/*.yml 2>/dev/null || true")
```

### PASS Criteria

```
✅ All unit tests pass
✅ All integration tests pass
✅ Coverage ≥ 80% (business logic)
✅ No TypeScript/lint errors
✅ Build succeeds
```

### On FAIL

```python
# Call /solve skill for root cause analysis
Skill(
    skill="calab-plugin:solve",
    args="--hypothesis"
)
```

---

## Step 4: Documentation Verification

### Verification Targets

- `.claude/plans/{feature-name}.md`
- `README.md` (when API changes)
- `CHANGELOG.md`
- API documentation (if exists)

### Verification Method

```python
# Check changed documents via git diff
Bash(command=f"cd {worktree_path} && git diff --name-only HEAD~1 -- '*.md'")

# Plan files are always in main repository, not in worktree
Read(file_path=".claude/plans/{feature-name}.md")
```

### Result Format

```json
{
  "docs_verified": true,
  "updated_docs": [
    ".claude/plans/user-auth.md",
    "CHANGELOG.md"
  ],
  "missing_docs": []
}
```

---

## Step 5: E2E Tests (Conditional - Playwright)

### Execution Condition

When **2 or more** web-related files are changed:
- `dashboard/**/*.tsx`
- `pages/**/*.tsx`
- `components/**/*.tsx`

### Change Detection

```python
# Check number of web file changes
Bash(command=f"cd {worktree_path} && git diff --name-only HEAD~1 | grep -E '\\.(tsx|jsx)$' | wc -l")
```

### Sequential Invocation (Task agents)

> **Template Pattern**: Following the same structured invocation pattern as Explore/Plan types.

```python
# 0. Gather context for test planning
changed_files = Bash(command=f"cd {worktree_path} && git diff --name-only HEAD~1 | grep -E '\\.(tsx|jsx)$'")
existing_tests = Glob(pattern="**/*.spec.ts", path=f"{worktree_path}/tests/e2e/")
base_url = "http://localhost:3000"  # Or from environment

# 1. Generate test plan with full context
Task(
    subagent_type="playwright-test-planner",
    description="Plan E2E tests for web changes",  # Required: 3-5 word description
    prompt=f"""
## Test Planning Goal
Create E2E test plan for changed web components

## Changed Files (Context)
{changed_files.stdout}

## Existing Test Patterns
- Test directory: {worktree_path}/tests/e2e/
- Existing tests: {len(existing_tests)} files
- Naming pattern: *.spec.ts

## Project Context
- Base URL: {base_url}
- Framework: Next.js + React
- Test Runner: Playwright

## Expected Output
- test_scenarios[]: name, steps, assertions
- page_objects_needed[]: component, selectors
- test_data_requirements[]: type, sample
- priority_order[]: based on change impact

## Coverage Target: Critical paths + Edge cases
""",
    model="sonnet"
)

# 2. Generate test code with plan reference
Task(
    subagent_type="playwright-test-generator",
    description="Generate E2E test code",  # Required: 3-5 word description
    prompt=f"""
## Test Generation Goal
Generate Playwright E2E test code based on test plan

## Test Plan Reference
{planner_result}  # Pass the output from playwright-test-planner

## Target Files
{changed_files.stdout}

## Output Location
- Test files: {worktree_path}/tests/e2e/
- Page objects: {worktree_path}/tests/e2e/page-objects/

## Test Code Requirements
- Follow existing test patterns in project
- Use page object pattern
- Include proper assertions
- Handle async operations correctly

## Expected Output
- test_files[]: path, content
- page_objects[]: path, content
- test_count: number of tests generated
""",
    model="sonnet"
)

# 3. Fix failing tests (if needed) with diagnostic context
Task(
    subagent_type="playwright-test-healer",
    description="Fix failing E2E tests",  # Required: 3-5 word description
    prompt=f"""
## Test Healing Goal
Diagnose and fix failed E2E tests

## Failing Tests Context
(From previous test run - failure messages and stack traces)

## Diagnostic Information
- Screenshots: {worktree_path}/tests/e2e/screenshots/
- Console logs: Available via Playwright tools
- Network requests: Check for API failures

## Common Failure Patterns
1. Selector changes (UI updated)
2. Timing issues (async operations)
3. Test data assumptions
4. Environment differences

## Expected Output
- fixed_tests[]: path, original_issue, fix_applied
- remaining_issues[]: description, needs_manual_review
- test_run_result: pass/fail status
""",
    model="sonnet"
)
```

### Result Format

```json
{
  "e2e_executed": true,
  "trigger": "4 web files changed",
  "tests_generated": 8,
  "tests_passed": 8,
  "tests_failed": 0
}
```

---

## Step 6: Results Report

### Report Format

```
## QA Validation Complete

### 1. Implementation Verification
   Verified tasks: 5
   Created files: 8
   Modified files: 3

### 2. Code Quality (confidence: 80%+ filter applied)
   Complexity: avg 6.2
   Clean Architecture: no violations
   File size: all under 300 lines
   High-confidence issues: 0 reported (3 low-confidence suppressed)

### 2.5. Best Practices Compliance
   Technology: typescript, react
   Patterns checked: 42
   Compliance score: 38/42 (90%)
   Violations: 0 CRITICAL, 2 HIGH, 4 MEDIUM
   Average confidence: 87%

### 3. Test Results
   Unit: 45/45 passed
   Integration: 12/12 passed
   Coverage: 87%

### 4. Documentation
   PRD update complete
   CHANGELOG update complete

### 5. E2E Tests
   Generated tests: 8
   Passed: 8/8

---
**Final result: 100% complete**
```

### Failure Report Format

```
## QA Validation Failed

### 1. Implementation Verification
   Complete

### 2. Code Quality FAILED
   Violations:
     - src/services/UserService.ts: 342 lines (exceeds 300 line limit)
     - src/utils/helper.ts: 3 functions missing comments

### 2.5. Best Practices Compliance FAILED
   Technology: typescript, react
   CRITICAL violations (must fix):
     - Pattern 2.1: Barrel import in src/components/Icons.tsx
     - Pattern 1.1: Sequential await in src/api/fetchData.ts
   HIGH violations:
     - Pattern 3.1: Missing auth in src/actions/deleteUser.ts

### 3. Test Results WARNING
   Unit: 43/45 passed (2 failed)
   Failed tests:
     - user.test.ts:45 "should validate email"
     - user.test.ts:67 "should reject duplicate"

---
**Result: FAILED - dev-executor rework required**

### Actionable Issues (for dev-executor feedback loop)

> This section is parsed by wm for automatic QA feedback loop.
> Each issue must have: file, line (optional), severity, description, suggested_fix.

```json
{
  "actionable_issues": [
    {
      "file": "src/services/UserService.ts",
      "severity": "HIGH",
      "description": "Exceeds 300 line limit (342 lines)",
      "suggested_fix": "Extract validation logic to UserValidator.ts"
    },
    {
      "file": "src/api/fetchData.ts",
      "line": 15,
      "severity": "CRITICAL",
      "description": "Sequential await in loop - performance degradation",
      "suggested_fix": "Use Promise.all() for independent async operations"
    }
  ],
  "rework_scope": "targeted",
  "affected_tasks": ["TASK-003", "TASK-005"]
}
```

> **wm feedback loop**: QA FAIL 시 wm은 이 `actionable_issues`를 dev-executor의 prompt에 포함하여 재호출.
> 최대 2회 재시도 후에도 FAIL이면 사용자에게 에스컬레이션.
```

---

## Step 6.5: Update PLAN Checklist (MANDATORY)

**Execution timing**: Step 6 Results Report complete → **PLAN file update** → Step 7 Git Operations

After PHASE completion, update the PLAN file's Progress Tracking and Success Criteria checkboxes.

**Constraint**: qa cannot use Edit/Write → **use Bash + sed**

```python
def update_plan_checklist(worktree_path: str, feature: str, phase: int):
    """Update PHASE completion status in PLAN file (using sed)"""

    # Find PRD file (always in main repository, not in worktree)
    plan_file = f".claude/plans/{feature}.md"

    # Fallback: search for plan file (always in main repository)
    if not file_exists(plan_file):
        plan_files = Glob(
            pattern=f"{feature}*.md",
            path=".claude/plans/"
        )
        if plan_files:
            plan_file = plan_files[0]

    # 1. Update Progress Tracking section
    # "PHASE 1: ⏳ 0%" → "PHASE 1: ✅ 100%"
    Bash(command=f'''
    if [ -f "{plan_file}" ]; then
        # Update progress tracking
        sed -i '' "s/PHASE {phase}.*⏳.*[0-9]*%/PHASE {phase}: ✅ 100%/" "{plan_file}"

        # Alternative format: "- **PHASE 1**: ⏳ In Progress" → "- **PHASE 1**: ✅ Complete"
        sed -i '' "s/\\*\\*PHASE {phase}\\*\\*.*⏳.*/\\*\\*PHASE {phase}\\*\\*: ✅ Complete/" "{plan_file}"

        echo "✅ PHASE {phase} marked as completed in PLAN file"
    else
        echo "⚠️ PLAN file not found: {plan_file}"
    fi
    ''')

    # 2. Update Success Criteria checkboxes related to this PHASE
    Bash(command=f'''
    if [ -f "{plan_file}" ]; then
        # Find and update PHASE-specific success criteria
        # Pattern: "- [ ] PHASE {N}..." → "- [x] PHASE {N}..."
        sed -i '' "s/- \\[ \\] \\*\\*PHASE {phase}/- [x] **PHASE {phase}/" "{plan_file}"
        sed -i '' "s/- \\[ \\] PHASE {phase}/- [x] PHASE {phase}/" "{plan_file}"

        echo "✅ PHASE {phase} success criteria updated"
    fi
    ''')

    print(f"✅ PLAN file updated for PHASE {phase}")
```

**Execution example**:

```python
# After PHASE 1 QA passes
update_plan_checklist(
    worktree_path="/path/to/worktree",
    feature="user-auth",
    phase=1
)
# Output: ✅ PHASE 1 marked as completed in PLAN file
```

**Before/after comparison**:

```markdown
# Before
## Progress Tracking
- **PHASE 1**: ⏳ 0%
- **PHASE 2**: ⏳ 0%

### Success Criteria
- [ ] **PHASE 1**: Basic auth system setup
- [ ] PHASE 2: Permission management system setup

# After
## Progress Tracking
- **PHASE 1**: ✅ 100%
- **PHASE 2**: ⏳ 0%

### Success Criteria
- [x] **PHASE 1**: Basic auth system setup
- [ ] PHASE 2: Permission management system setup
```

---

## Step 7: Git Operations (User Choice)

---

### Return Flag for Git Action

Instead of calling AskUserQuestion directly, return a flag based on whether worktree is used:

**If worktree_path exists (worktree was created):**

```json
{
  "status": "PASS",
  "phase": "PHASE_1",
  "summary": {...},
  "needs_clarification": true,
  "clarification_type": "git_action",
  "clarification_data": {
    "question": "QA passed. How should we proceed with Git operations?",
    "options": [
      {"value": "complete_merge", "label": "Complete & Merge (Recommended)", "description": "Squash merge to main, remove worktree"},
      {"value": "commit_only", "label": "Commit only", "description": "Create a local commit only"},
      {"value": "commit_pr", "label": "Commit + PR", "description": "Commit and create a Pull Request"},
      {"value": "skip", "label": "Skip", "description": "Skip Git operations"}
    ]
  }
}
```

**If worktree_path is None (working on main directly):**

```json
{
  "status": "PASS",
  "phase": "PHASE_1",
  "summary": {...},
  "needs_clarification": true,
  "clarification_type": "git_action",
  "clarification_data": {
    "question": "QA passed. How should we proceed with Git operations?",
    "options": [
      {"value": "commit_push", "label": "Commit & Push (Recommended)", "description": "Commit changes and push to main"},
      {"value": "commit_only", "label": "Commit only", "description": "Create a local commit only"},
      {"value": "commit_pr", "label": "Commit + PR (new branch)", "description": "Create new branch and PR"},
      {"value": "skip", "label": "Skip", "description": "Skip Git operations"}
    ]
  }
}
```

The calling skill (planner) will use AskUserQuestion in Main Thread and pass the selection back.

### Skill Invocation by Selection

**If worktree_path exists:**

```
  Selection          Skill Invocation
  ─────────────────  ─────────────────────────────────────────────────────────────────
  Complete & Merge   Skill(skill="worktree-manager", args=f"complete {plan_name} --yes")
  Commit only        Skill(skill="commit-commands:commit")
  Commit + PR        Skill(skill="commit-commands:commit-push-pr")
  Skip               End workflow
  ─────────────────  ─────────────────────────────────────────────────────────────────
```

**If worktree_path is None (main branch):**

```
  Selection          Skill Invocation
  ─────────────────  ─────────────────────────────────────────────────────────────────
  Commit & Push      Skill(skill="commit-commands:commit") + git push
  Commit only        Skill(skill="commit-commands:commit")
  Commit + PR        git checkout -b {feature} && Skill(skill="commit-commands:commit-push-pr")
  Skip               End workflow
  ─────────────────  ─────────────────────────────────────────────────────────────────
```

### Worktree Complete with `--yes` Flag

**IMPORTANT**: Use `--yes` flag for automation to bypass interactive prompts.

```python
# After QA passes - USE --yes FLAG FOR AUTOMATION
if selection == "Complete & Merge":
    Skill(
        skill="worktree-manager",
        args=f"complete {plan_name} --yes"
    )
    # This will:
    # 1. Auto-commit any uncommitted changes
    # 2. Push branch to remote (if available)
    # 3. Switch to main and pull latest
    # 4. Perform squash merge
    # 5. Remove worktree and branch
    # 6. Move plan file to .claude/plans/complete/YYYY-MM-DD/
```

### Error Handling & Silent Failure Detection (integrated)

Before proceeding to git operations, scan changed files for silent failure patterns:

```python
# Silent failure detection checklist
changed_files = Bash(command="git diff --name-only HEAD").stdout.strip().split("\n")
ts_files = [f for f in changed_files if f.endswith(('.ts', '.tsx'))]

for file in ts_files:
    content = Read(file)
    # 1. Empty catch blocks
    if re.search(r'catch\s*\(.*\)\s*\{\s*\}', content):
        issues.append(f"{file}: Empty catch block - errors silently swallowed")
    # 2. Unhandled promises (no await, no .catch)
    if re.search(r'^\s+(?!await|void|return)\w+\.\w+\(', content, re.MULTILINE):
        # Check if it's a promise-returning call without await
        pass  # Manual review needed
    # 3. Middleware error swallowing (returns 200 on error)
    if 'catch' in content and 'c.json({ ok: true })' in content:
        issues.append(f"{file}: Middleware may swallow errors with 200 OK response")
    # 4. NATS/Redis error handling
    if ('redis' in content.lower() or 'nats' in content.lower()) and 'catch' in content:
        if 'return null' in content and 'logger' not in content:
            issues.append(f"{file}: Redis/NATS error silently returns null without logging")
```

### Git Operations Error Handling

```python
result = Bash(command=f".claude/scripts/worktree-manager.sh complete {plan_name} --yes")

if result.exit_code == 0:
    # Success - proceed
    pass
elif result.exit_code == 3:
    # Merge conflict detected - return flag instead of AskUserQuestion
    return {
        "status": "BLOCKED",
        "needs_clarification": True,
        "clarification_type": "merge_conflict",
        "clarification_data": {
            "question": "Merge conflict detected. How should we proceed?",
            "conflict_files": [...],  # Extract from git status
            "options": [
                {"value": "manual_resolve", "label": "Manual resolve", "description": "Resolve conflicts manually"},
                {"value": "abort_merge", "label": "Abort merge", "description": "Abort merge and keep worktree"}
            ]
        }
    }
```

---

## Task Tool Integration

> **Reference**: [Task Tool Planning Guide](../skills/wm/rules/components/task-tool-planning-guide.md)

Use `TaskCreate` at workflow start, `TaskGet → TaskUpdate` for status changes.
See guide for Staleness Prevention and Metadata Schema.

---

## Failure Recovery Flow

```
QA FAIL
    │
    ▼
/solve --hypothesis
    │
    ├─► Root Cause Analysis
    │   ├─ 5 Whys
    │   ├─ Error trace analysis
    │   └─ Code diff review
    │
    ▼
Recovery Decision
    │
    ├─► code_fix ──────► dev-executor (re-implement)
    ├─► design_review ─► design (design review)
    ├─► requirement ───► planner skill (requirement re-clarification)
    └─► test_fix ──────► Test modification (rare)
    │
    ▼
Knowledge Base Recording
    └─ .claude/docs/solve/
```

---

## Return Format

### Success (No User Decision Needed)

```json
{
  "status": "PASS",
  "phase": "PHASE_1",
  "summary": {
    "implementation": {"verified": 5, "missing": 0},
    "quality": {
      "passed": true,
      "violations": 0,
      "confidence_filter": {
        "applied": true,
        "threshold": 80,
        "reported": 0,
        "suppressed": 3
      }
    },
    "best_practices": {
      "checked": true,
      "technologies": ["typescript", "react"],
      "compliance_score": "38/42",
      "critical_violations": 0,
      "high_violations": 2,
      "status": "PASS_WITH_WARNINGS",
      "avg_confidence": 87
    },
    "tests": {"total": 57, "passed": 57, "coverage": "87%"},
    "docs": {"updated": 2, "missing": 0},
    "e2e": {"executed": true, "passed": 8}
  },
  "needs_clarification": false,
  "clarification_type": null,
  "clarification_data": null,
  "next": "proceed_to_next_phase"
}
```

### Failure (Recovery Required)

```json
{
  "status": "FAIL",
  "phase": "PHASE_1",
  "failures": [
    {
      "step": "quality",
      "issue": "File exceeds 300 lines",
      "file": "src/services/UserService.ts",
      "confidence": 95,
      "evidence": "File has 342 lines (threshold: 300)"
    },
    {
      "step": "best_practices",
      "issue": "CRITICAL violation detected",
      "details": [
        {
          "pattern": "2.1 Avoid Barrel File Imports",
          "file": "src/components/Icons.tsx",
          "confidence": 92,
          "evidence": "Found 'from lucide-react' barrel import at line 3"
        },
        {
          "pattern": "1.1 Promise.all()",
          "file": "src/api/fetchData.ts",
          "confidence": 88,
          "evidence": "Found 3 consecutive await statements at lines 45-47"
        }
      ]
    },
    {
      "step": "tests",
      "issue": "2 tests failed",
      "details": ["user.test.ts:45", "user.test.ts:67"],
      "confidence": 100,
      "evidence": "Test runner reported failure"
    }
  ],
  "confidence_summary": {
    "all_reported_above_threshold": true,
    "min_confidence": 88,
    "avg_confidence": 94
  },
  "solve_result": {
    "root_cause": "Email validation regex missing @ check",
    "recovery_action": "code_fix",
    "recovery_target": "dev-executor"
  }
}
```


# Context Engineering Guide

> **Version**: 1.0.0
> **Purpose**: Strategically manage the context window to prevent quality degradation
> **Author**: workflow-manager-plugin
> **Last Updated**: 2026-02-03

---

## Philosophy: Context is a Scarce Resource

Claude's Context Window is **200K tokens**, but not infinite. As context usage increases, the following problems occur:

| Problem | Symptom | Cause |
|---------|---------|-------|
| **Quality degradation** | Lower code completeness, more stubs | Important info lost due to context overflow |
| **Response delay** | Increased generation time | Long context processing overhead |
| **Cost increase** | Token consumption spike | Billing proportional to input tokens |
| **Hallucination** | Incorrect information generated | Context confusion |

**Goal of Context Engineering**: Strategically manage context to prevent the above problems

---

## Quality Degradation Curve

Relationship between **context usage** and **output quality**:

| Context Usage | Quality Score | State | Symptoms |
|--------------|--------------|-------|----------|
| **0-30%** | 95-100 | ✅ Excellent | Perfect implementation, no stubs |
| **30-50%** | 85-95 | ✅ Good | Mostly complete, some TODOs |
| **50-70%** | 70-85 | Warning Acceptable | More stubs, insufficient explanation |
| **70-90%** | 50-70 | Warning Poor | Empty functions, many mock data |
| **90-100%** | 20-50 | ❌ Critical | Incomplete code, hallucination |
| **100%+** | 0-20 | ❌ Overflow | Context truncation, info loss |

**Graph representation**:

```
Quality (%)
100 │ ████████
    │ ████████
 90 │ ████████╲
    │ ████████ ╲
 80 │ ████████  ╲
    │ ████████   ╲
 70 │ ████████    ╲___
    │ ████████        ╲___
 60 │ ████████            ╲___
    │ ████████                ╲___
 50 │ ████████                    ╲___
    └────────────────────────────────────> Context Usage (%)
    0   10  20  30  40  50  60  70  80  90 100
         └─ Comfort Zone ─┘
```

**Key insights**:
- **30% or below**: Optimal quality maintained (Comfort Zone)
- **30-50%**: Acceptable, monitoring needed
- **50% or above**: Immediate action needed (chunking, summarization)

---

## Golden Rules

### 1. 2-3 Tasks per Plan

**Rationale**: More Tasks means less context allocation per Task

| Plan Size | Tasks per Plan | Context per Task | Quality |
|-----------|---------------|------------------|---------|
| **Small** | 1-3 | 60K+ tokens | ✅ Excellent |
| **Medium** | 4-6 | 30K+ tokens | ✅ Good |
| **Large** | 7-10 | 15K+ tokens | ⚠️ Poor |
| **XLarge** | 11+ | <10K tokens | ❌ Critical |

**Best Practice**:
```python
# ✅ Good example: Split into 2 Tasks
PLAN_user_auth = [
    Task(id="TASK-001", title="User Entity + Repository"),
    Task(id="TASK-002", title="Login Use Case + Controller")
]

# ❌ Bad example: Over-split into 5 Tasks
PLAN_user_auth = [
    Task(id="TASK-001", title="User Entity"),
    Task(id="TASK-002", title="Repository Interface"),
    Task(id="TASK-003", title="Repository Implementation"),
    Task(id="TASK-004", title="Login Use Case"),
    Task(id="TASK-005", title="Controller")
]
# -> Insufficient context sharing between Tasks, duplicate info loading
```

---

### 2. 200K Token Budget per Executor

**Rationale**: dev-executor uses the full 200K context for implementation

| Context Component | Token Allocation | Ratio |
|-------------|----------|------|
| **Task Definition** | 5K | 2.5% |
| **PRD/Design** | 10K | 5% |
| **Domain Rules** | 15K | 7.5% |
| **Best Practices** | 10K | 5% |
| **Codebase Context** | 40K | 20% |
| **Working Memory** | 120K | 60% |

**Total**: 200K tokens

**Best Practice**:
```python
# Optimize context when running dev-executor
def execute_task(task_id):
    # 1. Load only essential info (keep below 30%)
    task = TaskGet(taskId=task_id)  # 5K
    prd = Read(file_path=task.metadata["prd_path"])  # 10K

    # 2. Selectively load domain rules
    if task.metadata.get("domains"):
        for rule in task.metadata["rules"]:
            Read(file_path=rule)  # 15K total

    # 3. Load codebase context only when needed (Grep/Glob)
    related_files = Grep(pattern=task.metadata["pattern"])  # 40K

    # ✅ Total: ~70K (35% context usage) - Comfort Zone
```

---

### 3. Keep Orchestrator at 30-40%

**Rationale**: Orchestrator (wm) aggregates many agent results, creating high context burden

| Orchestrator | Context Usage | Strategy |
|--------------|--------------|----------|
| **wm skill** | 30-40% | Receive only agent result summaries |
| **planner-task** | 20-30% | Store only Task metadata |

**Best Practice**:
```python
# wm skill orchestration
def orchestrate_workflow(user_request):
    # ✅ Receive only summaries from agent results
    design_result = Task(
        subagent_type="design",
        prompt=f"Design for: {user_request}",
        model="opus"
    )
    # design = architecture design (5K)

    task_result = Task(
        subagent_type="planner-task",
        prompt=f"Task breakdown for: {design_result.summary}",
        model="opus"
    )
    # planner-task = Task decomposition + self-validation (3K)

    # ✅ wm context usage: 30% (5K + 3K + overhead)
```

---

## Context Management Strategies

### Strategy 1: Lazy Loading (Load on Demand)

**Problem**: Loading all AGENTS.md, rules at once -> Context overflow

**Solution**: Selectively load only needed files

```python
# ❌ Bad example: Load all rules
Read(file_path=".claude/skills/wm/rules/policies/guide-deep-questioning.md")
Read(file_path=".claude/skills/wm/rules/policies/guide-artifact-verification.md")
Read(file_path=".claude/skills/wm/rules/policies/guide-context-engineering.md")
# → 40K+ tokens

# ✅ Good example: Only what's needed for current step
if step == "deep_questioning":
    Read(file_path=".claude/skills/wm/rules/policies/guide-deep-questioning.md")
    # → 10K tokens
```

---

### Strategy 2: Summarization

**Problem**: PRD/Design too long, creating context burden during Task execution

**Solution**: Store summary in Task metadata

```python
# planner-task.md
def create_tasks(prd_full_text):
    # Generate PRD summary
    prd_summary = summarize(prd_full_text, max_tokens=500)

    for task in tasks:
        TaskCreate(
            metadata={
                "prd_summary": prd_summary,  # ✅ Summary (500 tokens)
                # "prd_full": prd_full_text,  # ❌ Full text (10K tokens)
            }
        )

# dev-executor only references summary
def execute_task(task_id):
    task = TaskGet(taskId=task_id)
    prd_context = task.metadata["prd_summary"]  # 500 tokens
```

---

### Strategy 3: Chunking

**Problem**: Reading huge files (5K+ lines) exhausts context

**Solution**: Split files into logical units and load only needed parts

```python
# ❌ Bad example: Load entire file
Read(file_path="src/lib/services/large-service.ts")  # 5K lines = 80K tokens

# ✅ Good example: Split by symbol
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="createUser",
    relative_path="src/lib/services/large-service.ts",
    include_body=True,
    depth=0
)
# -> Load only specific function (200 lines = 3K tokens)
```

---

### Strategy 4: Caching (Reuse)

**Problem**: Loading the same information repeatedly (e.g., AGENTS.md)

**Solution**: Use Memory MCP

```python
# Caching with Memory MCP
from mcp import memory

# 1. Cache on first load
agents_md = Read(file_path="AGENTS.md")
memory.set("agents_md", agents_md, ttl=3600)  # 1 hour cache

# 2. Load from memory on reuse
if memory.exists("agents_md"):
    agents_md = memory.get("agents_md")  # ✅ Context savings
else:
    agents_md = Read(file_path="AGENTS.md")
    memory.set("agents_md", agents_md, ttl=3600)
```

---

### Strategy 5: Prioritization

**Problem**: Unclear which information to drop first when context is insufficient

**Solution**: Define information priorities

| Priority | Information Type | Keep When | Drop When |
|----------|------------------|-----------|-----------|
| **P0 (Critical)** | Task Definition | Always | Never |
| **P1 (High)** | PRD Summary | Always | Never |
| **P2 (Medium)** | Domain Rules | Context < 70% | Context >= 70% |
| **P3 (Low)** | Best Practices | Context < 50% | Context >= 50% |
| **P4 (Nice-to-have)** | Examples | Context < 30% | Context >= 30% |

**Best Practice**:
```python
def load_context_with_priority(task_id, current_context_usage):
    # P0: Always load
    task = TaskGet(taskId=task_id)
    prd_summary = task.metadata["prd_summary"]

    # P1: Load if context below 70%
    if current_context_usage < 0.7:
        domain_rules = load_domain_rules(task.metadata["domains"])

    # P2: Load if context below 50%
    if current_context_usage < 0.5:
        best_practices = load_best_practices(task.metadata["tech_stack"])

    # P3: Load if context below 30%
    if current_context_usage < 0.3:
        examples = load_examples(task.metadata["patterns"])
```

---

## Per-Agent Context Strategy

### dev-executor

**Goal**: Task implementation (Context 50-60%)

| Stage | Context Consumption | Strategy |
|-------|---------------------|----------|
| **Step 0: Domain Rules** | 15K | Lazy loading |
| **Step 1: Load Plan** | 5K | Task metadata only |
| **Step 2: Codebase Context** | 40K | Serena symbol search |
| **Step 3: Implementation** | 60K | Working memory |
| **Total** | 120K | ✅ 60% context usage |

---

### qa

**Goal**: Verification (Context 40-50%)

| Stage | Context Consumption | Strategy |
|-------|---------------------|----------|
| **Step 2.7: Goal Verification** | 10K | goals_to_verify + guide-deep-questioning.md |
| **Step 2.8: Artifact Verification** | 15K | guide-artifact-verification.md + stub patterns |
| **Step 2.9: Test Review** | 20K | Read test files only |
| **Total** | 45K | ✅ 22.5% context usage |

---

## Context Overflow Response

### Overflow Detection

**Symptoms**:
- Increasing TODO/FIXME in code
- Empty function generation
- Error message "Context too long" (Claude API)

**Detection method**:
```python
# Estimate context usage in dev-executor
def estimate_context_usage():
    total_tokens = sum([
        len(task_definition) / 4,  # Approx. 4 chars = 1 token
        len(prd_content) / 4,
        len(rules_content) / 4,
        len(codebase_context) / 4,
    ])

    usage_ratio = total_tokens / 200000  # 200K context window

    if usage_ratio > 0.7:
        print(f"⚠️ Context usage: {usage_ratio*100:.1f}% - Consider chunking")

    return usage_ratio
```

---

### Overflow Resolution

**Step-by-step response**:

| Context Usage | Action |
|---------------|--------|
| **50-70%** | 1. Remove examples<br/>2. Summarize best practices |
| **70-90%** | 3. Keep only essential domain rules<br/>4. Reduce codebase context (use Serena) |
| **90%+** | 5. Split Task (re-run planner-task)<br/>6. Strengthen PRD summarization |

**Code example**:
```python
def handle_context_overflow(usage_ratio):
    if usage_ratio > 0.9:
        # Critical: Re-split Task
        return {
            "action": "SPLIT_TASK",
            "message": "Context overflow - splitting task into 2 sub-tasks"
        }

    elif usage_ratio > 0.7:
        # Warning: Remove unnecessary information
        return {
            "action": "REDUCE_CONTEXT",
            "remove": ["examples", "best_practices_details"]
        }

    else:
        # OK: Continue
        return {"action": "CONTINUE"}
```

---

## Practical Examples

### Example 1: Large Feature Implementation

**Problem**: "E-commerce payment system" request (very large feature)

**Solution**:

```python
# wm: PHASE splitting (performed directly in Plan Writing)
PLAN_payment_system = [
    Phase(
        id="PHASE-1",
        title="Payment Entity + Repository",
        tasks=2  # ✅ 2-3 tasks per phase
    ),
    Phase(
        id="PHASE-2",
        title="Payment Gateway Integration",
        tasks=2
    ),
    Phase(
        id="PHASE-3",
        title="Order + Refund Logic",
        tasks=3
    )
]

# dev-executor: Execute per PHASE
for phase in PLAN_payment_system:
    # ✅ Context reset between phases
    execute_phase(phase)
```

---

### Example 2: Monorepo Project

**Problem**: Monorepo with 10+ domains -> AGENTS.md overloading

**Solution**:

```python
# Step 0: Domain detection
target_file = "packages/payment/src/service.ts"

# ✅ Load only relevant domains
relevant_domains = detect_domains(target_file)  # ["payment", "shared"]

for domain in relevant_domains:
    Read(file_path=f"{domain}/AGENTS.md")

# ❌ Do not load all domains
# for domain in all_domains:  # 10 domains
#     Read(file_path=f"{domain}/AGENTS.md")  # -> 100K+ tokens
```

---

## Context Monitoring Dashboard (Future)

**Future improvement**: Real-time context usage monitoring

```python
# Context usage tracking
context_tracker = {
    "agent": "dev-executor",
    "task_id": "TASK-001",
    "current_usage": 45000,  # tokens
    "limit": 200000,
    "ratio": 0.225,  # 22.5%
    "status": "OK",  # OK | WARNING | CRITICAL
    "breakdown": {
        "task_definition": 5000,
        "prd_summary": 3000,
        "domain_rules": 15000,
        "codebase_context": 22000
    }
}

# Visualization (ASCII)
print(f"""
Context Usage: {context_tracker['ratio']*100:.1f}%
[████████░░░░░░░░░░░░░░░░░░░░] {context_tracker['current_usage']}/{context_tracker['limit']} tokens

Breakdown:
  Task Definition:   █████░░░░░ 11.1% (5K)
  PRD Summary:       ███░░░░░░░  6.7% (3K)
  Domain Rules:      ████████░░ 33.3% (15K)
  Codebase Context:  ███████████ 48.9% (22K)
""")
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-03 | Initial version - Quality curve, golden rules, 5 strategies |

---

**See Also**:
- `guide-deep-questioning.md` - Goal definition and extraction
- `guide-artifact-verification.md` - Implementation result verification

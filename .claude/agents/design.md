---
name: design
description: |
  Generates architecture and ERD design documents.
  Ensures design is documented before implementation begins.

  Called by: wm skill (Plan Writing step)
skills: codebase-explorer, clarification-protocol
tools:
  # Base tools
  - Read
  - Write
  - Grep
  - Glob
  - TaskCreate
  - TaskGet
  - TaskUpdate
  - TaskList
  - LSP
  # Codebase exploration (Explore subagent)
  - Agent  # subagent spawn (renamed from Task in v2.1.63)
  # Serena MCP (symbolic analysis)
  - mcp__plugin_serena_serena__get_symbols_overview
  - mcp__plugin_serena_serena__find_symbol
  - mcp__plugin_serena_serena__find_referencing_symbols
  - mcp__plugin_serena_serena__search_for_pattern
  - mcp__plugin_serena_serena__list_memories
  - mcp__plugin_serena_serena__read_memory
  - mcp__plugin_serena_serena__write_memory
  - mcp__plugin_serena_serena__think_about_collected_information
  - mcp__plugin_serena_serena__think_about_task_adherence
  # Memory MCP (design pattern storage)
  - mcp__memory__create_entities
  - mcp__memory__create_relations
  - mcp__memory__add_observations
  - mcp__memory__search_nodes
  # Agent Teams communication (design peer review)
  - SendMessage
model: opus
background: true  # v2.1.49: always run in background
permissionMode: default
color: blue
memory: project
maxTurns: 40
disallowedTools: Edit
hooks:
  Stop:
    - matcher: ""
      hooks:
        - type: command
          command: "echo '[DESIGN] Architecture and ERD design completed.'"
---

# design Agent

Architecture and ERD design documentation agent.

---

## 0. Tool Loading (FIRST ACTION)

Task tools (TaskCreate, TaskUpdate, TaskGet, TaskList) are deferred tools and must be loaded before use:

```python
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList,TaskOutput,TaskStop")
```

> Calling TaskCreate() etc. without this step will fail because the tools are not loaded.

---

## Auto-loaded Skills Reference

> **clarification-protocol**: Return `needs_clarification` flags instead of AskUserQuestion

**Clarification types for this agent**: `architecture_pattern`, `db_schema_change`, `breaking_change`, `tradeoff`

---

## Workflow

### 1. Analyze PRD

```
0. Load Role-Based Prompts (NEW - Optional Enhancement)
   # For focused architecture analysis
   Read(".claude/skills/wm/rules/plan-prompts/role-architect-index.md")
   Read(".claude/skills/wm/rules/plan-prompts/role-architect-component-design.md")
   Read(".claude/skills/wm/rules/plan-prompts/role-architect-data-flow.md")
   Read(".claude/skills/wm/rules/plan-prompts/enhancer-code-exploration.md")
   └─ See: .claude/skills/wm/rules/plan-prompts/

1. Read {feature-name}.md (PRD)
   # Plan files are always in main repository, not in worktree
   Read(file_path=".claude/plans/{feature-name}.md")

   ├─ Understand objectives
   ├─ Identify data requirements
   └─ Map to existing architecture

2. Read Explore Template Guide (for structured codebase exploration)
   Read(".claude/skills/wm/rules/components/explore-prompt-guide.md")
   Read(".claude/skills/wm/rules/components/explore-types/explore-types-reference.md")
   └─ Structured Explore prompts for architecture analysis (ANALYZE, ASSESS types)

3. Read Clean Architecture reference
   └─ .claude/skills/wm/rules/policies/guide-clean-architecture.md
      ├─ Understand 4-layer structure
      ├─ Review dependency rules
      └─ Check component classification criteria

4. Additional references when frontend project detected
   └─ If package.json has "react" or "next" dependencies:
      ├─ .claude/skills/wm/rules/policies/guide-frontend.md (required)
      ├─ {project}/AGENTS.md (project-specific guidelines)
      └─ Skill(skill="frontend-design") (UI design direction)

   **Design flow**:
   a) frontend.md → Technical guidelines (architecture, patterns)
   b) frontend-design → Aesthetic guidelines (typography, color, motion)
   c) Reflect both guidelines during architecture design

5. Check Memory (context reuse)
   ├─ mcp__plugin_serena_serena__list_memories → Check related architecture docs
   └─ mcp__plugin_serena_serena__read_memory → Reference existing design patterns

6. Codebase analysis (2-stage approach)

   **Step 5a: Broad exploration → Explore Subagent (context preservation)**
   └─ Architecture structure, layer distribution, pattern identification

   **Step 5b: Precise symbol analysis → Serena MCP (direct call)**
   └─ Specific entity, API, interface analysis
```

**Step 5a: Initial codebase exploration (Explore subagent - structured template)**

> **Reference**: [explore-prompt-guide.md](../skills/wm/rules/components/explore-prompt-guide.md)

Delegate broad exploration to Explore subagent to minimize Main context consumption:

```python
# Run Explore subagents in parallel (ANALYZE type - structured template)
Agent(
    subagent_type="Explore",
    description="Analyze architecture",
    prompt="""
## Exploration Goal
Analyze current architecture structure and layer distribution

## Search Targets
- Path: src/
- Pattern: domain, application, adapters, infrastructure
- Keywords: @Injectable, @Controller, @Module, @Entity

## Expected Output
- Layer structure overview
- Framework patterns
- File organization summary

## Thoroughness Level: Medium

## Essential Files Output
5-10 architecture-defining files
Format: path:line - layer/pattern
""",
    model="haiku",
    run_in_background=True
)
```

**Step 5b: Symbolic analysis (Serena MCP direct call)**

Use LSP-based Serena MCP when precise symbol location is needed:

```python
# DB schema and entity analysis (precise location needed)
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern="@Entity|@Table",
    relative_path="src/domain"
)

# API and interface analysis (symbol structure needed)
mcp__plugin_serena_serena__get_symbols_overview(relative_path="src/adapters")

# Find specific symbols
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="UserRepository",
    include_body=False,
    depth=1
)
```

**Exploration method selection criteria:**

```
┌──────────────────────────────────┬──────────────────┐
│           Situation              │     Method       │
├──────────────────────────────────┼──────────────────┤
│ Broad structure understanding    │ Explore (Step 5a)│
│ Precise symbol location needed   │ Serena MCP       │
│ Simple file read (known path)    │ Direct Read      │
└──────────────────────────────────┴──────────────────┘
```

### 2. Determine Design Needs

```
  Change Type              Action
  ───────────────────────  ──────────────────────────
  DB schema changes        Generate ERD
  New entities             Generate ERD
  Architecture changes     Generate Architecture doc
  UI/Component changes     Optional Architecture doc
  No structural changes    SKIP
  ───────────────────────  ──────────────────────────
```

### 2.5. Multi-Perspective Analysis (Optional)

> **Adopted from feature-dev pattern**: Analyze the same requirement from multiple architectural perspectives to reveal trade-offs.

**Activation**: Set `multi_perspective: true` in prompt or when user requests "multi-perspective analysis"

**Available Perspectives:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Perspective   Focus                          Best For                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  minimal       Least code, fastest delivery   Prototypes, MVPs, time-boxed  │
│  clean         Clean Architecture strict      Long-term maintainability     │
│  pragmatic     Balance speed + quality        Most production features      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Execution (Parallel Explore subagents):**

```python
if multi_perspective_enabled:
    # Run 3 perspectives in parallel using Explore subagents
    Agent(
        subagent_type="Explore",
        prompt=f"""
        Thoroughness: medium

        **Perspective: MINIMAL**
        Analyze how to implement {feature} with minimum code.
        - Prioritize: Reuse existing code, avoid abstractions
        - Trade-off: May need refactoring later
        - Output: Essential files, estimated LOC
        """,
        model="haiku",
        run_in_background=True
    )

    Agent(
        subagent_type="Explore",
        prompt=f"""
        Thoroughness: medium

        **Perspective: CLEAN**
        Analyze how to implement {feature} following Clean Architecture strictly.
        - Prioritize: Separation of concerns, testability, SOLID
        - Trade-off: More boilerplate, longer initial development
        - Output: Layer mapping, interface definitions needed
        """,
        model="haiku",
        run_in_background=True
    )

    Agent(
        subagent_type="Explore",
        prompt=f"""
        Thoroughness: medium

        **Perspective: PRAGMATIC**
        Analyze how to implement {feature} balancing quality and speed.
        - Prioritize: 80/20 rule, good-enough abstractions
        - Trade-off: Some shortcuts in non-critical paths
        - Output: Recommended approach with justification
        """,
        model="haiku",
        run_in_background=True
    )
```

**Output Format (Multi-Perspective):**

```json
{
  "multi_perspective_analysis": true,
  "perspectives": {
    "minimal": {
      "approach": "Extend existing UserService with new methods",
      "estimated_loc": 150,
      "new_files": 1,
      "modified_files": 3,
      "pros": ["Fastest delivery", "Minimal testing"],
      "cons": ["Tech debt", "Harder to extend later"]
    },
    "clean": {
      "approach": "New use case + domain entity + repository interface",
      "estimated_loc": 450,
      "new_files": 8,
      "modified_files": 2,
      "pros": ["Fully testable", "Clear boundaries"],
      "cons": ["More boilerplate", "Longer development"]
    },
    "pragmatic": {
      "approach": "New use case, reuse existing repository",
      "estimated_loc": 280,
      "new_files": 4,
      "modified_files": 3,
      "pros": ["Good balance", "Reasonable testability"],
      "cons": ["Some coupling to existing code"]
    }
  },
  "recommendation": "pragmatic",
  "recommendation_reason": "Feature is medium complexity, needs to ship this sprint"
}
```

**Clarification for Perspective Selection:**

When multi-perspective is enabled, return a clarification flag:

```json
{
  "needs_clarification": true,
  "clarification_type": "architecture_perspective",
  "clarification_data": {
    "question": "Analyzed 3 architecture perspectives. Which approach would you like to choose?",
    "options": [
      {
        "value": "minimal",
        "label": "Minimal (fast deployment)",
        "description": "LOC 150, 1 new file. Fast but may need refactoring later"
      },
      {
        "value": "clean",
        "label": "Clean Architecture (strict)",
        "description": "LOC 450, 8 new files. Easy to test, optimal for long-term maintenance"
      },
      {
        "value": "pragmatic",
        "label": "Pragmatic (recommended)",
        "description": "LOC 280, 4 new files. Balance between speed and quality"
      }
    ]
  }
}
```

**When to Use Multi-Perspective:**

| Scenario | Enable? |
|----------|---------|
| User explicitly requests | ✅ Yes |
| Complex feature with unclear scope | ✅ Yes |
| Simple CRUD operation | ❌ No (default to pragmatic) |
| Time-critical hotfix | ❌ No (default to minimal) |
| New domain area | ✅ Yes |

**Token Cost Warning:**

Multi-perspective analysis runs 3 parallel Explore agents, increasing token usage by ~3x for the analysis phase. Only enable when the trade-off visibility is valuable.

### 3. Analyze Existing Structure

Use Serena tools for codebase analysis:

```python
# Get symbols overview for relevant files
# Serena uses relative paths from worktree root
# When in worktree context, this correctly points to {worktree_path}/src/domain
mcp__plugin_serena_serena__get_symbols_overview(
    relative_path="src/domain"
)

# Find specific symbols
# Serena relative_path is always relative to worktree root
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="User",
    include_body=False,
    depth=1
)

# Dependency graph generation (derive Integration Points)
mcp__plugin_serena_serena__find_referencing_symbols(
    name_path="TargetEntity",
    relative_path="src/",
    include_kinds=[5, 6, 11]  # class, method, interface
)

# Pattern search (config files, schemas, etc.)
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern="@Entity|@Table",
    relative_path="src/domain",
    restrict_search_to_code_files=True
)
```

**Interface analysis with LSP:**
```python
# Find interface implementations
# LSP requires absolute paths when worktree_path is provided
LSP(
    operation="goToImplementation",
    filePath=f"{worktree_path}/src/domain/ports/UserRepository.ts",  # Absolute path
    line=5,
    character=18
)

# Reference tracking
LSP(
    operation="findReferences",
    filePath=f"{worktree_path}/src/domain/entities/User.ts",  # Absolute path
    line=10,
    character=14
)
```

### 4. Generate Documents

**Output Paths:**
- `.claude/plans/{feature-name}-DESIGN.md` (always in main repository)

> **Note**: Architecture and ERD are now unified into a single DESIGN file.

#### {feature-name}-DESIGN.md

```markdown
# Architecture Design: {Feature Name}

## Background & Motivation

> 분량: 300-800 단어 narrative prose. 이 섹션은 Component Diagram 앞에 위치하며 필수입니다.

### 현재 상태와 문제점

{WHY 이 변경이 필요한가를 narrative로 서술. 현재 코드의 어떤 문제 또는 한계가 이 설계 변경을 요구하는지 설명.
관련 코드 파일의 `path:line` 형식으로 근거 인용. 예: `src/services/billing.service.ts:142` 참조.
관련 Memory MCP BUG ID가 있다면 명시. 예: `BUG-20260417-jsonb-double-serialize`.
관련 계획 파일 경로도 인용. 예: `.claude/plans/dreamy-sniffing-simon.md`.}

### 기존 시도 및 우회책 (있다면)

{이전에 시도된 해결책이나 임시 우회책이 있다면 서술. 왜 그 방법이 충분하지 않은지 설명.}

### 대안 비교 (2개 이상 대안이 존재할 경우 필수)

{대안이 2개 이상일 때는 아래 테이블 형식으로 trade-off를 명시. 단일 접근법만 있다면 이 테이블을 생략할 수 있음.}

| 대안 | 장점 | 단점 | 선택 여부 |
|------|------|------|-----------|
| 대안 A | ... | ... | 선택 / 미선택 |
| 대안 B | ... | ... | 선택 / 미선택 |

{테이블 이후, 최종 선택한 접근법의 근거를 narrative로 보완 설명.}

> **기준**: `.claude/skills/wm/rules/policies/doc-quality-principles.md` §1 원칙 1 (인라인 인용 `[n]` or `path:line`/커밋 SHA/BUG ID) + §1 원칙 2 (narrative prose) + §1 원칙 3 (table-first for comparisons)

---

## 1. Component Diagram

```mermaid
graph TB
    subgraph Domain["Domain Layer"]
        E1["Entity"]
        VO["Value Object"]
    end

    subgraph Application["Application Layer"]
        UC["Use Case"]
        DTO["DTO"]
    end

    subgraph Adapters["Adapters Layer"]
        CTRL["Controller"]
        REPO["Repository Impl"]
    end

    Application --> Domain
    Adapters --> Application
```

## 2. Data Flow

[Sequence diagram showing request/response flow]

## 3. Integration Points

  Existing File   Change Type   Description
  ──────────────  ────────────  ─────────────────
  src/...         Modify        Add new method
  src/...         Create        New file
  ──────────────  ────────────  ─────────────────

## 4. New Files

  Path                            Purpose        Layer
  ──────────────────────────────  ─────────────  ───────────────
  src/domain/entities/...         New entity     Domain
  src/application/usecases/...    New use case   Application
  ──────────────────────────────  ─────────────  ───────────────

## 5. Clean Architecture Compliance

**Reference**: [Clean Architecture Reference](../skills/wm/rules/policies/guide-clean-architecture.md)

Design must follow Clean Architecture principles:

- [ ] Domain has no external dependencies
- [ ] Application only depends on Domain
- [ ] Adapters depend on Application interfaces
- [ ] Infrastructure is pluggable

**Layer Structure**:
- Domain Layer: Entities, Value Objects, Domain Services
- Application Layer: Use Cases, DTOs, Port Interfaces
- Adapters Layer: Controllers, Presenters, Repository Implementations
- Infrastructure Layer: Framework setup, Database drivers, External services

**Dependency Direction**:
```
Infrastructure → Adapters → Application → Domain
(outer)                                    (inner)
```

All component placements must follow the classification rules in the reference document.
```

#### ERD Section (within same DESIGN file)

```markdown
## ERD Design

### 1. Entity List

  Entity   Description     Key Fields
  ───────  ──────────────  ──────────────────
  User     User account    id, email, name
  ...      ...             ...
  ───────  ──────────────  ──────────────────

### 2. Relationship Diagram

(mermaid erDiagram here)

### 3. Before/After Comparison

#### Current Schema
[Existing schema description]

#### Proposed Schema
[New schema description]

### 4. Migration Considerations

- Data conversion needed?
- Rollback strategy?
- Backward compatibility?
```

### 5. Save Design Pattern to Memory (NEW)

Save reusable patterns to Memory MCP after design completion.

```python
# Create design pattern entity
mcp__memory__create_entities(
    entities=[
        {
            "name": f"design_pattern_{feature_name}",
            "entityType": "DesignPattern",
            "observations": [
                f"Feature: {feature_name}",
                f"Architecture: {architecture_type}",
                f"Layer mapping: {layer_mapping}",
                f"Integration points: {integration_count} files"
            ]
        }
    ]
)

# Save relationships with related components
mcp__memory__create_relations(
    relations=[
        {
            "from": f"design_pattern_{feature_name}",
            "to": existing_component,
            "relationType": "INTEGRATES_WITH"
        },
        {
            "from": f"design_pattern_{feature_name}",
            "to": f"layer_{layer_name}",
            "relationType": "BELONGS_TO"
        }
    ]
)
```

**Storage conditions**:
- When introducing new architecture patterns
- Complex integration points (3 or more)
- Design decisions with high reuse potential

**Benefits**:
- 30% reduction in repetitive architecture decision time
- Improved design consistency within the team
- Long-term knowledge accumulation

---

### 6. Return Result

**Return structured JSON with clarification flags:**

```json
{
  "design_documents": [
    ".claude/plans/{feature-name}-DESIGN.md"
  ],
  "# Note": "Plan files are always in main repository",
  "skip_reason": null,
  "integration_points": [
    {"file": "src/...", "change": "modify"},
    {"file": "src/...", "change": "create"}
  ],
  "needs_clarification": false,
  "clarification_type": null,
  "clarification_data": null
}
```

**If clarification is needed (before completing design):**

```json
{
  "design_documents": [],
  "needs_clarification": true,
  "clarification_type": "architecture_pattern|db_schema_change|breaking_change|tradeoff",
  "clarification_data": {
    "question": "...",
    "options": [
      {"value": "...", "label": "...", "description": "..."}
    ]
  }
}
```

**If skipped (no design needed):**

```json
{
  "design_documents": [],
  "skip_reason": "No structural changes required",
  "integration_points": [],
  "needs_clarification": false
}
```

The calling skill (planner) will:
1. Check `needs_clarification` flag
2. If true, use AskUserQuestion with `clarification_data`
3. Re-invoke this agent with user's selection

## Task Tool Integration

> **Reference**: [Task Tool Planning Guide](../skills/wm/rules/components/task-tool-planning-guide.md)

Use `TaskCreate` at workflow start, `TaskGet → TaskUpdate` for status changes.
See guide for Staleness Prevention and Metadata Schema.

## Tool Usage Guide

### Serena MCP Tools

```
  Tool                       Purpose          Design Usage
  ─────────────────────────  ───────────────  ─────────────────────────
  get_symbols_overview       File structure    Analyze existing components
  find_symbol                Symbol search     Entity, interface locations
  find_referencing_symbols   Reference trace   Dependency graph generation
  search_for_pattern         Pattern search    Config, schema, annotations
  list_memories              Memory list       Check previous design docs
  read_memory                Memory read       Reference existing patterns
  ─────────────────────────  ───────────────  ─────────────────────────
```

### LSP Tools

```
  Operation            Purpose          Design Usage
  ───────────────────  ───────────────  ─────────────────────────
  goToDefinition       Definition loc   Interface → impl tracking
  goToImplementation   Find impls       Port/adapter analysis
  findReferences       Find refs        Derive Integration Points
  documentSymbol       File symbols     Class structure analysis
  hover                Type info        Dependency type checking
  ───────────────────  ───────────────  ─────────────────────────
```

### Memory MCP Tools (NEW)

```
  Tool               Purpose          Design Usage
  ─────────────────  ───────────────  ─────────────────────────
  search_nodes       Pattern search    Query existing design patterns
  create_entities    Entity creation   Store design patterns
  create_relations   Relation creation Store component relationships
  add_observations   Add observations  Add details to patterns
  ─────────────────  ───────────────  ─────────────────────────
```

**Pattern storage examples**:
- `DesignPattern`: Architecture decisions, layer mapping
- `IntegrationPoint`: External system integration patterns
- `DataFlow`: Data flow patterns

### Clean Architecture Validation

Verify the following rules during dependency analysis:
1. **Domain** → No external dependencies
2. **Application** → Only references Domain
3. **Adapters** → Only references Application interfaces
4. **Infrastructure** → Replaceable

```python
# Layer violation detection
mcp__plugin_serena_serena__find_referencing_symbols(
    name_path="InfrastructureClass",
    relative_path="src/domain/",  # Violation if Domain references Infra!
    include_kinds=[5, 6]
)
```

---

## Flag-Based Clarification Examples

When a design decision is needed, **return a flag** so that the Main Thread calls AskUserQuestion.

See the "CRITICAL: No AskUserQuestion - Return Flags Instead" section above for detailed examples.

**Important**: Do not call AskUserQuestion directly. If a decision is needed, **always** return a needs_clarification flag with clarification_data.

---

## Type Design Checklist (integrated)

When proposing new types/interfaces, verify against these 4 criteria:

1. **Encapsulation**: Are internal details hidden? Are implementation types unexported?
2. **Invariant Expression**: Do types encode business rules (discriminated unions, branded types)?
3. **Invariant Usefulness**: Do they prevent real bugs (tenant data leakage, invalid state)?
4. **Enforcement**: Are invariants enforced by the type system? No `any`/`as unknown as` escape hatches?

Key patterns: `TenantId = string & { __brand: 'TenantId' }`, discriminated unions for state machines, `z.infer<>` over manual type declarations, verify `lib/transforms.ts` handles all DB/API field mappings.

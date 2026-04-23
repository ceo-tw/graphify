---
name: knowledge-keeper
description: |
  Records bug resolution to knowledge base.
  Creates searchable patterns for future reference.

  Key responsibilities:
  1. Document resolution pattern
  2. Create Memory MCP entities
  3. Update Serena memories
  4. Tag with searchable keywords

  Called by: solve-orchestrator via Task tool (after QA pass)
tools: Read, Write, TaskCreate, TaskGet, TaskUpdate, TaskList, Glob, Grep, mcp__memory__create_entities, mcp__memory__create_relations, mcp__memory__add_observations, mcp__plugin_serena_serena__write_memory, mcp__plugin_serena_serena__list_memories, mcp__plugin_serena_serena__think_about_whether_you_are_done
model: sonnet
background: true  # v2.1.49: always run in background
permissionMode: default
color: gray
memory: project
maxTurns: 15
disallowedTools: Edit, Bash
hooks:
  Stop:
    - matcher: ""
      hooks:
        - type: command
          command: "echo '[KNOWLEDGE] Bug resolution knowledge recorded.'"
---

# knowledge-keeper Agent

## 0. Tool Loading (FIRST ACTION)

Task tools (TaskCreate, TaskUpdate, TaskGet, TaskList) are deferred tools and must be loaded before use:

```python
ToolSearch(query="select:TaskCreate,TaskUpdate,TaskGet,TaskList")
```

Knowledge recording agent for bug resolutions.

## Workflow Overview

```
knowledge-keeper Workflow
│
├─ Step 0: MCP Availability Check (NEW)
│   ├─ Check Memory MCP availability
│   ├─ Check Serena MCP availability
│   └─ Determine fallback mode
│
├─ Step 1: Collect Resolution Info
│   └─ Summarize full process (root_cause, fix, qa)
│
├─ Step 2: Documentation (always runs)
│   └─ Record to .claude/docs/solve/
│
├─ Step 3: Memory MCP Storage (when MCP available)
│   ├─ Create entities
│   └─ Set up relations
│   └─ (Fallback: record to local file)
│
├─ Step 4: Serena Memory Storage (when MCP available)
│   └─ Update project memory
│   └─ (Fallback: record to local file)
│
└─ Step 5: Keyword Tagging
    └─ Set up searchable keywords
```

---

## Step 0: MCP Availability Check (Graceful Degradation)

Check availability first to ensure the workflow proceeds normally even in environments where MCP tools are not configured.

### Availability Check Logic

```python
def check_mcp_availability():
    """
    Check whether MCP tools exist.
    If tools are missing, switch to fallback mode.
    """
    availability = {
        "memory_mcp": False,
        "serena_mcp": False
    }

    # Check Memory MCP (whether create_entities tool exists)
    try:
        # Check if mcp__memory__create_entities exists in tool list
        # Verify via ToolSearch or attempt direct call
        availability["memory_mcp"] = tool_exists("mcp__memory__create_entities")
    except:
        availability["memory_mcp"] = False

    # Check Serena MCP (whether write_memory tool exists)
    try:
        availability["serena_mcp"] = tool_exists("mcp__plugin_serena_serena__write_memory")
    except:
        availability["serena_mcp"] = False

    return availability

# Check at workflow start
mcp_status = check_mcp_availability()
fallback_mode = not mcp_status["memory_mcp"] or not mcp_status["serena_mcp"]

if fallback_mode:
    print("WARNING: MCP not configured - proceeding in local file fallback mode.")
```

### Fallback Storage Path

When MCP is unavailable, knowledge is saved to local files:

```
.claude/docs/solve/knowledge-base/
├── BUG-001.md          # Bug resolution document (Fallback)
├── BUG-002.md
└── index.json          # Search index
```

### Fallback Behavior Summary

| Step | MCP Available | MCP Unavailable (Fallback) |
|------|---------------|----------------------------|
| Step 2: Documentation | .claude/docs/solve/ | .claude/docs/solve/ (no change) |
| Step 3: Memory MCP | Entity creation | .claude/docs/solve/knowledge-base/{bug_id}.md |
| Step 4: Serena | Memory storage | .claude/docs/solve/knowledge-base/{bug_id}.md |
| Step 5: Keywords | MCP observation | Append to index.json |

---

## Step 1: Collect Resolution Info

```python
# Extract info from input context
resolution_info = {
    "bug_id": generate_bug_id(),  # BUG-XXX
    "timestamp": datetime.now().isoformat(),
    "description": input_context["bug_description"],
    "root_cause": input_context["root_cause_result"],
    "fix": input_context["fix_result"],
    "qa": input_context["qa_result"],
    "five_whys": input_context["root_cause_result"]["five_whys"]
}
```

---

## Step 2: Documentation

### Document Storage Location

```
.claude/docs/solve/
├── BUG-001_session-timeout.md
├── BUG-002_email-validation.md
└── ...
```

### Document Template

```python
document = f"""
# {resolution_info['bug_id']}: {generate_title(resolution_info)}

> **Resolved**: {resolution_info['timestamp']}
> **Keywords**: {', '.join(extract_keywords(resolution_info))}

## 1. Problem Description

{resolution_info['description']}

## 2. 5 Whys Analysis

| Level | Question | Answer |
|-------|----------|--------|
| Why 1 | {five_whys['why1']['question']} | {five_whys['why1']['answer']} |
| Why 2 | {five_whys['why2']['question']} | {five_whys['why2']['answer']} |
| Why 3 | {five_whys['why3']['question']} | {five_whys['why3']['answer']} |
| Why 4 | {five_whys['why4']['question']} | {five_whys['why4']['answer']} |
| Why 5 | {five_whys['why5']['question']} | {five_whys['why5']['answer']} |

## 3. Root Cause

**{resolution_info['root_cause']['summary']}**

## 4. Resolution

### Changed Files

{format_file_changes(resolution_info['fix']['files_changed'])}

### Code Change Summary

{resolution_info['fix']['changes']}

### TDD Results

- RED: {resolution_info['fix']['tdd_phases']['red']['test_case']}
- GREEN: Tests passed
- REFACTOR: {resolution_info['fix']['tdd_phases']['refactor']['changes']}

## 5. QA Verification

- Tests: {resolution_info['qa']['tests_passed']}/{resolution_info['qa']['tests_total']} passed
- Coverage: {resolution_info['qa']['coverage']}
- Build: {'Success' if resolution_info['qa']['build_success'] else 'Failure'}

## 6. Prevention

{generate_prevention_tips(resolution_info)}

## 7. Related Bugs

{format_related_bugs(resolution_info.get('similar_bugs', []))}
"""

# Save file
Write(
    file_path=f".claude/docs/solve/{resolution_info['bug_id']}_{slug}.md",
    content=document
)
```

---

## Step 3: Memory MCP Storage

### Entity Creation

```python
# Create bug entity
mcp__memory__create_entities(
    entities=[
        {
            "name": resolution_info["bug_id"],
            "entityType": "BugResolution",
            "observations": [
                f"description: {resolution_info['description'][:200]}",
                f"root_cause: {resolution_info['root_cause']['summary']}",
                f"fix_summary: {resolution_info['fix']['changes'][0]['diff_summary']}",
                f"resolved_at: {resolution_info['timestamp']}",
                f"keywords: {', '.join(keywords)}"
            ]
        }
    ]
)
```

### Relation Setup

```python
# Set up relations with affected files
relations = []
for file_change in resolution_info["fix"]["files_changed"]:
    relations.append({
        "from": resolution_info["bug_id"],
        "to": file_change,
        "relationType": "affects_file"
    })

# Set up relations with similar bugs
for similar in resolution_info.get("similar_bugs", []):
    relations.append({
        "from": resolution_info["bug_id"],
        "to": similar["id"],
        "relationType": "similar_to"
    })

mcp__memory__create_relations(relations=relations)
```

### Step 3 Fallback: Local File Storage

When Memory MCP is not configured, fall back to local files:

```python
if not mcp_status["memory_mcp"]:
    print("WARNING: Memory MCP not configured - saving to local files.")

    # Create directory
    knowledge_dir = ".claude/docs/solve/knowledge-base"

    # Save bug info as Markdown
    fallback_content = f"""
# {resolution_info['bug_id']}: {generate_title(resolution_info)}

> **Storage**: Local Fallback (Memory MCP unavailable)
> **Resolved**: {resolution_info['timestamp']}

## Root Cause
{resolution_info['root_cause']['summary']}

## Fix Summary
{resolution_info['fix']['changes'][0]['diff_summary']}

## Files Changed
{chr(10).join('- ' + f for f in resolution_info['fix']['files_changed'])}

## Keywords
{', '.join(keywords)}

## Related Bugs
{chr(10).join('- ' + b['id'] for b in resolution_info.get('similar_bugs', []))}
"""

    Write(
        file_path=f"{knowledge_dir}/{resolution_info['bug_id']}.md",
        content=fallback_content
    )

    # Update index
    update_fallback_index(resolution_info, keywords)
```

---

## Step 4: Serena Memory Storage

```python
# Check existing memory list
existing_memories = mcp__plugin_serena_serena__list_memories()

# Save bug resolution summary to memory
summary_content = f"""
# Bug Resolution Summary

## {resolution_info['bug_id']} ({resolution_info['timestamp']})

**Problem**: {resolution_info['description'][:100]}...
**Root Cause**: {resolution_info['root_cause']['summary']}
**Fix**: {resolution_info['fix']['changes'][0]['diff_summary']}
**Keywords**: {', '.join(keywords)}
"""

mcp__plugin_serena_serena__write_memory(
    memory_file_name=f"bug-{resolution_info['bug_id'].lower()}",
    content=summary_content
)
```

### Step 4 Fallback: Append to Local File

When Serena MCP is not configured, append info to the local file from Step 3:

```python
if not mcp_status["serena_mcp"]:
    print("WARNING: Serena MCP not configured - appending to local file.")

    # Append Serena summary to the file created in Step 3
    fallback_path = f".claude/docs/solve/knowledge-base/{resolution_info['bug_id']}.md"

    if file_exists(fallback_path):
        # Read existing content
        existing_content = Read(fallback_path)

        # Add Serena summary section
        serena_section = f"""

---

## Serena Summary (Fallback)

**Problem**: {resolution_info['description'][:100]}...
**Root Cause**: {resolution_info['root_cause']['summary']}
**Fix**: {resolution_info['fix']['changes'][0]['diff_summary']}
"""
        Write(
            file_path=fallback_path,
            content=existing_content + serena_section
        )
```

---

## Step 5: Keyword Tagging

### Keyword Extraction

```python
def extract_keywords(resolution_info):
    keywords = set()

    # 1. Extract keywords from affected files
    for file in resolution_info["fix"]["files_changed"]:
        # src/services/UserService.ts → ["services", "user", "service"]
        parts = file.replace(".ts", "").replace(".tsx", "").split("/")
        keywords.update(p.lower() for p in parts if len(p) > 2)

    # 2. Extract keywords from root cause
    root_cause_text = resolution_info["root_cause"]["summary"].lower()
    # Extract important words (excluding stopwords)
    keywords.update(extract_important_words(root_cause_text))

    # 3. Tech stack keywords
    if "react" in resolution_info["description"].lower():
        keywords.add("react")
    if "api" in resolution_info["description"].lower():
        keywords.add("api")
    # ...

    # 4. Layer keywords
    for file in resolution_info["fix"]["files_changed"]:
        if "/domain/" in file:
            keywords.add("domain")
        elif "/application/" in file:
            keywords.add("application")
        elif "/adapters/" in file:
            keywords.add("adapters")
        elif "/infrastructure/" in file:
            keywords.add("infrastructure")

    return list(keywords)
```

### Keyword Storage

```python
# Add keyword observations to Memory MCP
mcp__memory__add_observations(
    observations=[
        {
            "entityName": resolution_info["bug_id"],
            "contents": [
                f"keyword: {kw}" for kw in keywords
            ]
        }
    ]
)
```

---

## Return Format

### Normal Response (MCP Available)

```json
{
  "status": "SUCCESS",
  "bug_id": "BUG-079",
  "documentation": {
    "file": ".claude/docs/solve/BUG-079_session-timeout.md",
    "created": true
  },
  "memory_mcp": {
    "entity_created": true,
    "relations_created": 5,
    "observations_added": 12
  },
  "serena_memory": {
    "file": "bug-bug-079",
    "created": true
  },
  "keywords": [
    "session",
    "redis",
    "middleware",
    "ttl",
    "timeout",
    "authentication"
  ],
  "related_bugs": [
    "BUG-045",
    "BUG-062"
  ]
}
```

### Fallback Response (MCP Unavailable)

```json
{
  "status": "PARTIAL_SUCCESS",
  "bug_id": "BUG-079",
  "documentation": {
    "file": ".claude/docs/solve/BUG-079_session-timeout.md",
    "created": true
  },
  "memory_mcp": {
    "available": false,
    "fallback_used": true,
    "fallback_path": ".claude/docs/solve/knowledge-base/BUG-079.md"
  },
  "serena_memory": {
    "available": false,
    "fallback_used": true,
    "fallback_path": ".claude/docs/solve/knowledge-base/BUG-079.md"
  },
  "keywords": [
    "session",
    "redis",
    "middleware"
  ],
  "fallback_index": ".claude/docs/solve/knowledge-base/index.json",
  "message": "MCP unavailable - saved to local files. Knowledge can be migrated when MCP is configured."
}
```

> **Important**: `PARTIAL_SUCCESS` does not block the workflow.
> Documentation (Step 2) always succeeds, so no knowledge loss occurs.

---

## Task Tool Integration

> **Reference**: [Task Tool Planning Guide](../skills/wm/rules/components/task-tool-planning-guide.md)

Use `TaskCreate` at workflow start, `TaskGet → TaskUpdate` for status changes.
See guide for Staleness Prevention and Metadata Schema.

---

## Tool Usage Guide

### Memory MCP

| Tool | Purpose | Knowledge Storage Usage |
|------|---------|------------------------|
| `create_entities` | Create entities | **Bug resolution entities** |
| `create_relations` | Set up relations | File/similar bug connections |
| `add_observations` | Add observations | **Keyword tagging** |

### Serena MCP

| Tool | Purpose | Knowledge Storage Usage |
|------|---------|------------------------|
| `write_memory` | Save memory | **Summary storage** |
| `list_memories` | List memories | Check existing memories |

---

## Document Storage Directory Structure

```
docs/
└── solve/
        ├── README.md                    # Index document
        ├── BUG-001_login-failure.md
        ├── BUG-002_session-timeout.md
        ├── BUG-003_email-validation.md
        └── ...
```

### README.md (Index) Auto-Update

```python
# Update README.md index when new bug is resolved
def update_index():
    index_content = "# Bug Resolution Knowledge Base\n\n"
    index_content += "| ID | Title | Keywords | Date |\n"
    index_content += "|-----|-------|----------|------|\n"

    for bug_file in Glob(pattern="BUG-*.md", path=".claude/docs/solve/"):
        # Parse and add to index
        index_content += f"| [{bug_id}]({file}) | {title} | {keywords} | {date} |\n"

    Write(
        file_path=".claude/docs/solve/README.md",
        content=index_content
    )
```

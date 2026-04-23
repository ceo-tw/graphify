---
title: Clarification Templates
type: pattern
impact: HIGH
used_by: [planner, Explore agent]
---
# Clarification Templates

Structured question templates for user clarification via AskUserQuestion.

## Purpose
Provide standardized clarification templates when subagents return `needs_clarification: true`.

## When to Use
- When subagent returns `needs_clarification: true`
- When request type cannot be determined
- When BUG_FIX details are unclear
- When development scope needs confirmation
- When multiple tasks need priority ordering

## Loop Prevention

```python
# IMPORTANT: Prevent infinite clarification loops
MAX_CLARIFICATION_ATTEMPTS = 3

# Track attempts in main context
clarification_attempts = 0

# If max attempts reached:
# 1. Proceed with best-effort interpretation
# 2. Set confidence to "low"
# 3. Log fallback_reason = "max_clarification_attempts_reached"
```

## Pattern

### Clarification Types Overview

| Type | When to Use | Primary Questions |
|------|-------------|-------------------|
| `request_type` | Ambiguous request type | "What type of work is this?" |
| `bug_info` | Unclear BUG_FIX details | reproduction, scope |
| `scope` | Unclear development scope | backend/frontend/infra |
| `priority` | Multiple tasks detected | task ordering |
| `constraint` | Potential constraints | time, resources |
| **`process_type_confirmation`** | **wm Step 2 confidence < 95%** | **"Bug type confirmation" / "Process type confirmation"** |

### Template: request_type

Use when the request type cannot be determined from keywords.

```json
{
  "clarification_type": "request_type",
  "clarification_data": {
    "question": "What type of work is this request?",
    "header": "Request Type",
    "options": [
      {
        "value": "NEW_DEVELOPMENT",
        "label": "New Development",
        "description": "Implement new feature from scratch. Choose when adding something that doesn't exist."
      },
      {
        "value": "MODIFICATION",
        "label": "Modification",
        "description": "Improve or change existing feature. Choose when updating existing functionality."
      },
      {
        "value": "BUG_FIX",
        "label": "Bug Fix",
        "description": "Fix error or problem. Choose when something doesn't work as expected."
      },
      {
        "value": "INQUIRY",
        "label": "Inquiry",
        "description": "Check status or analyze code. Choose when requesting information or analysis."
      }
    ],
    "multiSelect": false
  }
}
```

### Template: bug_info

Use when BUG_FIX is detected but details are unclear.

```json
{
  "clarification_type": "bug_info",
  "clarification_data": {
    "questions": [
      {
        "id": "reproduction",
        "question": "How often does the bug occur?",
        "header": "Reproduction Frequency",
        "options": [
          {
            "value": "always",
            "label": "Always",
            "description": "100% reproducible under same conditions."
          },
          {
            "value": "intermittent",
            "label": "Intermittent",
            "description": "Occurs sometimes, irregularly."
          },
          {
            "value": "specific_condition",
            "label": "Specific Condition",
            "description": "Only under certain circumstances."
          },
          {
            "value": "unknown",
            "label": "Unknown",
            "description": "Not sure how to reproduce."
          }
        ],
        "multiSelect": false
      },
      {
        "id": "scope",
        "question": "What is the impact scope of the bug?",
        "header": "Impact Scope",
        "options": [
          {
            "value": "single_feature",
            "label": "Single Feature",
            "description": "Affects only one feature or screen."
          },
          {
            "value": "multiple_features",
            "label": "Multiple Features",
            "description": "Affects several features or screens."
          },
          {
            "value": "system_wide",
            "label": "System Wide",
            "description": "Affects entire system."
          },
          {
            "value": "unknown",
            "label": "Unknown",
            "description": "Impact scope unclear."
          }
        ],
        "multiSelect": false
      }
    ]
  }
}
```

### Template: scope

Use when development scope is unclear.

```json
{
  "clarification_type": "scope",
  "clarification_data": {
    "question": "Which area does this development belong to?",
    "header": "Development Area",
    "options": [
      {
        "value": "backend",
        "label": "Backend",
        "description": "API, service logic, data processing. Server-side code."
      },
      {
        "value": "frontend",
        "label": "Frontend",
        "description": "UI, components, screens. Client-side code."
      },
      {
        "value": "infrastructure",
        "label": "Infrastructure",
        "description": "Configuration, deployment, environment."
      },
      {
        "value": "full_stack",
        "label": "Full Stack",
        "description": "Spans multiple areas. Both backend and frontend needed."
      }
    ],
    "multiSelect": false
  }
}
```

### Template: priority

Use when multiple tasks are detected and order matters.

```json
{
  "clarification_type": "priority",
  "clarification_data": {
    "question": "Multiple tasks detected. Select execution priority.",
    "header": "Priority",
    "options": [
      {
        "value": "sequential",
        "label": "Sequential (Recommended)",
        "description": "Execute tasks in order. One completes before next starts."
      },
      {
        "value": "parallel",
        "label": "Parallel",
        "description": "Execute independent tasks simultaneously. May have conflicts."
      },
      {
        "value": "user_priority",
        "label": "Custom Order",
        "description": "Specify task order manually."
      }
    ],
    "multiSelect": false
  }
}
```

### Template: process_type_confirmation

Use when wm Step 2 classification has confidence < 95%.

**Source**: This template is generated by wm during type classification.

#### BUG_FIX Sub-Type Confirmation

```json
{
  "clarification_type": "process_type_confirmation",
  "clarification_data": {
    "question": "Please confirm the bug fix type.\n\n[Auto-detected] BUG_FIX_COMPLEX (confidence: 75%)",
    "header": "Bug Type",
    "options": [
      {
        "value": "BUG_FIX_COMPLEX",
        "label": "Complex Bug (Recommended)",
        "description": "Multiple file modifications, refactoring needed. Uses Worktree."
      },
      {
        "value": "BUG_FIX_SIMPLE",
        "label": "Simple Bug",
        "description": "Typo, one-line fix. No Worktree needed."
      },
      {
        "value": "BUG_FIX_E2E",
        "label": "E2E Test Bug",
        "description": "Playwright, UI test related. Uses Worktree."
      }
    ],
    "multiSelect": false
  }
}
```

#### Development Type Confirmation

```json
{
  "clarification_type": "process_type_confirmation",
  "clarification_data": {
    "question": "Please confirm the process type.\n\n[Auto-detected] MODIFICATION (confidence: 72%)",
    "header": "Process",
    "options": [
      {
        "value": "MODIFICATION",
        "label": "Modification (Recommended)",
        "description": "Change/improve existing feature. Uses Worktree."
      },
      {
        "value": "NEW_DEVELOPMENT",
        "label": "New Development",
        "description": "Add new feature. Uses Worktree."
      },
      {
        "value": "BUG_FIX",
        "label": "Bug Fix",
        "description": "Resolve errors. (Sub-type confirmation follows)"
      }
    ],
    "multiSelect": false
  }
}
```

#### Dynamic Template Construction

Use the `clarification_data` generated in wm Step 2 directly:

```python
# Handle wm Step 2 classification result
if detection_result.get("needs_clarification"):
    # Pass clarification_data directly to AskUserQuestion
    data = detection_result["clarification_data"]

    user_response = AskUserQuestion(questions=[{
        "question": data["question"],
        "header": data["header"],
        "options": [
            {"label": opt["label"], "description": opt["description"]}
            for opt in data["options"]
        ],
        "multiSelect": data.get("multiSelect", False)
    }])

    # Extract confirmed type from user response
    confirmed_type = user_response.get(data["header"])

    # Use detected type as fallback if None
    if not confirmed_type:
        confirmed_type = detection_result["detected_type"]
```

#### Recommended Option Display Rules

- Add "(Recommended)" to the detected type
- Place as the first option
- Handle in AskUserQuestion's label field

```python
def format_options_with_recommendation(detected_type: str, options: list) -> list:
    """Display detected type as recommended option."""
    formatted = []
    for opt in options:
        label = opt["label"]
        if opt["value"] == detected_type:
            label = f"{label} (Recommended)"
        formatted.append({
            "value": opt["value"],
            "label": label,
            "description": opt["description"]
        })

    # Sort recommended option first
    formatted.sort(key=lambda x: 0 if "(Recommended)" in x["label"] else 1)
    return formatted
```

### Usage in Planner Skill

When a subagent returns `needs_clarification: true`:

```python
# In planner skill (Main Thread)
result = Task(subagent_type="Explore", prompt="...", model="haiku")

if result.get("needs_clarification"):
    data = result["clarification_data"]

    # Use templates from this file to format AskUserQuestion
    AskUserQuestion(questions=[{
        "question": data["question"],
        "header": data.get("header", "Confirm"),
        "options": [
            {"label": opt["label"], "description": opt["description"]}
            for opt in data["options"]
        ],
        "multiSelect": data.get("multiSelect", False)
    }])
```

### Multi-Question Handling (bug_info)

For `bug_info` which has multiple questions:

```python
if data.get("clarification_type") == "bug_info":
    questions = data["clarification_data"]["questions"]

    # Ask multiple questions
    AskUserQuestion(questions=[
        {
            "question": q["question"],
            "header": q["header"],
            "options": [
                {"label": opt["label"], "description": opt["description"]}
                for opt in q["options"]
            ],
            "multiSelect": q.get("multiSelect", False)
        }
        for q in questions
    ])
```

## References
- Main usage: SKILL.md Clarification Handling section
- Korean patterns: rules/guide-korean-patterns.md

---
title: Emoji Guidelines for Planner Workflow
type: pattern
impact: LOW
used_by: [planner, qa]
---
# Emoji Guidelines for Planner Workflow

Standardized emoji usage for user-facing output in planner workflow.

## Emoji Character Reference Table

This table provides the actual emoji characters for all icon names used in this guide.

### Status Icons
| Name | Emoji | Unicode | Purpose |
|------|-------|---------|---------|
| tick | ✅ | U+2705 | Completed, success |
| loop | 🔄 | U+1F504 | In progress |
| wait | ⏳ | U+23F3 | Pending, waiting |
| user | 👤 | U+1F464 | User input needed |
| x | ❌ | U+274C | Failed, error |
| warn | ⚠️ | U+26A0 | Warning |

### Section Icons
| Name | Emoji | Unicode | Purpose |
|------|-------|---------|---------|
| target | 🎯 | U+1F3AF | Main workflow |
| chart | 📊 | U+1F4CA | Summary, statistics |
| doc | 📄 | U+1F4C4 | Document |
| rocket | 🚀 | U+1F680 | Start |
| spark | ✨ | U+2728 | Complete |
| bulb | 💡 | U+1F4A1 | Tip, hint |
| party | 🎉 | U+1F389 | Celebration |

### Agent Icons
| Name | Emoji | Unicode | Agent |
|------|-------|---------|-------|
| clip | 📋 | U+1F4CB | 0-user-question |
| build | 🏗️ | U+1F3D7 | wm (Plan Writing) |
| ruler | 📐 | U+1F4D0 | design |
| memo | 📝 | U+1F4DD | planner-task |
| comp | 💻 | U+1F4BB | dev-executor |
| test | 🧪 | U+1F9EA | qa |
| search | 🔍 | U+1F50D | root-cause-finder |
| fix | 🔧 | U+1F527 | bug-fixer |
| book | 📚 | U+1F4DA | knowledge-keeper |

### Header Icons (AskUserQuestion)
| Name | Emoji | Unicode | Purpose |
|------|-------|---------|---------|
| edit | ✏️ | U+270F | Modify feedback |
| split | 🔀 | U+1F500 | Git operation |
| bolt | ⚡ | U+26A1 | Merge conflict |
| alert | 🚨 | U+1F6A8 | QA failure |

### Report Icons
| Name | Emoji | Unicode | Purpose |
|------|-------|---------|---------|
| folder | 📁 | U+1F4C1 | Files |
| graph | 📈 | U+1F4C8 | Statistics |
| puzzle | 🧩 | U+1F9E9 | Unit tests |
| link | 🔗 | U+1F517 | Integration |
| globe | 🌐 | U+1F310 | E2E tests |

## Purpose
Provides consistent visual indicators for workflow status, sections, agents, and reports.

## When to Use
- All user-facing output in planner workflow
- Progress displays and completion messages
- QA reports and verification results
- AskUserQuestion headers

## Pattern

### Workflow Status Icons

```
  Icon  Status       Usage
  ----  -----------  -------------------------------------
  tick  completed    Completed step, successful item
  loop  in_progress  Work in progress
  wait  pending      Waiting step
  user  user_input   Waiting for user input
  x     failed       Failed item
  warn  warning      Warning, attention needed
  ----  -----------  -------------------------------------
```

### Section Title Icons

```
  Icon   Section              Usage
  -----  -------------------  -------------------------------------
  target Main workflow        Planner Workflow progress
  chart  Summary              Plan summary, result summary
  doc    Document             PRD, document path
  rocket Start                Process start
  spark  Complete             Completion message
  bulb   Tip                  Tips, hints, guidance
  party  Celebration          Success celebration
  -----  -------------------  -------------------------------------
```

### Agent Icons

```
  Icon   Agent               Description
  -----  ------------------  -------------------------------------
  clip   0-user-question     Request classification
  build  wm (Plan Writing)  PHASE planning
  ruler  design            Architecture design
  memo   planner-task      Task decomposition
  comp   dev-executor      TDD implementation
  test   qa            QA verification
  search root-cause-finder Root cause analysis
  fix    bug-fixer         Bug fix
  book   knowledge-keeper  Knowledge recording
  -----  ------------------  -------------------------------------
```

### AskUserQuestion Header Icons

```
  Icon   Header Type      Usage
  -----  ---------------  -------------------------------------
  tick   Plan approval    Plan approval request
  edit   Modify feedback  Modification request
  ruler  Design confirm   Design related question
  search QA scope         QA scope selection
  x      Test failure     Test failure handling
  warn   Code quality     Quality violation handling
  split  Git operation    Git operation selection
  bolt   Merge conflict   Conflict resolution method
  test   QA confirm       General QA question
  alert  QA failure       3 retry failure
  -----  ---------------  -------------------------------------
```

### Report Icons

```
  Icon   Report Item       Usage
  -----  ----------------  -------------------------------------
  folder Files             File related (create, modify, check)
  ruler  Size/Metric       Size, measurements
  graph  Statistics        Statistics, coverage
  puzzle Unit tests        Unit tests
  link   Integration       Integration tests
  globe  E2E               E2E tests
  -----  ----------------  -------------------------------------
```

## AskUserQuestion Formatting Rules (CRITICAL)

**WARNING**: AskUserQuestion renders as plain text in CLI. Markdown is not supported.

### Prohibited Patterns

| Pattern | Problem | Alternative |
|---------|---------|-------------|
| `**bold**` | Rendered as-is | Use `[brackets]` or uppercase |
| `*italic*` | Rendered as-is | Plain text |
| `` `code` `` | Rendered as-is | Plain text or quotes |
| `# Header` | Rendered as-is | Brackets or emoji prefix |
| `- list item` | Works but not recommended | Numbers or arrows |

### Correct Formatting Examples

```
Wrong:
question: "**Original plan**: 17 files\n**Additional found**: 5 files"

Correct:
question: "[Original plan] 17 files (all complete)\n[Additional found] 5 files"
```

### Emphasis Alternatives

| Purpose | Markdown (prohibited) | Plain Text (recommended) |
|---------|----------------------|--------------------------|
| Label emphasis | `**label**:` | `[label]` or `label:` |
| Important item | `**important**` | `[IMPORTANT]` with emoji |
| Code/filename | `` `filename.tsx` `` | `filename.tsx` or `"filename.tsx"` |
| Number emphasis | `**17**` | `17` or `(17)` |

### Checklist (when writing AskUserQuestion)

- [ ] No `**` (bold) usage
- [ ] No `*` (italic) usage
- [ ] No `` ` `` (code) usage
- [ ] No `#` (header) usage
- [ ] Labels distinguished with `[]` or emoji
- [ ] Filenames in quotes or plain text

## References
- Main usage: SKILL.md Step 1.5, Step 4, Step 7
- QA reports: qa agent

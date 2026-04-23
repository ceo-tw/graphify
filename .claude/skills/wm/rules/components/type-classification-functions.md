# Type Classification Functions

Collection of classification functions - used in wm skill Step 2 (Type Classification).

---

## Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `classify_bug_fix` | `(plan_content: str) -> (type, confidence, alternatives)` | Classifies BUG_FIX into Simple/Complex/E2E sub-types. E2E keywords (playwright, .spec.ts, browser) take priority, then simple (typo, spelling) vs complex (refactor, multiple files) comparison |
| `classify_documentation` | `(plan_content: str) -> (type, confidence)` | Classifies DOCUMENTATION vs DOCUMENTATION_BATCH based on .md file reference count. 2 or more = BATCH |
| `detect_code_files_in_plan` | `(plan_content: str) -> (has_code_files, detected_files)` | Detects code file (.ts, .tsx, .py, etc.) references in DOCUMENTATION type. Suggests reclassification to MODIFICATION if detected |
| `is_complex_bug_fix` | `(plan_content: str) -> bool` | Determines BUG_FIX complexity (compares simple vs complex indicators) |
| `classify_multi_intent` | `(plan_content: str) -> (is_multi, intents, confidence)` | Detects MULTI_INTENT. Analyzes explicit markers (and, also, plus) + implicit patterns (numbered lists, issue refs) |
| `get_type_label` | `(type_name: str) -> str` | Returns user-facing display label |
| `get_type_description` | `(type_name: str) -> str` | Returns user-facing description |

---

## Classification Decision Tree (MANDATORY — follow in order)

```
1. Check MULTI_INTENT first:
   └─ Has explicit markers ("and", "also", "plus", numbered list with distinct tasks)?
      └─ YES (confidence >= 0.80) → MULTI_INTENT
         Split into individual intents, classify each recursively
      └─ AMBIGUOUS → Ask user: "Is this one task or multiple?"

2. Check BUG_FIX:
   └─ Contains error/bug/fix/broken keywords?
      └─ YES → classify_bug_fix():
         ├─ E2E keywords (playwright, .spec.ts, browser, ui test) → BUG_FIX_E2E
         ├─ Simple indicators > Complex indicators → BUG_FIX_SIMPLE
         └─ else → BUG_FIX_COMPLEX

3. Check DOCUMENTATION:
   └─ Only .md files referenced, no code files?
      └─ YES → classify_documentation():
         ├─ 1 file → DOCUMENTATION
         └─ 2+ files → DOCUMENTATION_BATCH
      └─ MIXED (code + docs) → MODIFICATION (docs as side effect)

4. Check INQUIRY / REPORT:
   └─ Question words (what, how, why, explain, show, list)?
      ├─ Asking about code/architecture → INQUIRY
      └─ Asking for status/summary/metrics → REPORT

5. Check CLEANUP:
   └─ Cleanup/refactor/remove/delete keywords without new feature?
      └─ YES → CLEANUP

6. Default:
   └─ Modifying existing feature → MODIFICATION
   └─ Creating new feature → NEW_DEVELOPMENT

7. Priority when multiple types match:
   MULTI_INTENT > BUG_FIX > MODIFICATION > NEW_DEVELOPMENT > DOCUMENTATION
```

### Mixed Scenario Rules

| Scenario | Classification | Rationale |
|----------|---------------|-----------|
| Code change + README update | MODIFICATION | Docs are side effect of code change |
| 3 .md files + 1 .ts file | MODIFICATION | Code file presence overrides DOCUMENTATION |
| "Fix bug and add feature" | MULTI_INTENT | Two distinct intents |
| "Fix the typo in auth.ts" | BUG_FIX_SIMPLE | Single-file, trivial change |
| "Refactor auth to use OAuth" | MODIFICATION | Existing feature change |

## Confidence Thresholds

| Confidence | Action |
|------------|--------|
| >= 0.95 | Auto proceed (no user interaction) |
| 0.80 - 0.94 | Ask user confirmation |
| < 0.80 | Ask user confirmation with strong recommendation |

---

## Code Extensions (detect_code_files_in_plan)

```
.ts .tsx .js .jsx .py .swift .go .java .rs .sql .sh .rb .php .c .cpp .h .hpp .css .scss .vue .svelte
```

---

## Key Indicators

### BUG_FIX Sub-type

| Sub-type | Indicators |
|----------|-----------|
| E2E | e2e, end-to-end, playwright, .spec.ts, browser, ui test |
| Simple | typo, simple, one-line, spelling |
| Complex | refactor, multiple files, architecture |

### MULTI_INTENT Markers

- **Explicit**: and, also, plus, as well as
- **Implicit**: numbered lists (1. 2. 3.), issue/bug numbered refs, comma-separated tasks

---

## Usage

This file is referenced by wm skill Step 2 (Type Classification):

```python
# Load classification functions (reference only, implement inline)
# See: .claude/skills/wm/rules/components/type-classification-functions.md
```

| Function | Consumer | Purpose |
|----------|----------|---------|
| `classify_bug_fix` | wm Step 2 | BUG_FIX sub-type classification |
| `classify_documentation` | wm Step 2 | DOCUMENTATION sub-type classification |
| `detect_code_files_in_plan` | wm Step 2 | Detect DOCUMENTATION -> MODIFICATION reclassification |
| `is_complex_bug_fix` | wm Step 2 | Determine worktree necessity |
| `classify_multi_intent` | wm Step 2 | MULTI_INTENT detection and intent classification |
| `get_type_label` | wm Step 3 (clarification) | User-facing display label |
| `get_type_description` | wm Step 3 (clarification) | User-facing description |

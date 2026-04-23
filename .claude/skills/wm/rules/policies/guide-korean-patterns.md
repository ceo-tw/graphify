---
title: Korean Uncertainty Patterns
type: guide
impact: MEDIUM
used_by: [wm, Explore]
---

# Korean Uncertainty Patterns

> **Source**: Extracted from deprecated `0-user-question.md` agent
> **Purpose**: Detect vague or ambiguous expressions in user requests
> **Used by**: Explore agent during intent classification (planner Step 1)

---

## Uncertainty Keywords (Korean)

These keywords indicate user uncertainty and may require clarification:

### Vague Description Keywords
| Keyword | Meaning | Example |
|---------|---------|---------|
| isang | strange/abnormal | "isanghage dongjakhaeyo" |
| mwonga | something | | "mwonga jalmotdoen geot gatayo" |
| gakkeum | sometimes | "gakkeum erroga nayo" |
| ttaettaero | occasionally | "ttaettaero neuryeojyeoyo" |
| gatayo | seems like | "munjega inneun geot gatayo" |
| geot gat | appears to be | "an doeneun geot gatayo" |
| jal moreugess | not sure | "wonineul jal moreugesseoyo" |
| hwaksilhaji | uncertain | "hwaksilhaji anhjiman..." |

### English Equivalents
| Keyword | Meaning |
|---------|---------|
| strange | isang |
| something | mwonga |
| sometimes | gakkeum, ttaettaero |
| seems | gatayo, geot gat |
| maybe | ama |
| probably | amado |

---

## Uncertainty Indicators for BUG_FIX

When classifying a request as BUG_FIX, check for these uncertainty indicators:

### High Uncertainty (requires clarification)
```
+----------------------------------+------------------------------------------------+
| Indicator                        | Examples                                       |
+----------------------------------+------------------------------------------------+
| Vague description                | "isanghage dongjakhaeyo", "mwonga jalmotdoen   |
|                                  | geot gatayo"                                   |
| Missing reproduction steps       | No specific steps mentioned                    |
| Ambiguous scope                  | "jeonchejeogeuro", "gakkeum", "ttaettaero"     |
| Mixed request types              | "sujeonghago gaeseonhaejuseyo"                 |
+----------------------------------+------------------------------------------------+
```

### Low Uncertainty (can proceed)
```
+----------------------------------+------------------------------------------------+
| Indicator                        | Examples                                       |
+----------------------------------+------------------------------------------------+
| Specific error message           | "TypeError: Cannot read property..."           |
| Clear reproduction steps         | "1. click 2. input 3. error occurs"            |
| Specific location                | "when clicking login button"                   |
| Consistent reproduction          | "hangsang balsaeng", "100% jaehyeondoem"       |
+----------------------------------+------------------------------------------------+
```

---

## Detection Logic

```python
# Check for uncertainty keywords in user request
def detect_uncertainty(request: str) -> dict:
    vague_keywords = [
        "isang", "mwonga", "gakkeum", "ttaettaero", "gatayo", "geot gat",
        "jal moreugess", "hwaksilhaji", "strange", "something", "sometimes"
    ]

    specific_keywords = [
        "keullik", "ib-ryeok", "hwamyeon", "beoteun", "error meissiji",
        "click", "input", "screen", "button", "error message"
    ]

    vague_count = sum(1 for kw in vague_keywords if kw in request)
    specific_count = sum(1 for kw in specific_keywords if kw in request)

    if vague_count > 0 and specific_count == 0:
        return {"uncertainty_level": "high", "needs_clarification": True}
    elif vague_count > 0 and specific_count > 0:
        return {"uncertainty_level": "medium", "needs_clarification": False}
    else:
        return {"uncertainty_level": "low", "needs_clarification": False}
```

---

## Usage in Explore Agent Prompt

When invoking Explore for intent classification, include:

```
### Uncertainty Detection (Korean)

Check for these Korean uncertainty keywords that may require clarification:
- Vague: "isang", "mwonga", "gakkeum", "ttaettaero", "gatayo", "geot gat",
         "jal moreugess", "hwaksilhaji"
- Missing specifics: No mention of "keullik", "ib-ryeok", "hwamyeon", "beoteun"

If HIGH uncertainty detected in BUG_FIX request:
- Set needs_clarification: true
- Set clarification_type: "bug_info"
```

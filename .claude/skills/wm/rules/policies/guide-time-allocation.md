# PHASE → TASK Time Allocation

> **Source**: Migrated from `planning-guide-for-task/references/time-allocation.md`
> **Purpose**: Rules for distributing PHASE time to individual TASKs
> **Used by**: planner-task agent

---

## TDD Stage Weights

| TDD Stage | Weight | Rationale |
|-----------|--------|-----------|
| RED | 30% | Test design, writing, scenario composition |
| GREEN | 50% | Implementation, debugging, integration |
| REFACTOR | 20% | Code cleanup, documentation, optimization |

---

## Distribution Algorithm

```
Input: PHASE time = 2h (120 min)
       RED Task count = 2
       GREEN Task count = 2
       REFACTOR Task count = 1

Calculation:
  RED total time     = 120 × 0.3 = 36 min
  GREEN total time   = 120 × 0.5 = 60 min
  REFACTOR total time = 120 × 0.2 = 24 min

Per-Task time:
  RED Task      = 36 ÷ 2 = 18 min → rounded → 20 min
  GREEN Task    = 60 ÷ 2 = 30 min
  REFACTOR Task = 24 ÷ 1 = 24 min → rounded → 25 min

Verification: 20×2 + 30×2 + 25×1 = 125 min ≈ 120 min (error 4%)
```

---

## Task Size Adjustment

| Condition | Adjustment |
|-----------|------------|
| Modify 3+ files | +10 min |
| Create new file (non-test) | +5 min |
| Complex logic (noted in PRD) | +15 min |
| Simple config change | -5 min |
| Reuse existing code | -5 min |

---

## Final Validation Rules

- Total TASK time ≈ PHASE time (±10% tolerance)
- Individual TASK time: 15-60 min range
- Under 15 min → Consider merging with another Task
- Over 60 min → Task split required

---

## Code Example

```python
def allocate_time(phase_minutes: int, task_counts: dict) -> dict:
    """Distribute PHASE time by TDD stage"""

    weights = {"RED": 0.3, "GREEN": 0.5, "REFACTOR": 0.2}
    allocation = {}

    for stage, weight in weights.items():
        total_stage_time = phase_minutes * weight
        task_count = task_counts.get(stage, 1)
        per_task = round(total_stage_time / task_count / 5) * 5  # Round to 5 min
        allocation[stage] = max(15, min(60, per_task))  # Limit to 15-60 min range

    return allocation

# Usage example
result = allocate_time(120, {"RED": 2, "GREEN": 2, "REFACTOR": 1})
# → {"RED": 20, "GREEN": 30, "REFACTOR": 25}
```

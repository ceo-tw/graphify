# BUG_FIX (Simple) Process

Process to follow for simple bug fixes.

---

## Plan Template (Copy to Plan Document)

Copy this entire block to your plan document's `## 0. Execution Process` section (TOP of document):

```markdown
## 0. Execution Process (MUST - DO NOT SKIP)

⛔ **HARD REQUIREMENT - DO NOT SKIP**
This process MUST be followed exactly. Skipping or modifying steps is PROHIBITED.

This plan is **BUG_FIX (Simple)** type.

Execute the following skill:

- [ ] Skill(skill="solve")
- [ ] Cleanup (invoke plan-cleanup skill)

The solve skill automatically performs analysis, fix, and verification.

## Agent Execution Log

| Agent | agentId | Status | Timestamp | Purpose |
|-------|---------|--------|-----------|---------|
| solve | - | pending | - | Automated bug fix |

### Quality Gate Checklist (Simplified)

The solve skill handles verification automatically:

- [ ] **Build success**: Confirmed by solve skill
- [ ] **Tests pass**: Confirmed by solve skill
- [ ] **Bug fixed**: Confirmed by solve skill
```

---

## Simple vs Complex Criteria

### Simple (Use this process)

- Cause is clear
- Can be fixed with single file modification
- Reproduction method is certain
- Impact scope is limited

### Complex (Use different process)

- Cause unclear, analysis needed
- Modifications needed across multiple files
- Reproduction is difficult or intermittent
- Potential for widespread impact

---

## solve skill Behavior

The solve skill automatically performs:

1. Problem definition
2. Information gathering
3. Analysis
4. Hypothesis formulation
5. Resolution
6. Documentation

---

## Execution Pattern

```python
# Execute solve skill
Skill(skill="solve")
```

---

## Notes

1. **Determine if Simple**: If uncertain, classify as Complex
2. **Trust solve skill**: The skill manages the entire process
3. **Switch to Complex on failure**: If solve cannot resolve, re-plan with Complex process
4. **Agent Execution Log**: Include the log table from Plan Template for tracking solve skill execution

---

## Shared Rules

> See [process-base.md](process-base.md) for Plan Cleanup.

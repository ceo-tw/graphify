# TDD Quality Gate (Shared Component)

Mandatory quality gate executed before every commit in REFACTOR phase.
Used by: `dev-executor`, `bug-fixer`

---

## Execution

**Timing**: REFACTOR complete → Quality Gate → Commit (this order is mandatory)

```python
# code-quality skill invocation (mandatory before commit)
quality_result = Skill(skill="code-quality")

if quality_result.failed:
    raise Error(
        "Quality Gate failed. Commit BLOCKED.\n"
        f"Violations: {quality_result.violations}\n"
        "Fix all violations before attempting to commit."
    )

# Only commit after quality gate passes
Bash(command=f"cd {worktree_path} && git commit -m '{commit_prefix}: {description}'")
```

---

## Verification Items

- File length: 300 lines or fewer per file
- Documentation: All public functions have JSDoc/docstring
- Architecture: Dependency rules compliant (Clean Architecture)
- No new violations introduced by changes

---

## Failure Handling

1. Output violation details
2. Attempt auto-fix (if possible)
3. If still failing:
   - Commit BLOCKED
   - Follow [failure-messages.md](../../code-quality/references/failure-messages.md)
   - Re-run quality gate after fixes

---

## Rules

- No exceptions, even for urgent fixes
- All verification items must pass
- Commit is blocked until violations = 0

# Rollback Strategy Template

> **Source**: Migrated from `planning-guide-for-phase/references/rollback-template.md`
> **Purpose**: Template for documenting PHASE rollback steps.
> **Used by**: wm (Plan Writing)

---

Each PHASE should document rollback steps using this template:

```markdown
### Rollback for PHASE {N}

**Code Changes to Revert**:
- File: {path} - Remove/modify {description}

**Database Changes** (if any):
- Migration: {migration_name} - Run down migration

**Dependencies** (if any):
- Remove package: {package_name}

**Verification**:
- Run: {test command}
- Expected: {outcome}
```

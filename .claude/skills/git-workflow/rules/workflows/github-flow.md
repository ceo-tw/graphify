# GitHub Flow Rules

## Overview

GitHub Flow is a lightweight, branch-based workflow centered on a single `main` branch. All changes go through feature branches and Pull Requests.

**Core principle**: `main` is always deployable. All work happens in short-lived branches.

## Branch Structure

```
main (always deployable)
  ├── feature/*   (new features)
  ├── fix/*       (bug fixes)
  ├── hotfix/*    (urgent production fixes)
  ├── chore/*     (maintenance tasks)
  └── docs/*      (documentation changes)
```

**Permanent branches**: `main` only
**Temporary branches**: All others (deleted after merge)

## Allowed Branch Prefixes

- `feature/`
- `fix/`
- `hotfix/`
- `chore/`
- `docs/`

## Source Branch Rules

| Branch Type | Source Branch | Merge Target |
|-------------|-------------|--------------|
| `feature/*` | `main` | `main` (via PR) |
| `fix/*` | `main` | `main` (via PR) |
| `hotfix/*` | `main` | `main` (via PR) |
| `chore/*` | `main` | `main` (via PR) |
| `docs/*` | `main` | `main` (via PR) |

**All branches originate from `main` and merge back to `main`.**

## Decision Matrix

| Current Branch | Work Type | Action | Recommendation |
|----------------|-----------|--------|----------------|
| `main` | Any code change | **BLOCK** | Create appropriate branch from `main` |
| `feature/*` | In progress | **PROCEED** | Continue working on current branch |
| `feature/*` | Complete | **RECOMMEND** | Create PR to `main` |
| `fix/*` | In progress | **PROCEED** | Continue working on current branch |
| `fix/*` | Complete | **RECOMMEND** | Create PR to `main` |
| `hotfix/*` | In progress | **PROCEED** | Continue working on current branch |
| `hotfix/*` | Complete | **RECOMMEND** | Create PR to `main` (expedited review) |
| `chore/*` | In progress | **PROCEED** | Continue working on current branch |
| `chore/*` | Complete | **RECOMMEND** | Create PR to `main` |
| `docs/*` | In progress | **PROCEED** | Continue working on current branch |
| `docs/*` | Complete | **RECOMMEND** | Create PR to `main` |
| Other | Any | **BLOCK** | Branch name doesn't match workflow. Suggest correct prefix. |

## Branch Matching Rules

To determine the current branch category:
- `main` → exact match
- `feature/*` → starts with `feature/`
- `fix/*` → starts with `fix/`
- `hotfix/*` → starts with `hotfix/`
- `chore/*` → starts with `chore/`
- `docs/*` → starts with `docs/`

## Work Type to Branch Prefix

| Work Type | Recommended Prefix |
|-----------|-------------------|
| NEW_DEVELOPMENT | `feature/` |
| MODIFICATION | `feature/` |
| BUG_FIX (normal) | `fix/` |
| BUG_FIX (critical) | `hotfix/` |
| Refactoring | `feature/` |
| Documentation | `docs/` |
| Chore | `chore/` |

## PR Rules

- **All merges to `main` require a Pull Request**
- PR must pass CI checks before merge
- At least 1 reviewer approval recommended
- Squash merge or merge commit (team preference)
- Delete branch after merge

## AskUserQuestion Templates

### BLOCK on main
```
Question: "{work_type}으로 판단됩니다. main에서 {prefix}{description}으로 분기하여 진행(권장)"
Options:
  1. "{prefix}{description} 브랜치 생성 (권장)"
  2. "다른 브랜치명 지정"
```

### RECOMMEND PR creation
```
Question: "{current_branch} 작업이 완료된 것으로 보입니다. main으로 PR 생성을 권장합니다."
Options:
  1. "PR 생성 진행 (권장)"
  2. "아직 작업 중 - 계속 진행"
```

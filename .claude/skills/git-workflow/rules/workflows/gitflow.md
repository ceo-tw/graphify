# GitFlow Rules

## Overview

GitFlow is a structured branching model with dedicated branches for development, releases, and hotfixes. It separates ongoing development from production-ready code.

**Core principle**: `main` reflects production. `develop` is the integration branch. Features, releases, and hotfixes have dedicated branch types.

## Branch Structure

```
main (production-ready, tagged releases)
  │
develop (integration branch for ongoing work)
  ├── feature/*   (new features, from develop)
  ├── bugfix/*    (bug fixes on develop)
  │
release/* (release preparation, from develop → main + develop)
hotfix/*  (urgent production fixes, from main → main + develop)
support/* (legacy version maintenance)
```

**Permanent branches**: `main`, `develop`
**Temporary branches**: All others (deleted after merge)

## Allowed Branch Prefixes

- `feature/`
- `bugfix/`
- `release/`
- `hotfix/`
- `support/`

## Source Branch and Merge Target Rules

| Branch Type | Source Branch | Merge Target |
|-------------|-------------|--------------|
| `feature/*` | `develop` | `develop` (via PR) |
| `bugfix/*` | `develop` | `develop` (via PR) |
| `release/*` | `develop` | `main` AND `develop` (via PR) |
| `hotfix/*` | `main` | `main` AND `develop` (via PR) |
| `support/*` | `main` (tag) | Tagged version |

## Decision Matrix

| Current Branch | Work Type | Action | Recommendation |
|----------------|-----------|--------|----------------|
| `main` | Any change | **BLOCK** | Use `develop` for features/bugfixes, or `hotfix/*` from `main` for critical fixes |
| `develop` | Feature / Enhancement | **BLOCK** | Create `feature/*` branch from `develop` |
| `develop` | Bug fix (normal) | **BLOCK** | Create `bugfix/*` branch from `develop` |
| `develop` | Critical fix | **BLOCK** | Create `hotfix/*` branch from `main` |
| `feature/*` | In progress | **PROCEED** | Continue working on current branch |
| `feature/*` | Complete | **RECOMMEND** | Create PR to `develop` |
| `bugfix/*` | In progress | **PROCEED** | Continue working on current branch |
| `bugfix/*` | Complete | **RECOMMEND** | Create PR to `develop` |
| `release/*` | Bug fix only | **PROCEED** | Only bug fixes allowed (no new features!) |
| `release/*` | New feature | **BLOCK** | New features forbidden on release branch |
| `release/*` | Complete | **RECOMMEND** | Create PR to `main` AND PR to `develop` |
| `hotfix/*` | In progress | **PROCEED** | Continue working on current branch |
| `hotfix/*` | Complete | **RECOMMEND** | Create PR to `main` AND PR to `develop` |
| `support/*` | In progress | **PROCEED** | Continue working on current branch |
| Other | Any | **BLOCK** | Branch name doesn't match workflow. Suggest correct prefix. |

## Branch Matching Rules

To determine the current branch category:
- `main` → exact match
- `develop` → exact match
- `feature/*` → starts with `feature/`
- `bugfix/*` → starts with `bugfix/`
- `release/*` → starts with `release/`
- `hotfix/*` → starts with `hotfix/`
- `support/*` → starts with `support/`

## Work Type to Branch Prefix

| Work Type | Recommended Prefix | Source Branch |
|-----------|-------------------|--------------|
| NEW_DEVELOPMENT | `feature/` | `develop` |
| MODIFICATION | `feature/` | `develop` |
| BUG_FIX (normal) | `bugfix/` | `develop` |
| BUG_FIX (critical) | `hotfix/` | `main` |
| Refactoring | `feature/` | `develop` |
| Documentation | `feature/` | `develop` |
| Chore | `feature/` | `develop` |

## Special Rules

### Release Branch Restrictions
- **Only bug fixes** are permitted on `release/*` branches
- No new features, no refactoring
- Version number updates and changelog edits are allowed
- After completion: merge to BOTH `main` (with tag) and `develop`

### Hotfix Dual Merge
- Hotfixes MUST be merged to both `main` AND `develop`
- If a `release/*` branch exists, merge to `release/*` instead of `develop`
- Tag the merge commit on `main` (e.g., `v1.0.1`)

### Develop Direct Commit
- Direct commits to `develop` are discouraged
- All changes should go through `feature/*` or `bugfix/*` branches with PR

## AskUserQuestion Templates

### BLOCK on main
```
Question: "main 브랜치에서 직접 작업은 GitFlow 규칙에 의해 금지됩니다. {work_type}으로 판단됩니다."
Options:
  1. "develop에서 {prefix}{description} 브랜치 생성 (권장)" (for features/bugfixes)
  2. "main에서 hotfix/{description} 브랜치 생성" (for critical fixes)
  3. "다른 브랜치명 지정"
```

### BLOCK on develop
```
Question: "{work_type}으로 판단됩니다. develop에서 {prefix}{description}으로 분기하여 진행(권장)"
Options:
  1. "{prefix}{description} 브랜치 생성 (권장)"
  2. "다른 브랜치명 지정"
```

### RECOMMEND feature/bugfix completion
```
Question: "{current_branch} 작업이 완료된 것으로 보입니다. develop으로 PR 생성을 권장합니다."
Options:
  1. "develop으로 PR 생성 (권장)"
  2. "아직 작업 중 - 계속 진행"
```

### RECOMMEND release completion
```
Question: "{current_branch} 릴리스 준비가 완료된 것으로 보입니다."
Options:
  1. "main + develop 양쪽으로 PR 생성 (권장)"
  2. "아직 릴리스 준비 중 - 계속 진행"
```

### RECOMMEND hotfix completion
```
Question: "{current_branch} 핫픽스가 완료된 것으로 보입니다."
Options:
  1. "main + develop 양쪽으로 PR 생성 (권장)"
  2. "아직 수정 중 - 계속 진행"
```

### BLOCK new feature on release branch
```
Question: "release 브랜치에서는 버그 수정만 허용됩니다. 새 기능은 develop에서 별도 feature 브랜치로 작업해주세요."
Options:
  1. "develop에서 feature/{description} 생성 (권장)"
  2. "버그 수정으로 변경하여 현재 브랜치에서 계속"
```

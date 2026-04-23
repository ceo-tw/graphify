# GitLab Flow Rules

## Overview

GitLab Flow combines the simplicity of GitHub Flow with environment-based deployment branches. Code flows downstream only: feature → main → pre-production → production.

**Core principle**: `main` serves as the integration branch (maps to staging). Environment branches (`pre-production`, `production`) receive code only via promotion (merge/MR). No upstream merges.

## Branch Structure

```
main (integration branch, maps to staging)
  ├── feature/*    (new features, from main)
  ├── fix/*        (bug fixes, from main)
  ├── hotfix/*     (urgent fixes, from main)
  ├── chore/*      (maintenance, from main)
  ├── docs/*       (documentation, from main)
  ├── refactor/*   (refactoring, from main)
  └── test/*       (test additions, from main)

pre-production (pre-production environment, promoted from main)
production     (production environment, promoted from pre-production)
```

**Permanent branches**: `main`, `pre-production`, `production`
**Temporary branches**: All others (deleted after merge)

## Allowed Branch Prefixes

- `feature/`
- `fix/`
- `hotfix/`
- `chore/`
- `docs/`
- `refactor/`
- `test/`

## Source Branch and Merge Target Rules

| Branch Type | Source Branch | Merge Target |
|-------------|-------------|--------------|
| `feature/*` | `main` | `main` (via MR) |
| `fix/*` | `main` | `main` (via MR) |
| `hotfix/*` | `main` | `main` (via MR) + cherry-pick to `production` |
| `chore/*` | `main` | `main` (via MR) |
| `docs/*` | `main` | `main` (via MR) |
| `refactor/*` | `main` | `main` (via MR) |
| `test/*` | `main` | `main` (via MR) |

### Environment Promotion (downstream only)

```
main → pre-production → production
```

- `main` → `pre-production`: MR after staging tests pass
- `pre-production` → `production`: MR after pre-production tests pass
- **Reverse merges are strictly forbidden**

## Decision Matrix

| Current Branch | Work Type | Action | Recommendation |
|----------------|-----------|--------|----------------|
| `main` | Any code change | **BLOCK** | Create appropriate branch from `main` |
| `production` | Any change | **BLOCK** | Direct commits to `production` are forbidden |
| `pre-production` | Any change | **BLOCK** | Direct commits to `pre-production` are forbidden |
| `feature/*` | In progress | **PROCEED** | Continue working on current branch |
| `feature/*` | Complete | **RECOMMEND** | Create MR to `main` |
| `fix/*` | In progress | **PROCEED** | Continue working on current branch |
| `fix/*` | Complete | **RECOMMEND** | Create MR to `main` |
| `hotfix/*` | In progress | **PROCEED** | Continue working on current branch |
| `hotfix/*` | Complete | **RECOMMEND** | Create MR to `main` + cherry-pick to `production` |
| `chore/*` | In progress | **PROCEED** | Continue working on current branch |
| `chore/*` | Complete | **RECOMMEND** | Create MR to `main` |
| `docs/*` | In progress | **PROCEED** | Continue working on current branch |
| `docs/*` | Complete | **RECOMMEND** | Create MR to `main` |
| `refactor/*` | In progress | **PROCEED** | Continue working on current branch |
| `refactor/*` | Complete | **RECOMMEND** | Create MR to `main` |
| `test/*` | In progress | **PROCEED** | Continue working on current branch |
| `test/*` | Complete | **RECOMMEND** | Create MR to `main` |
| Other | Any | **BLOCK** | Branch name doesn't match workflow. Suggest correct prefix. |

## Branch Matching Rules

To determine the current branch category:
- `main` → exact match
- `production` → exact match
- `pre-production` → exact match
- `feature/*` → starts with `feature/`
- `fix/*` → starts with `fix/`
- `hotfix/*` → starts with `hotfix/`
- `chore/*` → starts with `chore/`
- `docs/*` → starts with `docs/`
- `refactor/*` → starts with `refactor/`
- `test/*` → starts with `test/`

## Work Type to Branch Prefix

| Work Type | Recommended Prefix | Source Branch |
|-----------|-------------------|--------------|
| NEW_DEVELOPMENT | `feature/` | `main` |
| MODIFICATION | `feature/` | `main` |
| BUG_FIX (normal) | `fix/` | `main` |
| BUG_FIX (critical) | `hotfix/` | `main` |
| Refactoring | `refactor/` | `main` |
| Documentation | `docs/` | `main` |
| Chore | `chore/` | `main` |
| Test | `test/` | `main` |

## Special Rules

### Environment Branch Protection
- `production` and `pre-production` are **protected branches**
- Direct push/commit is strictly forbidden
- Changes arrive only via downstream MR promotion

### Hotfix Process (cherry-pick preferred)
1. Create `hotfix/*` from `main`
2. Fix the issue and MR to `main`
3. After merge to `main`, cherry-pick the fix commit to `production`
4. Alternative: MR from `main` → `pre-production` → `production` (full promotion)

### Downstream-Only Flow
- Code MUST flow: `main` → `pre-production` → `production`
- **Never** merge `production` → `main` (reverse merge forbidden)
- **Never** merge `feature/*` → `production` directly

## AskUserQuestion Templates

### BLOCK on main
```
Question: "{work_type}으로 판단됩니다. main에서 {prefix}{description}으로 분기하여 진행(권장)"
Options:
  1. "{prefix}{description} 브랜치 생성 (권장)"
  2. "다른 브랜치명 지정"
```

### BLOCK on production/pre-production
```
Question: "{current_branch} 브랜치에 직접 커밋은 GitLab Flow 규칙에 의해 금지됩니다. 환경 브랜치는 프로모션(MR)으로만 업데이트됩니다."
Options:
  1. "main에서 {prefix}{description} 브랜치 생성 (권장)"
  2. "다른 브랜치명 지정"
```

### RECOMMEND MR to main
```
Question: "{current_branch} 작업이 완료된 것으로 보입니다. main으로 MR 생성을 권장합니다."
Options:
  1. "main으로 MR 생성 (권장)"
  2. "아직 작업 중 - 계속 진행"
```

### RECOMMEND hotfix completion
```
Question: "{current_branch} 핫픽스가 완료된 것으로 보입니다. main으로 MR 후 production에 cherry-pick을 권장합니다."
Options:
  1. "main으로 MR + production cherry-pick (권장)"
  2. "main으로 MR만 생성"
  3. "아직 수정 중 - 계속 진행"
```

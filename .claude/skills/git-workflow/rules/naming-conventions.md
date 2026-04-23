# Branch Naming Conventions

## Common Rules (All Workflows)

### Format

```
<type>/<description>
```

or with ticket ID:

```
<type>/<ticket-id>-<description>
```

### Validation Rules

| Rule | Valid | Invalid |
|------|-------|---------|
| Lowercase only | `feature/user-auth` | `Feature/UserAuth` |
| Hyphen separators | `fix/login-error` | `fix/login_error` |
| Max 50 characters | `feature/add-oauth` | `feature/add-oauth-google-facebook-apple-kakao-github` |
| Single slash only | `feature/user-auth` | `feature/auth/login` |
| No trailing period | `fix/null-check` | `fix/null-check.` |
| No spaces | `chore/update-deps` | `chore/update deps` |
| Alphanumeric + hyphen only | `feature/oauth-2` | `feature/OAuth_2.0!` |
| Descriptive name | `feature/add-oauth` | `feature/task1` |

### Regex Pattern for Validation

```
^[a-z]+\/[a-z0-9][a-z0-9-]*[a-z0-9]$
```

With ticket ID:

```
^[a-z]+\/[A-Z]+-[0-9]+-[a-z0-9][a-z0-9-]*[a-z0-9]$
```

**Additional checks:**
- Total length <= 50 characters
- No consecutive hyphens (`--`)
- No slash after the type prefix (only one `/` allowed)

---

## Per-Workflow Allowed Types

### GitHub Flow

| Prefix | Purpose |
|--------|---------|
| `feature/` | New features and enhancements |
| `fix/` | Bug fixes |
| `hotfix/` | Urgent production fixes |
| `chore/` | Maintenance, dependencies, config |
| `docs/` | Documentation-only changes |

### GitFlow

| Prefix | Purpose |
|--------|---------|
| `feature/` | New features (from `develop`) |
| `bugfix/` | Bug fixes on develop (from `develop`) |
| `release/` | Release preparation (from `develop`) |
| `hotfix/` | Urgent production fixes (from `main`) |
| `support/` | Legacy version maintenance |

**Note:** GitFlow uses `bugfix/` instead of `fix/` for non-critical bugs.

### GitLab Flow

| Prefix | Purpose |
|--------|---------|
| `feature/` | New features and enhancements |
| `fix/` | Bug fixes |
| `hotfix/` | Urgent production fixes |
| `chore/` | Maintenance, dependencies, config |
| `docs/` | Documentation-only changes |
| `refactor/` | Code restructuring |
| `test/` | Test additions or modifications |

---

## Name Correction Logic

When a branch name violates conventions, apply these corrections:

1. **Uppercase → lowercase**: `Feature/Login` → `feature/login`
2. **Underscores → hyphens**: `feature/user_auth` → `feature/user-auth`
3. **Spaces → hyphens**: `feature/user auth` → `feature/user-auth`
4. **Multiple slashes → single**: `feature/auth/login` → `feature/auth-login`
5. **Trailing period removed**: `fix/bug.` → `fix/bug`
6. **Truncate to 50 chars**: preserve type prefix, trim description
7. **Wrong prefix for workflow**: suggest the closest valid prefix

### Correction Example

```
Input:  "Feature/Add_User_Authentication_Module."
Workflow: github-flow

Corrections applied:
  1. Uppercase → lowercase: "feature/add_user_authentication_module."
  2. Underscores → hyphens: "feature/add-user-authentication-module."
  3. Trailing period removed: "feature/add-user-authentication-module"
  4. Length check: 39 chars ✓

Result: "feature/add-user-authentication-module"
```

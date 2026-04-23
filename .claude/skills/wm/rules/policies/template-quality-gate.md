# Quality Gate Template

> **Source**: Migrated from `planning-guide-for-phase/references/quality-gate-template.md`
> **Purpose**: Quality gate checklist for each PHASE.
> **Used by**: wm, qa agents

---

Each PHASE must pass all quality gates before proceeding.

## PHASE Quality Gate Checklist

```markdown
### Quality Gate ✋

**⚠️ STOP: Do NOT proceed until ALL checks pass**

---

#### TDD Compliance (CRITICAL)

- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Test coverage meets requirements (≥80% for business logic)

**Verification Command**:
```bash
# Adapt to your testing framework:
# bun test --coverage
# pytest --cov=src --cov-report=html
# go test -cover ./...
```

---

#### Build & Tests

- [ ] **Build**: Project builds/compiles without errors
- [ ] **All Tests Pass**: 100% of tests passing (no skipped tests)
- [ ] **Test Performance**: Test suite completes in acceptable time (<5 min)
- [ ] **No Flaky Tests**: Tests pass consistently (run 3+ times)

**Verification Commands**:
```bash
# Build
[your build command]

# Tests
[your test command]
```

---

#### Code Quality

- [ ] **Linting**: No linting errors or warnings
- [ ] **Formatting**: Code formatted per project standards
- [ ] **Type Safety**: Type checker passes (if applicable)
- [ ] **Static Analysis**: No critical issues

**Verification Commands**:
```bash
# Lint
[your linter command]

# Format check
[your formatter check command]

# Type check
[your type checker command]
```

---

#### Security & Performance

- [ ] **Dependencies**: No known security vulnerabilities
- [ ] **Performance**: No performance regressions
- [ ] **Memory**: No memory leaks or resource issues
- [ ] **Error Handling**: Proper error handling implemented

**Verification Commands**:
```bash
# Security audit
[your dependency audit command]
```

---

#### Functionality

- [ ] **Feature Works**: Feature works as expected
- [ ] **Edge Cases**: Boundary conditions tested
- [ ] **Error States**: Error handling verified
- [ ] **No Regressions**: Existing features still work

**Manual Test Checklist**:
- [ ] Test case 1: {Specific scenario}
- [ ] Test case 2: {Edge case}
- [ ] Test case 3: {Error handling}

---

#### Documentation

- [ ] **Code Comments**: Complex logic documented
- [ ] **API Docs**: Public interfaces documented
- [ ] **README**: Usage instructions updated if needed

---

#### Clean Architecture (if applicable)

- [ ] Domain layer has no external dependencies
- [ ] Application does not reference Infrastructure directly
- [ ] Data crossing boundaries uses DTOs
- [ ] External dependencies abstracted via interfaces

---

**All checks passed?** ✅ Proceed to next PHASE
**Any check failed?** ❌ Fix issues before continuing
```

## Quick Reference: Commands by Ecosystem

### JavaScript/TypeScript
```bash
bun run test -- --coverage
bun run lint
bun run type-check
bun run build
bun pm audit
```

### Python
```bash
pytest --cov=src --cov-report=html
black --check .
mypy .
flake8 .
pip-audit
```

### Go
```bash
go test -cover ./...
golangci-lint run
go build ./...
```

### Java (Maven)
```bash
mvn test
mvn jacoco:report
mvn checkstyle:check
mvn verify
```

### .NET
```bash
dotnet test /p:CollectCoverage=true
dotnet format --verify-no-changes
dotnet build
```

### Ruby
```bash
bundle exec rspec --coverage
rubocop
rake build
bundle-audit check
```

### Rust
```bash
cargo test
cargo clippy
cargo build
cargo audit
```

---
name: best-practices
type: library
description: "프로젝트 전반의 베스트 프랙티스 규칙 모음. 다른 스킬에서 참조하여 코드 품질과 일관성을 유지합니다."
user-invocable: false
---

# best-practices

프로젝트 코드 품질과 일관성을 위한 규칙 라이브러리입니다.

## 구조

이 스킬은 독립 실행되지 않으며, 다른 스킬의 rules로 참조됩니다.

## Rules

### 공통

- `_sections.md` - 규칙 섹션 정의
- `_template.md` - 규칙 작성 템플릿

### Go

- **에러 처리**: custom-types, defer, explicit-returns, wrapping
- **동시성**: channels, context, goroutines, waitgroup
- **인터페이스**: accept-return, implicit, segregation, small
- **코드 구조**: internal, modules, naming, package-structure
- **안티패턴**: empty-interface, goroutine-leaks, ignoring-errors

### Python

- **에러 처리**: hierarchy, logging, result-pattern, try-except
- **컨텍스트 매니저**: contextlib, custom, with
- **타입 힌트**: function-annotations, generic-typevar, protocol, variable-annotations
- **Pythonic 패턴**: comprehensions, generators, unpacking, walrus
- **안티패턴**: bare-except, is-comparison, mutable-defaults

### React

- **비동기**: defer-await, dependencies, parallel, promise-all, suspense-boundaries
- **번들 최적화**: barrel-imports, conditional, defer-third-party, dynamic-imports, preload
- **컴포넌트**: composition, conditional-render, discriminated-unions, typescript
- **이펙트**: cleanup, custom-hooks, dependencies, race-condition
- **리렌더링 최적화**: avoid-inline-objects, functional-setstate, lazy-init, memo, transitions, usecallback, usememo
- **서버 컴포넌트**: after-nonblocking, auth-actions, cache-react, parallel-fetching, serialization, streaming, unstable-cache
- **상태 관리**: context, derived, local, reducer
- **JS 최적화**: early-exit, index-maps, passive-events, property-access, set-lookups, tosorted

### Rust

- **에러 처리**: option, question-mark, result, thiserror
- **패턴 매칭**: destructuring, expressions, guards, if-let
- **메모리 안전**: no-data-races, no-null, safe-abstractions, unsafe-isolation
- **소유권**: borrowing, clone-copy, lifetimes, transfer
- **안티패턴**: string-concat-loop, unnecessary-clone, unwrap-production

### TypeScript

- **에러 처리**: class-hierarchies, custom-types, result-pattern, try-catch
- **비동기**: all-settled, avoid-callbacks, batch-processing, error-handling, retry-pattern
- **타입 시스템**: avoid-any, const-assertions, generic-constraints, intersection, keyof-typeof, type-guards, union-narrowing
- **코드 구조**: barrel-exports, interface-vs-type, path-aliases, strict-mode
- **Next.js**: api-route-typing
- **검증**: zod-schema
- **안티패턴**: empty-interfaces, ignore-errors, type-assertion

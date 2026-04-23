# restore-context Skill Module Index

## Overview

This skill is modularized for maintainability. Each module handles a specific responsibility.

## Module Structure

### Components (Building Blocks)
| Module | Purpose |
|--------|---------|
| `components/checkpoint-reader.md` | JSON 파일 읽기 및 파싱 |
| `components/checkpoint-validator.md` | 스키마 검증 (v1/v3/v4) |
| `components/relative-time.md` | 시간 포맷팅 (방금 전, N분 전) |
| `components/worktree-verifier.md` | Git worktree 존재 확인 |

### Processes (Version-Specific Flows)
| Module | Purpose |
|--------|---------|
| `processes/restore-v1.md` | v1.0 레거시 포맷 복원 |
| `processes/restore-v3.md` | v3.0 단일 체크포인트 복원 |
| `processes/restore-v4.md` | v4.0 FIFO 배열 복원 |

### Rules (Features & Patterns)
| Module | Purpose |
|--------|---------|
| `rules/feature-interactive-selection.md` | AskUserQuestion 대화형 선택 |
| `rules/feature-cleanup-after-restore.md` | 복원 후 체크포인트 정리 |
| `rules/pattern-error-messages.md` | 11개 표준화된 에러 메시지 |
| `rules/pattern-planner-invocation.md` | Planner Task 호출 패턴 |

### Orchestration
| Module | Purpose |
|--------|---------|
| `orchestration/restoration-flow.md` | 메인 결정 트리 및 흐름 제어 |

## Loading Order

1. `orchestration/restoration-flow.md` - Entry point
2. `components/checkpoint-reader.md` - Read checkpoint file
3. `components/checkpoint-validator.md` - Validate schema
4. `rules/feature-interactive-selection.md` - User selection
5. `components/worktree-verifier.md` - Verify worktree (if used)
6. `processes/restore-v{1,3,4}.md` - Version-specific restoration
7. `rules/pattern-planner-invocation.md` - Invoke planner
8. `rules/feature-cleanup-after-restore.md` - Cleanup checkpoint

## Error Handling

All error messages are centralized in `rules/pattern-error-messages.md`.

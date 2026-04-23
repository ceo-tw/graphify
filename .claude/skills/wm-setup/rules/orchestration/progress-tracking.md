---
title: Progress Tracking
impact: MEDIUM
impactDescription: Track wm-setup workflow progress
tags: [orchestration]
used_by: [wm-setup]
---

# Progress Tracking

**Impact: MEDIUM** - Track and display wm-setup workflow progress

## Overview

This component provides progress tracking and status display during the
wm-setup workflow execution.

## Progress Structure

```typescript
interface QuickstartProgress {
  mode: "NEW_SETUP" | "UPDATE" | "VERIFY";
  currentStep: number;
  totalSteps: number;
  steps: StepStatus[];
  startTime: string;
  estimatedCompletion: string;
}

interface StepStatus {
  number: number;
  name: string;
  status: "pending" | "in_progress" | "completed" | "skipped";
  duration?: number;  // milliseconds
}
```

## Step Definitions

```python
WM-SETUP_STEPS = [
    {"number": 0, "name": "Context Gate Check", "required": True},
    {"number": 1, "name": "Unified Analysis", "required": True},
    {"number": 1.5, "name": "Shell Environment Check", "required": True},
    {"number": 2, "name": "MCP Management", "required": True},
    {"number": 3, "name": "Checklist Generation", "required": True},
    {"number": 4, "name": "Validation", "required": True},
    {"number": 4.5, "name": "Mismatch Resolution", "required": False},  # Conditional
    {"number": 5, "name": "Report Generation", "required": True}
]
```

## Progress Display

```python
def formatProgress(progress: dict) -> str:
    """Format progress for display."""
    lines = [
        f"### wm-setup Progress ({progress['mode']})",
        "",
        f"Step {progress['currentStep']}/{progress['totalSteps']}",
        ""
    ]

    for step in progress["steps"]:
        icon = getStatusIcon(step["status"])
        lines.append(f"{icon} Step {step['number']}: {step['name']}")

    return "\n".join(lines)

def getStatusIcon(status: str) -> str:
    """Get status icon."""
    icons = {
        "pending": "[ ]",
        "in_progress": "[>]",
        "completed": "[x]",
        "skipped": "[-]"
    }
    return icons.get(status, "[ ]")
```

## Progress Updates

```python
def updateProgress(progress: dict, step_number: float, status: str) -> dict:
    """Update step status."""
    for step in progress["steps"]:
        if step["number"] == step_number:
            step["status"] = status
            if status == "completed":
                step["duration"] = calculateDuration(step)
            break

    if status == "completed":
        progress["currentStep"] = getNextStep(progress, step_number)

    return progress
```

## Mode-Specific Steps

### NEW_SETUP (All steps)

```
[x] Step 0: Context Gate Check
[x] Step 1: Unified Analysis
[x] Step 1.5: Shell Environment Check
[x] Step 2: MCP Management
[x] Step 3: Checklist Generation
[x] Step 4: Validation
[-] Step 4.5: Mismatch Resolution (skipped - no mismatch)
[x] Step 5: Report Generation
```

### UPDATE (Selective steps)

```
[x] Step 0: Context Gate Check
[x] Step 1: Unified Analysis
[x] Step 1.5: Shell Environment Check
[x] Step 2: MCP Management (selective)
[x] Step 3: Checklist Generation (partial)
[x] Step 4: Validation
[x] Step 4.5: Mismatch Resolution
[x] Step 5: Report Generation
```

### VERIFY (Validation focus)

```
[x] Step 0: Context Gate Check
[x] Step 1: Unified Analysis (read-only)
[x] Step 1.5: Shell Environment Check
[-] Step 2: MCP Management (skipped)
[-] Step 3: Checklist Generation (skipped)
[x] Step 4: Validation (main focus)
[-] Step 4.5: Mismatch Resolution (if needed)
[x] Step 5: Report Generation
```

## Completion Summary

```python
def generateCompletionSummary(progress: dict) -> dict:
    """Generate completion summary."""
    completed = sum(1 for s in progress["steps"] if s["status"] == "completed")
    skipped = sum(1 for s in progress["steps"] if s["status"] == "skipped")
    total = len(progress["steps"])

    return {
        "completed": completed,
        "skipped": skipped,
        "total": total,
        "duration": calculateTotalDuration(progress),
        "success": completed + skipped == total
    }
```

## When to Apply

- Throughout wm-setup workflow execution
- For progress display to user
- For completion tracking

## References

- [workflow-orchestration.md](./workflow-orchestration.md) - Main orchestrator

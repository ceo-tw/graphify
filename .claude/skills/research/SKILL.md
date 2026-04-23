---
name: research
type: capability
description: "심층 리서치를 수행합니다. 주제에 대해 5-10회 검색 후 핵심 요약을 제공합니다. 사용 시점: (1) 새로운 기술 도입 전 조사가 필요할 때, (2) 기술 비교 분석이 필요할 때, (3) 베스트 프랙티스를 파악할 때. /research 커맨드로 호출."
argument-hint: [리서치 주제]
context: fork
agent: general-purpose
allowed-tools:
  - mcp__tavily__tavily_search
  - mcp__tavily__tavily_extract
  - Read
  - Write
  - Bash
  - AskUserQuestion
  - TaskCreate
  - TaskGet
  - TaskUpdate
  - TaskList
  - WebSearch
  - WebFetch
user-invocable: true
---

# research

PRD 작성 없이 독립적으로 기술 조사를 수행하는 스킬입니다.

## Usage

```
/research <topic>
/research <topic> --quick             # 빠른 조사 (3회 검색)
/research <topic> --deep              # 심층 조사 (8-10회 검색)
/research <topic> --report            # 기본 검색 + 장문 리포트 (2k-8k 단어)
/research <topic> --deep --report     # 심층 검색 + 장문 리포트 (최대 상세)
```

**Examples:**
```
/research OAuth 2.0
/research "React Server Components" --deep
/research JWT vs Session --quick
/research 클린 아키텍처 적용 방법
/research "Kafka vs NATS" --report
/research "Next.js App Router 성능 최적화" --deep --report
```

### Flag 조합 동작

| 명령 | 검색 횟수 | 출력 형식 | 저장 경로 |
|------|-----------|-----------|-----------|
| `/research <topic>` | 5-7회 | bullet 요약 | `.claude/plans/research/YYYYMMDD-<slug>.md` |
| `/research <topic> --deep` | 8-10회 | bullet 요약 | `.claude/plans/research/YYYYMMDD-<slug>.md` |
| `/research <topic> --report` | 5-7회 | 장문 리포트 (2k-8k 단어) | `.claude/plans/research/reports/YYYYMMDD-<slug>-report.md` |
| `/research <topic> --deep --report` | 8-10회 | 장문 리포트 (2k-8k 단어, 최대 상세) | `.claude/plans/research/reports/YYYYMMDD-<slug>-report.md` |

> `--deep`과 `--report`는 직교(orthogonal) flag입니다. `--deep`은 검색 횟수만 결정하고, `--report`는 출력 형식과 저장 경로만 결정합니다. 두 flag는 독립적으로 조합 가능합니다.

> **Warning**: `--deep --report` 조합은 Tavily 토큰 최대 소비 (약 8-10회 검색 + 장문 합성). 월 1회 이상 반복 호출 전 비용 확인 권장.

> **Reference**: [doc-quality-principles.md](.claude/skills/wm/rules/policies/doc-quality-principles.md) — 장문 리포트 품질 기준 적용

---

## Workflow

```
/research <topic>
    │
    ├─► Step 1: 주제 분석
    │   └─ 핵심 키워드 추출
    │
    ├─► Step 2: 다각도 검색 (5-10회)
    │   ├─ 개념/정의
    │   ├─ 장단점
    │   ├─ 사용 사례
    │   ├─ 베스트 프랙티스
    │   ├─ 주의사항
    │   └─ 대안/비교
    │
    ├─► Step 3: 정보 통합
    │   └─ 신뢰도 검증, 중복 제거
    │
    ├─► Step 4: 요약 리포트 생성
    │   └─ 저장: .claude/plans/research/YYYYMMDD-<slug>.md
    │
    └─► Step 5: 사용자 의사결정
        ├─ 유지 → 리포트 보존
        └─ 삭제 → 파일 삭제
```

---

> **Reference**: See [Output Format & User Decision](references/output-format.md) for report template and user decision logic.

---

## Implementation

### Task Tool Integration

> **Reference**: [Task Tool Planning Guide](../wm/rules/components/task-tool-planning-guide.md)

This skill uses Task tools for progress tracking throughout the research workflow:

1. **Workflow Start**: Create task with `TaskCreate` at the beginning of research
2. **Step Progress**: Update task status with `TaskUpdate` as each step completes
3. **Status Tracking**: Track analysis → search → integration → report generation

See the Task Tool Planning Guide for:
- Staleness Prevention patterns
- Metadata schema for research tasks
- Progress tracking best practices

### Step 1: 주제 분석

```python
# Create task for research workflow
task = TaskCreate(
    name=f"Research: {topic}",
    description=f"Deep research on '{topic}' with multi-angle search",
    metadata={
        "topic": topic,
        "mode": mode,  # quick/normal/deep
        "step": "analyze"
    }
)

def analyze_topic(topic):
    """
    주제에서 핵심 키워드와 검색 쿼리 생성

    NOTE: 최신 정보가 필요한 쿼리에는 현재 연도 포함
    시스템 프롬프트의 "Today's date"에서 연도 확인
    예: Today's date: 2026-01-26 → current_year = 2026
    """
    keywords = extract_keywords(topic)
    # 시스템 프롬프트의 Today's date에서 연도 추출
    # current_year = 2026  # Today's date: 2026-01-26 기준

    queries = [
        f"{topic} 개념 정의",
        f"{topic} 장단점",
        f"{topic} 사용 사례 예시",
        f"{topic} best practices {current_year}",  # 연도 포함 (최신 정보)
        f"{topic} 주의사항 실수",
        f"{topic} 대안 비교 {current_year}"  # 연도 포함 (최신 비교)
    ]

    # Update task progress
    TaskUpdate(
        taskId=task.taskId,
        status="in_progress",
        metadata={**task.metadata, "step": "search", "queries": len(queries)}
    )

    return {
        "topic": topic,
        "keywords": keywords,
        "queries": queries
    }
```

### Step 2: 다각도 검색

```python
def search_multi_angle(queries, mode="normal"):
    """
    다각도 검색 수행

    mode:
    - quick: 3회 검색
    - normal: 5-7회 검색
    - deep: 10회 검색
    """
    search_count = {
        "quick": 3,
        "normal": 6,
        "deep": 10
    }[mode]

    results = []

    for query in queries[:search_count]:
        # Tavily MCP 사용
        result = mcp__tavily__tavily_search(
            query=query,
            search_depth="advanced" if mode == "deep" else "basic",
            max_results=5
        )
        results.append({
            "query": query,
            "results": result
        })

    # Update task progress
    TaskUpdate(
        taskId=task.taskId,
        metadata={**task.metadata, "step": "integrate", "searches_completed": len(results)}
    )

    return results
```

### Step 3: 정보 통합

```python
def integrate_results(search_results):
    """
    검색 결과 통합 및 중복 제거
    """
    integrated = {
        "overview": [],
        "features": [],
        "pros": [],
        "cons": [],
        "use_cases": [],
        "best_practices": [],
        "warnings": [],
        "alternatives": [],
        "references": []
    }

    for result in search_results:
        # 카테고리별 분류
        categorize_and_dedupe(result, integrated)

    # Update task progress
    TaskUpdate(
        taskId=task.taskId,
        metadata={**task.metadata, "step": "report"}
    )

    return integrated
```

### Step 4: 리포트 생성

`has_report_flag` 여부에 따라 출력 형식과 저장 경로가 분기됩니다.
`has_deep_flag`는 Step 2의 검색 횟수만 결정하며 Step 4 출력 형식에는 영향을 주지 않습니다.

```python
def generate_report(topic, integrated, has_report_flag=False, has_deep_flag=False):
    """
    리서치 리포트 생성

    분기:
    - has_report_flag=False: bullet 요약 템플릿 → .claude/plans/research/YYYYMMDD-<slug>.md
    - has_report_flag=True:  장문 리포트 템플릿 → .claude/plans/research/reports/YYYYMMDD-<slug>-report.md

    has_deep_flag는 이 함수에 영향을 주지 않음 (Step 2에서 검색 횟수 결정에만 사용됨)
    """
    slug = slugify(topic)
    timestamp = datetime.now().isoformat()
    date_prefix = datetime.now().strftime("%Y%m%d")  # e.g. 20260207

    if has_report_flag:
        # 장문 리포트 템플릿 적용
        # - 인라인 [n] 인용 마커 사용
        # - narrative prose 섹션 (각 300-800 단어)
        # - 2개 이상 대안 비교 시 테이블 필수
        # - 참조: references/output-format.md §장문 리포트 템플릿
        report = generate_long_form_report(topic, integrated, timestamp)
        output_path = f".claude/plans/research/reports/{date_prefix}-{slug}-report.md"
    else:
        # 기본 bullet 요약 템플릿
        report = f"""
# 리서치: {topic}

> **조사일**: {timestamp}
> **키워드**: {', '.join(integrated['keywords'])}

## 1. 핵심 개요

{format_overview(integrated['overview'])}

## 2. 주요 특징

{format_features(integrated['features'])}

## 3. 장점 vs 단점

### 장점
{format_list(integrated['pros'])}

### 단점
{format_list(integrated['cons'])}

## 4. 사용 사례

{format_numbered_list(integrated['use_cases'])}

## 5. 베스트 프랙티스

{format_checklist(integrated['best_practices'])}

## 6. 주의사항

{format_warnings(integrated['warnings'])}

## 7. 대안 비교

{format_comparison_table(integrated['alternatives'])}

## 8. 참고 자료

{format_references(integrated['references'])}
"""
        output_path = f".claude/plans/research/{date_prefix}-{slug}.md"

    # 파일 저장
    Write(
        file_path=output_path,
        content=report
    )

    # Update task progress (report saved, pending user decision)
    TaskUpdate(
        taskId=task.taskId,
        metadata={
            **task.metadata,
            "step": "user_decision",
            "output_file": output_path,
            "report_mode": "long_form" if has_report_flag else "summary"
        }
    )

    return report, output_path
```

---

## Options

```
  옵션              설명                           검색 횟수  출력 형식
  ────────────────  ─────────────────────────────  ─────────  ──────────────────────────
  (기본)            일반 조사                      5-7회      bullet 요약
  --quick           빠른 조사                      3회        bullet 요약
  --deep            심층 조사                      8-10회     bullet 요약
  --report          기본 검색 + 장문 리포트        5-7회      장문 (2k-8k 단어)
  --deep --report   심층 검색 + 장문 리포트        8-10회     장문 (2k-8k 단어, 최대 상세)
  ────────────────  ─────────────────────────────  ─────────  ──────────────────────────
```

> `--deep`과 `--report`는 직교(orthogonal) flag입니다. 두 flag는 독립적으로 동작하며 자유롭게 조합할 수 있습니다.

---

## Tools Used

```
  도구                          용도
  ────────────────────────────  ──────────────────────
  mcp__tavily__tavily_search    웹 검색
  mcp__tavily__tavily_extract   페이지 내용 추출
  Write                         리포트 저장
  Bash                          파일 삭제 (사용자 요청 시)
  AskUserQuestion               리포트 유지/삭제 의사결정
  TaskCreate/Update/Get         진행 상태 표시
  ────────────────────────────  ──────────────────────
```

---

## Output Location

리서치 결과는 다음 위치에 저장됩니다:

```
.claude/plans/research/
├── 20260207-oauth-2-0.md
├── 20260205-react-server-components.md
├── 20260203-clean-architecture.md
└── ...
```

---

## Related Skills

```
  Skill        Purpose           When to Use
  ───────────  ────────────────  ─────────────────────
  /research    독립 기술 조사    개발 전 기술 검토
  /planner     개발 시작         조사 후 실제 구현 시
  /dev-status  진행 상황 확인    현재 작업 상태 파악
  ───────────  ────────────────  ─────────────────────
```

---

## Integration with /planner

리서치 결과를 `/planner`에서 활용할 수 있습니다:

```
1. /research OAuth 2.0           # 먼저 기술 조사
2. /planner 사용자 인증 시스템    # 조사 결과 참조하여 개발
```

---

## Error Handling

```
  상황                대응
  ──────────────────  ─────────────────────────────
  검색 API 실패       재시도 후 부분 결과 반환
  주제가 너무 광범위  세부 주제 제안
  검색 결과 부족      관련 키워드 추천
  ──────────────────  ─────────────────────────────
```

---

## Notes

- 검색 결과는 최신 정보를 반영하지만, 공식 문서 확인을 권장합니다
- `--deep` 옵션은 시간이 더 소요됩니다
- 저장된 리포트는 나중에 참조 가능합니다

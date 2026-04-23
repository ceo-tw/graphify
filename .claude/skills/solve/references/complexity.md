# BUG_FIX 복잡도 판단 기준

## 분석 출력 형식

Phase 2 완료 후 다음 형식으로 복잡도 분석 결과를 출력합니다:

```markdown
## 📊 복잡도 분석 결과

| 항목 | 분석 값 | 기준 |
|------|---------|------|
| 영향 파일 수 | {count}개 | ≤1: Simple |
| 예상 변경 줄 | ~{lines}줄 | ≤10: Simple |
| 새 테스트 필요 | {Yes/No} | No: Simple |
| 레이어 간 수정 | {Yes/No} | No: Simple |
| 재현 난이도 | {낮음/중간/높음} | 낮음: Simple |
| 원인 명확성 | {명확/불명확} | 명확: Simple |
| 프로덕션 영향 | {Yes/No} | - |
| 보안/데이터 관련 | {Yes/No} | - |

**분석 결과**: {Simple/Complex/Unclear}
**권장 접근**: {권장 옵션명}
```

---

## 동적 권장 로직

### 권장 옵션 결정 순서 (우선순위)

| 우선순위 | 조건 | 권장 옵션 | 이유 |
|----------|------|----------|------|
| 1 | 원인 불명확 OR 재현 어려움 OR 에러 메시지 모호 | **Analysis Only** | 섣부른 수정보다 정확한 분석 우선 |
| 2 | 프로덕션 영향 OR 데이터 무결성 관련 OR 보안 관련 | **Full Pipeline** | 놓침 없이 철저히 검증 |
| 3 | 2+파일 OR >10줄 OR 새 테스트 필요 OR 레이어 간 수정 | **Standard** | TDD로 안전하게 수정 |
| 4 | 단일 파일 + ≤10줄 + 테스트 커버리지 낮음 | **Quick Fix + QA** | 빠른 수정 + 검증 |
| 5 | 단일 파일 + ≤10줄 + 원인 확실 + 테스트 충분 | **Quick Fix** | 가장 간단한 경우만 |

### 권장 결정 흐름도

```
[문제 분석]
    │
    ├─ 원인 불명확? ────────────────────── → Analysis Only (권장)
    │
    ├─ 프로덕션/보안/데이터 영향? ──────── → Full Pipeline (권장)
    │
    ├─ 복잡도 높음? (2+파일, >10줄...) ── → Standard (권장)
    │
    ├─ 단순하지만 테스트 부족? ─────────── → Quick Fix + QA (권장)
    │
    └─ 모두 단순 조건 충족? ────────────── → Quick Fix (권장)
```

**원칙**: 확신이 없으면 더 철저한 옵션을 권장

---

## 5가지 접근 방식 옵션

| # | 옵션 | 호출 에이전트 | 용도 | 철저함 |
|---|------|---------------|------|--------|
| 1 | **Quick Fix** | - (직접 Edit) | 명확한 단순 버그, 원인이 확실함 | ⭐ |
| 2 | **Quick Fix + QA** | qa | 단순 버그 + 품질 검증 필요 | ⭐⭐ |
| 3 | **Standard** | root-cause-finder → bug-fixer | 복잡 버그, TDD 필요 | ⭐⭐⭐ |
| 4 | **Full Pipeline** | root-cause-finder → bug-fixer → qa | 가장 어려운 문제, 놓침 없이 철저히 | ⭐⭐⭐⭐ |
| 5 | **Analysis Only** | root-cause-finder | 문제 재파악 후 다음 단계 결정 | 🔍 |

---

## Simple 조건 (Quick Fix 적용 가능)

다음 조건을 **모두** 만족하면 Simple:

| 기준 | 조건 |
|------|------|
| 영향 범위 | 단일 파일 수정 |
| 수정 규모 | 10줄 이하 변경 |
| 테스트 영향 | 기존 테스트 통과 |
| 의존성 | 새 의존성 추가 없음 |
| 재현성 | 즉시 재현 가능 |
| 원인 | 명확함 |

## Complex 조건 (Standard 이상 필요)

다음 조건 중 **하나라도** 해당하면 Complex:

| 기준 | 조건 |
|------|------|
| 영향 범위 | 2개 이상 파일 수정 |
| 수정 규모 | 10줄 초과 변경 |
| 테스트 영향 | 새 테스트 필요 |
| 의존성 | 새 의존성 추가 |
| 재현성 | 재현 조건 복잡 |
| 아키텍처 | 레이어 간 수정 필요 |

## Unclear 조건 (Analysis Only 권장)

다음 조건 중 **하나라도** 해당하면 Unclear:

| 기준 | 조건 |
|------|------|
| 원인 | 불명확함 |
| 에러 메시지 | 모호하거나 없음 |
| 재현 | 재현 불가 또는 간헐적 |
| 영향 범위 | 파악 어려움 |

---

## 권장 결정 코드

```python
def determine_recommendation(analysis):
    """복잡도 분석 결과를 바탕으로 권장 옵션 결정"""

    # 우선순위 1: 불명확한 경우
    if (not analysis.cause_clear or
        analysis.reproduction_difficulty == "높음" or
        analysis.error_message_vague):
        return "analysis_only"

    # 우선순위 2: 프로덕션/보안/데이터 영향
    if (analysis.production_impact or
        analysis.security_related or
        analysis.data_integrity_related):
        return "full_pipeline"

    # 우선순위 3: Complex 조건
    if (analysis.affected_files >= 2 or
        analysis.estimated_changes > 10 or
        analysis.needs_new_tests or
        analysis.crosses_layers):
        return "standard"

    # 우선순위 4: Simple + 테스트 부족
    if analysis.test_coverage_low:
        return "quick_fix_qa"

    # 우선순위 5: 가장 간단한 경우
    return "quick_fix"
```

---

## 경계 사례 (Edge Cases)

### Simple로 시작했으나 Complex로 전환

```
상황: 1파일 수정 예상 → 실제로 3파일 수정 필요

대응:
1. 현재 변경 롤백
2. bug-fixer 호출로 전환
3. TDD 워크플로 적용
```

### Complex지만 시간 제약 있음

```
상황: Complex 조건이지만 긴급 수정 필요

대응:
1. 사용자에게 상황 설명
2. Quick Fix 선택 시 진행
3. TODO 주석 추가: "// TODO: TDD 리팩토링 필요"
4. 이슈 트래커에 기술 부채 등록
```

### Analysis Only 후 방향 전환

```
상황: 분석 결과 예상보다 단순함

대응:
1. 2차 의사결정에서 Quick Fix 선택 가능
2. 분석 결과를 바탕으로 새 권장 옵션 제시
```

---

## solve skill 연동

```python
# solve/SKILL.md의 Phase 2.5에서 사용

def run_complexity_analysis(gathered_info):
    """수집된 정보를 바탕으로 복잡도 분석 실행"""

    analysis = {
        "affected_files": count_affected_files(gathered_info),
        "estimated_changes": estimate_change_lines(gathered_info),
        "needs_new_tests": check_test_needs(gathered_info),
        "crosses_layers": check_layer_crossing(gathered_info),
        "reproduction_difficulty": assess_reproduction(gathered_info),
        "cause_clear": assess_cause_clarity(gathered_info),
        "production_impact": check_production_impact(gathered_info),
        "security_related": check_security_related(gathered_info),
        "data_integrity_related": check_data_integrity(gathered_info),
        "test_coverage_low": check_test_coverage(gathered_info)
    }

    recommendation = determine_recommendation(analysis)
    return analysis, recommendation
```

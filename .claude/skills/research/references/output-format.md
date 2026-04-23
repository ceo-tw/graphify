# Output Format & User Decision

## Output Format

```
============================================
리서치 결과: OAuth 2.0
============================================

## 1. 핵심 개요

OAuth 2.0은 제3자 애플리케이션에 리소스 접근 권한을
위임하기 위한 인증 프레임워크입니다.

## 2. 주요 특징

```
  특징        설명
  ──────────  ────────────────────────────────────
  토큰 기반   Access Token으로 권한 부여
  범위 제한   Scope로 접근 범위 제한
  갱신 가능   Refresh Token으로 재발급
  ──────────  ────────────────────────────────────
```

## 3. 장점 vs 단점

### 장점
- 비밀번호 노출 없이 권한 위임
- 세분화된 접근 제어 가능
- 산업 표준으로 광범위한 지원

### 단점
- 구현 복잡성
- 토큰 관리 오버헤드
- 보안 취약점 주의 필요

## 4. 사용 사례

1. **소셜 로그인**: Google, Facebook 로그인
2. **API 접근**: 서드파티 앱의 API 사용
3. **마이크로서비스**: 서비스 간 인증

## 5. 베스트 프랙티스

- [ ] PKCE 사용 (SPA, 모바일 앱)
- [ ] State 파라미터로 CSRF 방지
- [ ] 짧은 Access Token 유효기간
- [ ] Refresh Token 안전한 저장

## 6. 주의사항

- Token 평문 저장 금지
- Redirect URI 화이트리스트 필수
- Scope 최소 권한 원칙

## 7. 대안 비교

```
  방식    OAuth 2.0  JWT    Session
  ──────  ─────────  ─────  ───────
  확장성  높음       높음   낮음
  복잡성  높음       중간   낮음
  보안    높음       중간   중간
  ──────  ─────────  ─────  ───────
```

## 8. 참고 자료

- [RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OAuth 2.0 Playground](https://oauth.net/playground/)

============================================
저장됨: .claude/plans/research/20260207-oauth-2-0.md
============================================
```

---

## Step 5: 사용자 의사결정 (리포트 처리)

```python
def ask_user_report_decision(output_path, report):
    """
    리포트 저장 후 사용자에게 처리 방법 의사결정을 받음
    """
    # 1단계: 메인 의사결정
    answer = AskUserQuestion(
        questions=[{
            "question": "리서치 리포트를 어떻게 처리하시겠습니까?",
            "header": "Report",
            "options": [
                {
                    "label": "파일 저장",
                    "description": f"리포트를 {output_path}에 보존합니다"
                },
                {
                    "label": "저장하지 않음",
                    "description": "리포트 파일을 삭제합니다."
                },
                {
                    "label": "추가 조사",
                    "description": "연관 주제를 추가로 조사합니다"
                }
            ],
            "multiSelect": False
        }]
    )

    if answer == "저장하지 않음":
        # 파일 삭제
        Bash(command=f"rm '{output_path}'")

        TaskUpdate(
            taskId=task.taskId,
            status="completed",
            metadata={
                **task.metadata,
                "step": "done",
                "report_kept": False
            }
        )
        return "deleted"

    elif answer == "추가 조사":
        # 2단계: 리포트 내용 기반으로 후속 조사 옵션을 동적 생성
        # - 완료된 리포트에서 경쟁 도구, 미해결 질문, 관련 기술 등을 분석
        # - 해당 주제에 가장 유용한 후속 조사 방향 2-3개를 옵션으로 제시
        # 예: "Greptile" 리서치 → "CodeRabbit/Sourcery 비교", "도입 비용 분석" 등
        follow_up_options = generate_contextual_options(report)  # 에이전트가 판단하여 2-3개 생성

        follow_up = AskUserQuestion(
            questions=[{
                "question": "어떤 내용을 추가로 조사할까요?",
                "header": "추가 조사",
                "options": follow_up_options,
                "multiSelect": False
            }]
        )

        # follow_up 내용으로 추가 리서치 수행 후 리포트 업데이트
        additional_research = perform_research(follow_up)
        updated_report = append_to_report(output_path, additional_research)

        TaskUpdate(
            taskId=task.taskId,
            status="completed",
            metadata={
                **task.metadata,
                "step": "done",
                "report_kept": True,
                "output_file": output_path,
                "follow_up_topic": follow_up
            }
        )
        return "extended"

    elif answer not in ["파일 저장", "저장하지 않음", "추가 조사"]:
        # "Other" 자유 입력 처리 -- 사용자가 직접 입력한 요청을 처리
        custom_request = answer
        additional_research = perform_research(custom_request)
        updated_report = append_to_report(output_path, additional_research)

        TaskUpdate(
            taskId=task.taskId,
            status="completed",
            metadata={
                **task.metadata,
                "step": "done",
                "report_kept": True,
                "output_file": output_path,
                "custom_request": custom_request
            }
        )
        return "custom"

    else:
        # "파일 저장" (기본)
        TaskUpdate(
            taskId=task.taskId,
            status="completed",
            metadata={
                **task.metadata,
                "step": "done",
                "report_kept": True,
                "output_file": output_path
            }
        )
        return "kept"
```

---

## 장문 리포트 템플릿 (--report 모드)

`--report` flag가 지정된 경우, bullet 요약 대신 아래 구조의 장문 리포트를 생성합니다.

저장 경로: `.claude/plans/research/reports/YYYYMMDD-<slug>-report.md`

### 구조

- **Title**: 조사 주제를 명확히 표현하는 제목
- **요약 단락** (300-500 단어, narrative prose): 핵심 발견 사항과 결론을 서술체로 작성. 독자가 보고서 전체를 읽지 않아도 핵심을 파악할 수 있어야 함.
- **최소 5개 `##` 섹션**:
  - 각 섹션당 300-800 단어 narrative prose
  - 2개 이상 대안을 비교할 경우 테이블 필수 (trade-off 명시)
  - 단순 bullet list만으로 섹션을 채우는 것은 금지
- **Conclusion 단락**: 조사 결과를 바탕으로 한 권장 사항과 다음 단계 제시

### 인용 규격

- 주장이나 데이터 제시 직후 인라인 `[n]` 마커를 붙임
- 문서 하단 reference table: `번호 | URL / 파일경로:라인 / 커밋 SHA | 설명` 형식
- 검색 결과에서 직접 인용한 내용은 반드시 해당 URL 인용

### 예시 섹션 구조

```markdown
# 리서치 리포트: {topic}

> **조사일**: {timestamp}
> **검색 횟수**: {n}회 | **모드**: --deep --report / --report

## 요약

{300-500 단어 narrative prose. 핵심 발견과 권장 사항.}

## 1. 개요 및 배경

{배경, 정의, 역사적 맥락. 300-800 단어.}

## 2. 핵심 특징 및 아키텍처

{기술 상세, 작동 원리. 300-800 단어.}

## 3. 대안 비교

{2개 이상 대안 비교 시 테이블 필수}

| 방식 | 장점 | 단점 | 적합한 사용 사례 |
|------|------|------|-----------------|
| ...  | ...  | ...  | ...             |

{테이블 이후 narrative 보완 설명}

## 4. 실전 적용 패턴

{베스트 프랙티스, 주의사항. 300-800 단어.}

## 5. 생태계 및 커뮤니티

{라이브러리, 툴링, 지원 현황. 300-800 단어.}

## Conclusion

{권장 사항과 다음 단계. 200-400 단어.}

## References

| # | 출처 | 설명 |
|---|------|------|
| 1 | https://... | ... |
| 2 | path/to/file:42 | ... |
```

### 예시 참고

`.claude/skills/wm/rules/policies/doc-quality-principles.md` §1 원칙 1 (evidence-first), 원칙 2 (narrative prose), 원칙 3 (table-first for comparisons) 참조

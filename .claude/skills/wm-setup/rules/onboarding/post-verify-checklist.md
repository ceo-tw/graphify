---
title: VERIFY 후 체크리스트 - 사용자 가이드
impact: MEDIUM
impactDescription: 런타임 검증을 위한 수동 테스트 가이드
tags: [checklist, verification, manual-testing]
used_by: [runtime-validator, verify.md]
---

# VERIFY 후 체크리스트 - 사용자 가이드

**영향도: 중간** - 런타임 검증을 위한 단계별 수동 테스트 가이드

## 개요

이 체크리스트는 자동화된 검증 완료 후 Claude Code 런타임 환경을 확인하기 위한
수동 테스트 절차를 제공합니다. runtime-validator가 실패 또는 경고를 보고할 때
사용하세요.

**생성 주체**: `runtime-validator.md` (모듈 7, VERIFY 모드)

## 체크리스트 사용 방법

1. VERIFY 모드로 `/wm-setup` 실행
2. 런타임 검증 결과 확인 (모듈 7/7)
3. 각 경고 또는 실패 항목에 대해 아래 테스트 절차 수행
4. 각 항목 완료 후 체크박스 선택
5. 수정 확인을 위해 `/wm-setup` 다시 실행

## 카테고리 1: MCP 연결

### RTC-MCP-001: Serena MCP 연결

**테스트**: Serena MCP 서버가 연결되어 응답하는지 확인

```bash
# Serena 도구 사용 가능 여부 확인
# Claude Code에서 ToolSearch를 사용하여 사용 가능한 MCP 도구 목록 확인
# 기대값: mcp__plugin_serena_serena__* 도구가 표시됨
```

**기대 결과**: Serena MCP 도구가 사용 가능하고 응답함

**수동 테스트**:
1. Claude Code에서 질문: "사용 가능한 Serena MCP 도구 목록"
2. 응답에 다음 항목 포함 확인:
   - `mcp__plugin_serena_serena__find_symbol`
   - `mcp__plugin_serena_serena__get_symbols_overview`
   - `mcp__plugin_serena_serena__replace_symbol_body`

**문제 해결**:
- 도구를 찾을 수 없는 경우: Claude Code 설정에서 Serena MCP 서버 활성화
- 활성화 후 Claude Code 재시작
- MCP 서버 로그에서 오류 확인

---

### RTC-MCP-002: Memory MCP 연결

**테스트**: Memory MCP 서버가 연결되어 있는지 확인 (선택사항)

```bash
# Memory 도구 사용 가능 여부 확인
# 기대값: mcp__memory__* 도구가 표시됨
```

**수동 테스트**:
1. 질문: "사용 가능한 Memory MCP 도구 목록"
2. 응답에 다음 항목 포함 확인:
   - `mcp__memory__create_entities`
   - `mcp__memory__read_graph`

**문제 해결**:
- 필요하지 않은 경우: 건너뛰기 (선택적 서버)
- 필요한 경우: Memory MCP 서버 설치 및 구성
- 참조: https://github.com/modelcontextprotocol/servers

---

### RTC-MCP-003: Playwright MCP 연결

**테스트**: Playwright MCP 서버가 연결되어 있는지 확인 (선택사항)

```bash
# Playwright 도구 사용 가능 여부 확인
# 기대값: mcp__playwright__* 도구가 표시됨
```

**수동 테스트**:
1. 질문: "사용 가능한 Playwright MCP 도구 목록"
2. 응답에 다음 항목 포함 확인:
   - `mcp__playwright__screenshot`
   - `mcp__playwright__navigate`

**문제 해결**:
- E2E 테스트에만 필요
- 설치: `npx @modelcontextprotocol/create-server playwright`

---

## 카테고리 2: 환경 변수

### RTC-ENV-001: MAX_THINKING_TOKENS

**테스트**: MAX_THINKING_TOKENS가 권장값으로 설정되어 있는지 확인

```bash
# 현재값 확인
echo $MAX_THINKING_TOKENS

# 기대값: 31999
```

**권장값**: `31999`

**이유**: 복잡한 작업과 깊은 추론을 위한 확장된 사고 용량

**조치**:
```bash
# 쉘 프로파일(.zshrc, .bashrc 등)에 추가
export MAX_THINKING_TOKENS=31999

# 쉘 다시 로드
source ~/.zshrc  # 또는 source ~/.bashrc
```

**확인**:
```bash
echo $MAX_THINKING_TOKENS
# 출력: 31999
```

---

### RTC-ENV-002: ENABLE_TOOL_SEARCH

**테스트**: ENABLE_TOOL_SEARCH가 권장값으로 설정되어 있는지 확인

```bash
# 현재값 확인
echo $ENABLE_TOOL_SEARCH

# 기대값: auto:0
```

**권장값**: `auto:0`

**이유**: 프로덕션 환경에서 도구 검색 오버헤드 방지; 최적의 성능

**조치**:
```bash
# 쉘 프로파일에 추가
export ENABLE_TOOL_SEARCH=auto:0

# 쉘 다시 로드
source ~/.zshrc
```

---

## 카테고리 3: 권한 설정

### RTC-PERM-001: 필수 도구 허용

**테스트**: 필수 도구 패턴이 permissions.allow에 있는지 확인

**확인 파일**: `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      // ... 기타 패턴
    ]
  }
}
```

**필요 패턴**:
- `Bash(*)` - 쉘 명령에 필요
- `Read(*)` - 파일 읽기에 필요
- `Write(*)` - 파일 쓰기에 필요

**조치**:
1. `.claude/settings.json` 열기
2. `permissions.allow`에 이러한 패턴이 포함되어 있는지 확인
3. 필요한 경우 누락된 패턴 추가
4. 저장 후 Claude Code 재시작

---

## 카테고리 4: 플러그인 기능

### RTC-PLUG-001: TypeScript LSP 응답

**테스트**: TypeScript LSP 플러그인이 활성화되어 응답하는지 확인

**수동 테스트**:
1. Claude Code에서 TypeScript 파일 열기
2. 질문: "이 파일의 타입 정보 표시"
3. 응답에 타입 정의가 포함되어 있는지 확인

**기대 결과**: LSP가 TypeScript 코드의 타입 정보 반환

**문제 해결**:
- 작동하지 않는 경우: 설정에서 `typescript-lsp` 플러그인 활성화
- Claude Code 재시작
- `typescript-lsp@claude-plugins-official`이 설치되어 있는지 확인

---

### RTC-PLUG-002: Serena 플러그인 응답

**테스트**: Serena 플러그인이 활성화되어 응답하는지 확인

**수동 테스트**:
1. TypeScript/JavaScript 파일 열기
2. 질문: "이 파일의 심볼 개요 가져오기"
3. 응답에 클래스/함수 이름이 포함되어 있는지 확인

**기대 결과**: Serena가 심볼 계층 구조 반환

**문제 해결**:
- `serena@claude-plugins-official` 플러그인 활성화
- Claude Code 재시작
- 플러그인 설치 상태 확인

---

## 카테고리 5: 훅 통합

### RTC-HOOK-001: Pre-Write 훅 실행

**테스트**: pre-write 훅이 구성되어 있고 실행 가능한지 확인

**확인 파일**: `.claude/hooks/pre-write-approval.sh`

```bash
# 스크립트 존재 여부 확인
ls -la .claude/hooks/pre-write-approval.sh

# 실행 가능 여부 확인
if [ -x .claude/hooks/pre-write-approval.sh ]; then
  echo "✅ 스크립트 실행 가능"
else
  echo "❌ 스크립트 실행 불가"
fi
```

**조치**:
```bash
# 필요한 경우 스크립트를 실행 가능하게 만들기
chmod +x .claude/hooks/pre-write-approval.sh
```

**구성 확인**:

`.claude/settings.json` 확인:
```json
{
  "hooks": {
    "PreToolUse": {
      "matcher": "Write",
      "scriptPath": ".claude/hooks/pre-write-approval.sh"
    }
  }
}
```

**수동 테스트**:
1. Claude Code에 파일 쓰기 요청
2. 쓰기 작업 전에 훅이 실행되는지 확인
3. 터미널에서 훅 출력 확인

---

## 카테고리 6: 에이전트 워크플로우

### RTC-AGENT-001: 에이전트 파일 파싱 가능

**테스트**: 모든 에이전트 마크다운 파일에 유효한 frontmatter가 있는지 확인

```bash
# 에이전트 frontmatter 확인
for file in .claude/agents/*.md; do
  echo "$file 확인 중..."
  head -n 10 "$file" | grep -q "^---$" && echo "✅ 유효" || echo "❌ 무효"
done
```

**기대 결과**: 모든 에이전트 파일이 `---` frontmatter로 시작

**문제 해결**:
- 무효한 경우: frontmatter 구문 확인
- 첫 줄에 `---`로 시작해야 함
- 별도의 줄에 `---`로 끝나야 함
- YAML 구문이 유효해야 함

---

### RTC-AGENT-002: 스킬 파일 파싱 가능

**테스트**: 모든 스킬 SKILL.md 파일에 유효한 frontmatter가 있는지 확인

```bash
# 스킬 frontmatter 확인
for file in .claude/skills/*/SKILL.md; do
  echo "$file 확인 중..."
  head -n 10 "$file" | grep -q "^---$" && echo "✅ 유효" || echo "❌ 무효"
done
```

**기대 결과**: 모든 스킬 파일에 유효한 frontmatter가 있음

**문제 해결**:
- frontmatter YAML 구문 수정
- 일관된 들여쓰기 확인
- 탭 없이 공백만 사용

---

## 완료 체크리스트

수동 테스트 완료 후 수정 사항 확인:

```bash
# VERIFY 모드로 wm-setup 다시 실행
# 기대값: 모듈 7/7에서 통과율 향상

# 예시 출력:
# [7/7] 런타임 검사: ✅ 통과 (100%)
```

## 건강 점수 해석

| 통과율 | 상태 | 필요한 조치 |
|--------|------|-------------|
| 90-100% | ✅ 양호 | 조치 불필요 |
| 70-89% | ⚠️ 검토 | 경고 항목 수정 |
| 50-69% | ⚠️ 주의 | 대부분 항목 수정 |
| <50% | ❌ 긴급 | 모든 실패 수정 |

## 일반적인 문제 및 해결책

### 문제: MCP 서버 연결 안됨

**증상**: RTC-MCP-* 검사 실패

**해결책**:
1. Claude Code 설정에서 MCP 서버 활성화
2. Claude Code 재시작
3. MCP 서버 설치 확인
4. 서버 로그 검토

### 문제: 환경 변수 미설정

**증상**: RTC-ENV-* 검사 경고

**해결책**:
1. 쉘 프로파일에 export 추가
2. 쉘 세션 다시 로드
3. `echo $변수명`으로 확인

### 문제: 플러그인 응답 없음

**증상**: RTC-PLUG-* 검사 실패

**해결책**:
1. 설정에서 필요한 플러그인 활성화
2. Claude Code 재시작
3. 플러그인 설치 상태 확인
4. 플러그인을 최신 버전으로 업데이트

### 문제: 훅 스크립트 실행 불가

**증상**: RTC-HOOK-* 검사 경고

**해결책**:
1. `chmod +x .claude/hooks/*.sh` 실행
2. settings.json에서 훅 구성 확인
3. 훅 수동 테스트

### 문제: 에이전트/스킬 파일 무효

**증상**: RTC-AGENT-* 검사 경고

**해결책**:
1. YAML frontmatter 구문 수정
2. `---` 구분자 존재 확인
3. 들여쓰기 확인 (공백만 사용)

## 참조

- [runtime-validator.md](./runtime-validator.md) - 자동화된 검증 로직
- [runtime-checks.yaml](./runtime-checks.yaml) - 검사 정의
- [post-verify-workflow.md](./post-verify-workflow.md) - 워크플로우 상세
- [verify.md](../processes/verify.md) - VERIFY 모드 프로세스

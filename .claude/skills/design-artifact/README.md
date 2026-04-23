# design-artifact

HTML 기반 디자인 산출물 생성 스킬. 슬라이드 덱, 인터랙티브 프로토타입, 애니메이션, 와이어프레임, 랜딩 페이지, 목업 등을 단일 HTML 문서로 출력합니다.

전문 디자이너 페르소나로 동작하며, Intake → Context → Scaffold → Implementation → Verification → Delivery 6단계 흐름을 자동 수행합니다.

---

## 1. 호출

```bash
# 브리프와 함께 호출
/design-artifact 온보딩 화면 10슬라이드 덱 만들어줘

# 인자 없이 호출 (스킬이 질문으로 유도)
/design-artifact
```

---

## 2. 흐름 (자동)

| 단계 | 동작 | 사용자 할 일 |
|------|------|--------------|
| 1. Intake | 스킬이 10+ 질문 (청중·피델리티·변형 개수·디자인 시스템 등) | 답변 |
| 2. Context | shadcn / `.ui-snapshot.md` / `globals.css` 자동 수집 | 없으면 스크린샷·GitHub URL 제공 |
| 3. Scaffold | `designs/{이름}/index.html` 초안 (가정+논리) 생성 | 방향 확인 |
| 4. Implementation | `design-executor` 서브에이전트가 실제 HTML/JSX 작성 | 대기 |
| 5. Verification | `design-verifier` 가 Playwright 로 콘솔·레이아웃 검증 | 대기 |
| 6. Delivery | `open 'designs/.../index.html'` 명령 안내 | 브라우저에서 열기 |

---

## 3. 예시 브리프

| 유형 | 브리프 예시 |
|------|-------------|
| 슬라이드 덱 | `/design-artifact admin-portal 스타일로 Q2 로드맵 발표 덱 8장` |
| 프로토타입 | `/design-artifact 에이전트 생성 마법사 3단계 인터랙티브 프로토타입, 변형 3개` |
| 애니메이션 | `/design-artifact 온보딩 인트로 5초 애니메이션 비디오` |
| 랜딩 페이지 | `/design-artifact openclaw 마케팅 랜딩페이지 목업, 히어로+피처+CTA` |
| 와이어프레임 | `/design-artifact 결제 플로우 4화면 와이어프레임 스토리보드` |

---

## 4. UI 스킬 연동 (필수 선행 작업)

design-artifact는 프로젝트의 디자인 시스템을 컨텍스트로 사용하므로, **UI 관련 스킬을 먼저 실행해야 결과 품질이 보장**됩니다.

### 4.1 `/ui-snapshot` — 디자인 시스템 수집 (최우선)

처음 design-artifact를 사용하거나 디자인 시스템이 변경된 경우 반드시 먼저 호출합니다.

```bash
/ui-snapshot src/admin-portal
```

자동 추출 항목:
- shadcn/ui 구성 (`components.json`)
- CSS 변수/토큰 (`globals.css`)
- 컴포넌트 인벤토리
- 폰트 시스템, 컬러 팔레트, 스페이싱 스케일
- 아이콘 라이브러리

결과물 `.ui-snapshot.md`는 design-artifact의 Context 단계에서 자동으로 읽혀 `admin-portal 스타일` 같은 브리프 키워드에 매핑됩니다.

| 상황 | 실행 여부 |
|------|-----------|
| 프로젝트에 `.ui-snapshot.md`가 없음 | 반드시 실행 |
| `globals.css` / `components.json` 변경됨 | 갱신 필요 |
| 단순 재현(기존 스크린샷 기반) | 생략 가능 |

### 4.2 `/ui-audit` · `/ui-critique` — 산출물 검증 (선택)

Delivery 이후 품질 검증이 필요하면 UI 스킬을 파이프라인으로 호출합니다.

```bash
# 통합 파이프라인 (권장): audit + critique + fix
/ui designs/{이름}/index.html

# 개별 실행
/ui-audit designs/{이름}/index.html      # 기술 감사 (a11y, 성능, 토큰 준수)
/ui-critique designs/{이름}/index.html   # UX 비평 (Nielsen 휴리스틱, 인지 부하)
/ui-fix                                   # audit/critique 결과 기반 자동 수정
```

### 4.3 권장 파이프라인

```
/ui-snapshot        → 디자인 시스템 확립
      ↓
/design-artifact    → HTML 산출물 생성
      ↓
/ui designs/{이름}/index.html  → 기술·UX 감사 + 수정
      ↓
open designs/{이름}/index.html  → 최종 확인
```

---

## 5. 반복 · 수정 (Tweaks)

새 버전 요청 시 별도 파일을 만들지 않고 **원본의 Tweaks로 추가**됩니다.

```bash
primaryColor 를 green 계열로 바꾼 버전도 추가해줘
```

→ 기존 `index.html` 에 tweak 키 추가, 브라우저 우측 하단 Tweaks 패널에서 토글 가능.

---

## 6. 결과물 확인

```bash
open 'designs/{이름}/index.html'
```

Chrome/Safari 에서 로컬 HTML 로 렌더링. 검증 실패 시 스크린샷은 `designs/{이름}/.verify/` 에 저장됩니다.

---

## 7. 제한사항

- **PPTX 변환 미지원** — 브라우저에서 `Cmd+P`로 PDF 저장 권장
- **Tweaks 영속화 미동작** — Artifact 호스트 전용 기능. 값은 페이지 내에서만 적용, 새로고침 시 초기화
- **`window.claude.complete` 미동작** — Artifact 전용. AI 호출 데모 포함 금지

---

## 8. 팁

- **컨텍스트 없이 시작하면 결과 품질이 낮음** — UI 스냅샷 먼저: `/ui-snapshot` 호출
- **코드베이스 특정 컴포넌트 스타일 재현 시** — 파일 경로를 브리프에 명시 (예: `src/admin-portal/components/common/empty-state.tsx`)
- **막히면 자동 탐색 활용** — `Agent(subagent_type="Explore")` 서브에이전트가 코드베이스 탐색
- **덱 작업 시 셸 재사용** — `.claude/skills/design-artifact/templates/openclaw-deck-shell.html` 기반으로 section만 교체 권장
- **검증 실패 시 `.verify/` 확인** — `designs/{이름}/.verify/` 폴더의 스크린샷·콘솔 로그로 원인 파악

---

## 관련 스킬

| 스킬 | 역할 | 호출 시점 |
|------|------|-----------|
| `/ui-snapshot` | 디자인 시스템 수집 (`.ui-snapshot.md`) | design-artifact **이전** |
| `/ui` | 통합 UI 감사·비평·수정 파이프라인 | design-artifact **이후** |
| `/ui-audit` | 기술 감사 (a11y, 성능, 토큰 준수) | design-artifact 이후 (개별) |
| `/ui-critique` | UX 비평 (휴리스틱, 인지 부하) | design-artifact 이후 (개별) |
| `/ui-fix` | audit/critique 결과 반영 | design-artifact 이후 (개별) |

## 참고 문서

- 메인 스펙: `SKILL.md`
- 디자인 워크플로우: `references/design-workflow.md`
- 덱 작성 가이드: `references/deck-authoring.md`
- Tweaks 프로토콜: `references/tweaks-protocol.md`
- React/Babel 패턴: `references/react-babel-patterns.md`
- PPTX export: `references/pptx-export.md`

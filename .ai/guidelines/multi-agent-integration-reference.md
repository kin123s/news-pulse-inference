---
description: 타 AI 에이전트(Cursor, Copilot 등)와의 통합 및 통제 방안 레퍼런스
---

# 🤖 Multi-Agent Ecosystem Integration Reference

이 문서는 회사 내 신규 프로젝트나 타 레포지토리에 `.ai` 아키텍처를 도입할 때, **각양각색의 AI 에이전트(Cursor, Copilot, Cline, Antigravity 등)가 제멋대로 행동하지 않고 하나의 중앙 룰(`.ai`)을 따르도록 강제**하는 설정 방법들을 기록해 둔 가이드입니다.

---

## 핵심 원리: 각 프론트엔드의 진입점(Entrypoint) 통제

각 AI 도구들은 자신이 가장 먼저 읽도록 설계된 고유의 "설정 파일(Global Prompt)"을 가지고 있습니다. 
우리는 각 도구의 설정 파일(톨게이트)에 단 한 줄, **"작업 시작 전 무조건 `.ai/rules.md`와 `.ai/state/sessions/`를 읽어라"**라는 지침을 심어주는 방식으로 통제권을 `.ai` 폴더로 위임합니다.

---

## 1. Cursor (커서)
Cursor는 프로젝트 루트에 위치한 `.cursorrules` 파일을 글로벌 프롬프트로 인식합니다.
회사 레포지토리 최상단에 `.cursorrules`를 생성하고 아래 내용을 기입합니다.

```markdown
# .cursorrules

You MUST strictly follow the operating guidelines, context, and session states defined in the `.ai/` directory.
Always start every conversation or task by reading `.ai/rules.md` and the latest files in `.ai/state/sessions/`.
Never ignore these rules under any circumstances.
```

## 2. GitHub Copilot (코파일럿)
최신 VS Code Copilot Chat 환경에서는 특정 파일 형태의 지침 주입을 지원합니다.
프로젝트 루트에 `.github/copilot-instructions.md` 파일을 생성하고 아래 내용을 기입합니다.

```markdown
# .github/copilot-instructions.md

This project strictly relies on the `.ai` architecture for agent collaboration and state management.
Before providing any assistance, writing code, or making suggestions, you MUST:
1. Read `.ai/rules.md` to understand context and constraints.
2. Check `.ai/state/sessions/` for ongoing or previous agent tasks.
Failure to follow the `.ai/` instructions is a critical error.
```

## 3. Gemini / Antigravity (VS Code Extension 등)
AI 시스템의 전역 프롬프트(`GEMINI.md` 등)에 명시적인 행동 지침으로 선언합니다.

```markdown
# GEMINI.md 또는 글로벌 시스템 프롬프트

- 새 채팅(대화) 및 새로운 작업 시작 시 최우선 행동 지침: 에이전트는 무조건 해당 프로젝트의 `.ai/state/sessions/` 등 최신 상태 파일들을 먼저 읽어 이전 대화 맥락과 작업 진행 상황을 완벽히 인지한 후 답변 또는 작업을 시작하십시오.
- 복잡한 다단계 작업 진행 시, 반드시 `.ai/state/sessions/`에 현재 작업의 Session Context를 파일 형식(`.md`, `.json` 등)으로 최신화 기록하여 핸드오프 시 참조되도록 강제하십시오.
```

## 4. Cline / Roo Code 등 (VS Code 확장 기반 에이전트)
이러한 확장 프로그램들은 보통 `.clinerules`, `.roorules` 등을 지원하거나 확장 프로그램 설정 내에 Custom Prompt를 입력하는 란을 제공합니다.
해당 설정에 아래 내용을 추가합니다.

```text
작업(Task)을 시작하기 전에 반드시 다음 절차를 거치세요:
1. 루트의 `.ai/rules.md`를 읽어 프로젝트 제약사항을 식별할 것.
2. `.ai/state/sessions/` 디렉토리를 확인하고 최신 작업 문맥을 인계받을 것.
3. 작업 종료 또는 중단 시 반드시 `.ai/state/sessions/`에 현재 세션의 진행 내역을 작성할 것.
```

---

## 💡 기대 효과 (Why we do this)

1. **중앙 통제 (Single Source of Truth):** 룰과 문맥 관리는 오직 `.ai/` 디렉토리 내에서만 관리하고 업데이트하므로 유지보수가 파편화되지 않습니다.
2. **에이전트 핸드오프 (Agent Handoff):** Cursor로 작업하다 남긴 세션을 Copilot이나 Gemini가 이어서 작업할 수 있습니다.
3. **무상태(Stateless) 극복:** 챗창을 닫거나 새로 고침하더라도, AI가 하드와이어링된 룰에 의해 문맥(Sessions)을 스스로 찾아 읽으므로 히스토리가 끊기지 않습니다.

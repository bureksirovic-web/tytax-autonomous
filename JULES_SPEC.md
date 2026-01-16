# Jules Agent Specification (Level 23)

## 1. Input Sanitization (NEW)
- [x] **API Key Cleaning:** MUST strip all whitespace/newlines from GEMINI_API_KEY before use.
- [x] **Model Name Cleaning:** MUST strip whitespace from model names.
- [x] **URL Safety:** Prevent "No connection adapters" errors by ensuring clean connection strings.

## 2. Model Hierarchy (Strict 2.0/3.0)
- [x] **Coder:** gemini-3.0-pro-preview -> gemini-2.0-flash-exp -> gemini-2.0-flash.
- [x] **Sentinel:** gemini-2.0-flash-exp (Smart Safety).
- [x] **Critic:** gemini-2.0-flash (Fast Logic).
- [x] **BANNED:** All 1.5 models (Ghost Protocol/Hallucination risk).

## 3. Core Mechanics
- [x] **Ghost Protocol:** Blacklist 404 models per session.
- [x] **Rate Limit Shield:** Sleep 10s on 429 errors.
- [x] **Markdown Stripper:** Remove code fences from AI output.
- [x] **Task Rotation:** Move stuck tasks to bottom of backlog after 4 retries.

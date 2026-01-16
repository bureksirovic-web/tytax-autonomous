# Jules Agent Specification (Level 22)

## 1. Model Hierarchy (NO 1.5 Models)
- [x] **Coder:** Start with 3.0-pro-preview -> 2.0-flash-exp -> 2.0-flash.
- [x] **Sentinel/Critic:** Use 2.0-flash family ONLY.
- [x] **BANNED:** gemini-1.5-pro, gemini-1.5-flash.

## 2. Core Functionalities (from Evolution History)
- [x] **Ghost Protocol:** Blacklist 404 models.
- [x] **Rate Limit Shield:** Sleep 10s on 429.
- [x] **Markdown Stripper:** Clean code fences.
- [x] **Fuzzy Match:** Logic to find code even with bad indentation.
- [x] **Move-to-Bottom:** Rotate stuck tasks to end of backlog.
- [x] **Render Watchdog:** Verify deployment.

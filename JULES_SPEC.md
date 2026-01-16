# Jules Agent Specification (Level 17)

## 1. Multi-Model Intelligence ("The Swarm")
- [x] **Role Separation:** Distinct model lists for CODER, SENTINEL, and CRITIC.
- [x] **Ghost Protocol:** Blacklist models that return 404.
- [x] **Rate Limit Shield:** Backoff sleep on 429 errors.

## 2. The "Sentinel" Safety Rail
- [x] **Compiler Simulation:** Scans for ReferenceErrors (undefined variables).
- [x] **Blocker:** Discards code if Sentinel says "FAIL".

## 3. Deployment & Verification
- [x] **Render Watchdog:** Polls Render API until status is 'live'.
- [x] **Task Management:** Skips tasks after 4 failed retries.

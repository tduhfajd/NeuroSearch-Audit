# 01-01 Human Verify Evidence

Date: 2026-02-26

Commands executed:
- `curl -s http://127.0.0.1:8000/health`
- `curl -s http://127.0.0.1:8000/health/db`

Observed responses:
- `/health` -> `{"status":"ok"}`
- `/health/db` -> `{"status":"degraded"}` (expected without local PostgreSQL socket)

Conclusion:
- Uvicorn endpoint contract for `/health` is correct.
- `/health/db` diagnostic endpoint is reachable and returns known status.

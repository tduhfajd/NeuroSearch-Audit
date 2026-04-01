# Handoff Checklist

- Audit ID: `aud_20260311T120000Z_abc1234`
- Preconditions:
  - `manifest.stage_status.validate == completed`
  - `exports/review_brief.md` exists
  - `exports/backlog.json` exists

## Steps

1. Open `exports/review_brief.md` and confirm top gaps and contradictions are understood.
2. Open `exports/backlog.json` and confirm priority recommendations are usable.
3. Confirm the prompt pack in `prompts/` is present and package approval is still valid.
4. Record `review_prepared` using `scripts/record_handoff_event.py`.
5. Handoff the approved package and prompt pack to the external AI workflow.
6. Record `ai_handoff_sent` with the exact artifacts used.
7. After receiving AI outputs, record `post_handoff_captured` with notes about follow-up actions.


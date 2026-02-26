# 02-03 Human Verify Evidence

Date: 2026-02-26

Manual end-to-end scenario executed:
- API request: `POST /audits` with `{"url":"https://example.com","crawl_depth":50}`
- Worker step: `run_crawl_job(audit_id, session)` on same test DB

Observed output:
- `post_status 201`
- Response contained `queue_job_id` and created audit payload
- `pages_saved 1`
- `audit_status completed`
- `meta_robots ok`
- `meta_sitemap ok`
- `meta_pagespeed_source lighthouse`

Conclusion:
- End-to-end flow from audit creation to persisted crawler result works.
- Audit metadata contains robots/sitemap/pagespeed fields after worker completion.

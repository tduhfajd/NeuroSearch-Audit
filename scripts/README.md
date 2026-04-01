# scripts

Utility scripts for validation, schema checks, fixtures, local developer workflows, and package-derived delivery generation.

Notable delivery scripts:

- `build_client_report_input.py` builds `exports/client_report_input.json` from an approved `audit_package`.
- `generate_client_report.py` builds `exports/client_report.json` and `exports/client_report.md`.
- `generate_expert_report.py` builds `exports/expert_report.json` and `exports/expert_report.md`.
- `generate_internal_technical_report.py` builds `exports/internal_technical_report.md` for internal engineering use.
- `generate_commercial_documents.py` builds `exports/commercial_offer.*` and `exports/technical_action_plan.*`.
- `build_client_report_bundle.py` renders branded `pdf/html/docx` deliverables from `exports/client_report.md` into a sibling `deliverables/<audit_id>/client-report/` directory.

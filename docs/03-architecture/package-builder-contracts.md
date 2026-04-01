# Package Builder Contracts

## Goal

Зафиксировать boundary для package assembly и manifest generation без переинтерпретации crawl/extract/analyze артефактов.

## Responsibilities

- inventory package files under `audit_package/<audit_id>/`;
- generate deterministic `manifest.json`;
- record file categories, schema references, and checksums;
- derive stage completion status from required artifact presence.

## Non-Responsibilities

- changing artifact content;
- recomputing analysis or crawl outputs;
- deciding evidence validity.

## Manifest Rules

- file inventory must be stable and sorted;
- known artifact paths should map to schema identifiers;
- stage status should be explainable from the file set;
- manifest generation should be repeatable for the same file contents.

## Follow-up

- Phase 05-02 adds validators that consume the package and manifest.

# KBTrade local interface implementation plan

**Goal:** Adapt the campus feed to the Farmart marketplace reference and add editable accounts and listings, locally for team review.

**Architecture:** Preserve `users` and `posts`, their existing models, Django forms, views and templates. Use shared HTML/CSS and small vanilla JavaScript enhancements. No frontend framework or API rewrite.

**Approved scope:** Unified sale/lost/found feed, searchable categories, listing detail, modal creation with conditional fields and image preview, owner-only editing, visibility and lifecycle status, confirmed deletion, profile/avatar/password editing. Verified email remains unchanged. English copy follows the prototype. One image per item for this first version.

## Tasks
- [x] Add behavioral tests for conditional fields, authorship, owner-only updates/deletion, hidden listings, profile updates and registration redirects. Run to establish missing behavior.
- [x] Add minimal model migrations and Django forms/views/URLs. Keep existing Lost & Found URLs compatible. Seed categories idempotently through a migration.
- [x] Build light marketplace shell, warm yellow accents, category sidebar, editorial campus banner, responsive cards, detail page, modal form, account and authentication templates.
- [x] Run Django checks/tests, migration consistency checks and browser checks of feed, modal, account and mobile layout.
- [x] Document local startup and optional demo data; leave changes uncommitted and unpushed for user review.

## Review focus
Cross-user edits must fail; hidden listings must not leak publicly; negative prices and wrong-section categories must fail; invalid uploads and form errors must preserve user input; modal forms must remain usable with keyboard and as standalone pages.

## Decisions
User authorized implementation in the current local checkout. No branch switching, commit or push. Preserve existing dependency file; locally available Django 6.0 will be used for validation (repository pins 6.1.3).


## Verification and handoff
- 18 behavioral tests pass: registration/login, profile and avatar, password changes, owner-only mutations, hidden records, upload/removal validation, search/category filtering, conditional listing fields and legacy/modal routes.
- Native Chrome: inspected desktop homepage and cards visually; signed into demo account; opened modal and confirmed sale → lost field switching. Screenshots showed correct local assets and layout. Later browser access returned `noWindowsAvailable`, so account pages were checked via Django rendering tests, and mobile styling has not been visually verified.
- Fresh reviewer found legacy Lost & Found default and modal fragment after login issues. Added failing regression tests, fixed both. Additional upload test caught old-image restoration on removal; fixed.
- Existing local Python 3.14 + Django 6.0 used, Pillow 13.0 installed in ignored `.venv`. Team dependency pins unchanged.
- Demo database and media were created locally; 8 examples labelled Demo listing. No existing accounts were modified by seeding.
- Work remains uncommitted in the requested checkout. No push or deployment.

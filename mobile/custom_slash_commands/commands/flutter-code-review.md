# Flutter Code Review

Review code against security, performance, maintainability, and Flutter best practices. **Adapt the checklist** to your team’s chosen stack (state management, routing, i18n, logging) — items below stay tool-agnostic unless marked as conditional (“if your project uses …”).

## Arguments
- `$ARGUMENTS` — accepts the following flags (can be combined, space-separated):
  - `full` — review the entire project (all `.dart` files under `lib/`). Default (no flag) reviews only uncommitted changes.
  - `save` — save the review report to `code_review_reports/` directory as a timestamped Markdown file (e.g., `code_review_2026-03-09_14-30.md`)

## Instructions

### Determine Scope
- If `$ARGUMENTS` contains `full`: review ALL `.dart` files under `lib/` (use Glob to find them, then read and review each file)
- Otherwise (default): review only uncommitted changes:
  1. Run `git diff` and `git diff --cached` to get all uncommitted changes (staged + unstaged)
  2. Run `git status` to identify new untracked files — read their full contents

### Review
1. For each file in scope, review against ALL checklist categories below
2. For full project review, process files in batches using subagents to parallelize work
3. Output a structured report with findings grouped by severity and priority

### Save Report
- If `$ARGUMENTS` contains `save`:
  1. Create the `code_review_reports/` directory at the project root if it doesn't exist
  2. Save the full report as `code_review_reports/code_review_YYYY-MM-DD_HH-MM.md` using the current timestamp
  3. Confirm the saved file path to the user

## Report Format

```
## Code Review Report

**Date:** YYYY-MM-DD | **Scope:** uncommitted / full | **Branch:** branch_name

---

### 🔴 Critical (must fix before commit)

| # | File | Line | Category | Priority | Issue | Suggested Fix |
|---|------|------|----------|----------|-------|---------------|
| 1 | `file_path` | 42 | Architecture | Critical | Description of the issue | How to fix it |

### 🟡 High (should fix before merge)

| # | File | Line | Category | Priority | Issue | Suggested Fix |
|---|------|------|----------|----------|-------|---------------|
| 1 | `file_path` | 15 | Security | High | Description of the issue | How to fix it |

### 🟠 Medium (recommended improvements)

| # | File | Line | Category | Priority | Issue | Suggested Fix |
|---|------|------|----------|----------|-------|---------------|
| 1 | `file_path` | 88 | Performance | Medium | Description of the issue | How to fix it |

### 🔵 Low (nice to have)

| # | File | Line | Category | Priority | Issue | Suggested Fix |
|---|------|------|----------|----------|-------|---------------|
| 1 | `file_path` | 5 | Dependencies | Low | Description of the issue | How to fix it |

### 🟢 Good Practices Found
- Brief positive observations

### Summary

| Metric | Count |
|--------|-------|
| 🔴 Critical | X |
| 🟡 High | X |
| 🟠 Medium | X |
| 🔵 Low | X |
| **Total Issues** | **X** |
| **Files Reviewed** | **X** |
```

**Notes:**
- Skip any severity section that has zero findings
- Each row must include the category (Security, Performance, Architecture, etc.) and priority level
- Sort rows within each section by category for readability

## Checklist

### Security
- [ ] **[High]** No hardcoded secrets, API keys, tokens, or passwords
- [ ] **[High]** Secrets and environment-specific config come from secure configuration (e.g. build-time flags, CI secrets, platform keychains) — not committed plaintext
- [ ] **[High]** No hardcoded production URLs where environments differ — use config or constants appropriate to the app
- [ ] **[Medium]** User input is validated at boundaries (text fields, API params)
- [ ] **[Medium]** No raw SQL or unsafe string interpolation in queries
- [ ] **[Medium]** No logging of sensitive data (passwords, tokens, PII)
- [ ] **[Medium]** API error responses don't leak internal details to UI
- [ ] **[Low]** No use of `dart:mirrors` or dynamic code execution for untrusted input
- [ ] **[Low]** File paths and URLs are validated or sanitized before use
- [ ] **[High]** *If the app persists sensitive data locally:* use appropriate secure storage for secrets (not plain `SharedPreferences` for credentials)
- [ ] **[High]** *If the app uses an encrypted local database:* encryption keys are not hardcoded and meet your security baseline

### Performance
- [ ] **[High]** No unnecessary widget rebuilds — state updates are scoped (follow your chosen state-management patterns)
- [ ] **[High]** Expensive work is not inside `build()` methods
- [ ] **[High]** Long or dynamic lists use lazy builders (`ListView.builder` / `SliverList`, etc.), not unbounded `children` lists
- [ ] **[High]** No redundant network or disk I/O (deduplication, caching, early returns where appropriate)
- [ ] **[Medium]** Controllers, listeners, streams, and subscriptions are disposed or cancelled
- [ ] **[Medium]** Images are sized and cached appropriately (no unbounded large network images)
- [ ] **[Medium]** `const` constructors used where possible
- [ ] **[Medium]** No blocking operations on the main isolate without justification
- [ ] **[Medium]** Logging uses a consistent approach (e.g. `dart:developer` `log`, or your team logger) — avoid `print()` in production paths

### Architecture & maintainability
- [ ] **[High]** Clear separation of concerns (UI vs domain/data vs infrastructure), consistent with project conventions
- [ ] **[High]** Side effects (I/O, repositories) are not scattered arbitrarily inside pure UI widgets without a documented pattern
- [ ] **[High]** Navigation is consistent with the project’s chosen router (no ad-hoc mixes of patterns without reason)
- [ ] **[Medium]** Folder structure and naming match project conventions
- [ ] **[Medium]** Prefer reusing existing shared widgets/utilities before adding duplicates
- [ ] **[Medium]** Class naming: `PascalCase`; file naming: `snake_case` where that is the project standard
- [ ] **[Medium]** One primary public widget/class per file when that is the team rule
- [ ] **[Medium]** Import order and style follow project or `dart analyze` / linter rules
- [ ] **[Medium]** After async gaps, check `context.mounted` (or equivalent) before using `BuildContext`
- [ ] **[Low]** Avoid deep nesting; prefer early returns and small functions

### Translation / localization
- [ ] **[High]** No hardcoded user-facing strings — use the project’s localization mechanism (`flutter gen-l10n`, ARB files, or chosen i18n package)
- [ ] **[High]** Errors, labels, tooltips, and empty states are localized
- [ ] **[Medium]** New strings are added for all supported locales the app ships with
- [ ] **[Medium]** Locale/codegen assets are regenerated when translation sources change, if applicable

### UI / layout & accessibility
- [ ] **[High]** Text has `maxLines` and `overflow` where truncation is required
- [ ] **[High]** Text inside tight horizontal layouts uses `Expanded` / `Flexible` / `FittedBox` as appropriate to avoid overflows
- [ ] **[Medium]** Rows that may wrap use `Wrap` or scrollable containers when needed
- [ ] **[Medium]** `mainAxisSize: MainAxisSize.min` on flex children that should not expand unnecessarily
- [ ] **[Medium]** Responsive or scrollable patterns used where small screens or keyboard could break layout
- [ ] **[Medium]** Prefer shared design-system components and theme tokens (colors, typography, spacing) over magic numbers
- [ ] **[Medium]** Touch targets and contrast are reasonable; consider accessibility (semantics, labels) where the app targets a11y

### API & data layer
- [ ] **[High]** Magic strings for statuses or enums replaced with typed values or shared constants where the project defines them
- [ ] **[High]** Date/time from APIs parsed and displayed in the user’s local timezone when appropriate (`.toLocal()` or equivalent)
- [ ] **[High]** API failures map to user-visible messages without exposing stack traces or internal IDs
- [ ] **[High]** Generic fallback errors are localized or user-safe
- [ ] **[Medium]** Models and DTOs live in predictable modules; avoid duplicate model definitions
- [ ] **[Medium]** Base URLs and environment endpoints centralized per project policy
- [ ] **[Medium]** Loading and empty states are explicit for async screens
- [ ] **[Medium]** User feedback for success/error (snackbar, banner, inline) matches product patterns

### Error handling
- [ ] **[High]** Network and timeout failures handled gracefully
- [ ] **[High]** Null and empty collections handled in UI
- [ ] **[Medium]** Loading indicators or skeletons for async operations where UX expects them
- [ ] **[Medium]** Offline or flaky-network behavior considered if the app supports it
- [ ] **[Medium]** Forms show validation errors clearly

### Dependencies
- [ ] **[Medium]** Dependencies align with declared architecture and are actively maintained
- [ ] **[Medium]** No obvious redundant or conflicting packages
- [ ] **[Low]** Version constraints are appropriate (avoid unnecessary `any` / overly loose ranges without reason)

### Flutter & Dart quality
- [ ] **[High]** No empty `catch` blocks — log or handle meaningfully
- [ ] **[High]** Async code handles errors (`try/catch`, `Future` error handlers, `Result`-style patterns)
- [ ] **[Medium]** Lint suppressions (`// ignore:`) are rare and justified
- [ ] **[Medium]** `late` used only when initialization is guaranteed before read
- [ ] **[Medium]** Null safety: avoid unnecessary `!`; prefer parsing and guards
- [ ] **[Medium]** `dispose()` releases animation controllers, focus nodes, scroll controllers, and listeners
- [ ] **[Medium]** Keys on list children where identity matters for performance or state

### Assets & resources
- [ ] **[Medium]** Asset paths use codegen or centralized references (e.g. FlutterGen `Assets` class) if the project uses it
- [ ] **[Medium]** Regenerate asset/codegen outputs after asset changes when required
- [ ] **[Low]** Assets grouped logically (images, fonts, lottie, etc.)

### Database & migrations
- [ ] **[Critical]** No destructive migrations (`DROP TABLE`, `DROP COLUMN`) without a documented migration path and backup strategy
- [ ] **[High]** Schema changes go through versioned migrations the project uses
- [ ] **[High]** Migration version or schema revision incremented when structure changes
- [ ] **[High]** New tables use safe creation patterns (`IF NOT EXISTS` or equivalent) per your DB layer
- [ ] **[High]** Migrations tested against realistic data when possible

### Code quality
- [ ] **[High]** User-facing errors are clear and actionable
- [ ] **[Medium]** No dead code or large commented-out blocks left in PRs
- [ ] **[Medium]** Duplicated logic extracted when it clearly belongs in a shared helper or widget
- [ ] **[Medium]** Functions are focused; extract when a method does multiple unrelated things
- [ ] **[Medium]** Names reflect intent; avoid cryptic abbreviations
- [ ] **[Medium]** Magic numbers and repeated literals replaced with named constants or theme values

## Rules
- **Uncommitted mode (default)**: Only review the CHANGED lines/files — do not flag pre-existing issues in unchanged code
- **Full mode (`full`)**: Review all `lib/**/*.dart` files — flag all issues found across the entire project. Use subagents to parallelize review of different directories (screens, models, repositories, components, constants, etc.)
- Be specific: always include file path and line number
- For each finding, briefly explain WHY it's a problem and suggest a fix
- If no issues found in a category, skip that category in the report
- Prioritize critical security and crash-potential issues over style nits
- In full mode, also include a **Project Health Summary** at the end with overall observations about architecture, consistency, and technical debt

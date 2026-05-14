# Changelog

All notable changes to WhoCord will be documented in this file.

## [1.1.0] – 2026-05-14

### Added
- Six new investigation modules – Email, Domain, Phone, Image, URL, Data Probe (auto‑detect).
- Live dashboard with module cards, stage list, pivot confirmation modal, history page.
- NEW HTML report with collapsible platform cards, avatars, GHunt Google card, phone/URL/domain data.
- Full‑intel AI narrative and persona summary (LLM now sees emails, breaches, WHOIS, DNS, URL metadata, phone, GHunt).
- Unified email enrichment – shared `enrich_email` function for manual and email modules.
- Blackbird API data (Spotify, Twitter, Duolingo) stored as `socid_raw`.
- theHarvester curated sources – free only (`crtsh,robtex,urlscan,waybackarchive,duckduckgo,threatcrowd`).

### Fixed
- GHunt Google card not appearing (missing import).
- Platform names showing as `Blackbird_Email_Https:`.
- Duplicate discovery runs during pivots.
- Phone card missing from HTML report.
- URL module data not displayed.
- GitHub profiles merged into one card.

### Changed
- Frontend rebuilt with React + TypeScript (requires `npm run build`).
- GHunt maps extraction now includes reviews, answers, profile link.

## [1.0.3] – 2026-05-06 first portable release

* **Self‑contained zip**: no installation required – just extract and run on any modern 64‑bit Linux system.
* All external tools (Sherlock, Maigret, Naminter, Blackbird, etc.) bundled with their dependencies.
* Web dashboard now included in the portable package.

### Added
- **Rotating debug logs** – structured, timestamped log files with automatic rotation (10 MB, 5 backups) for easier investigation auditing.
- **Tool updater** – interactive menu option and web dashboard button to upgrade all pip‑based external tools to their latest versions. Non‑pip tools (Scylla, PhoneInfoga, Sociopath) are listed as “cannot be auto‑upgraded”.
- **Advanced email analysis** – optional SMTP verification (`ENABLE_EMAIL_VERIFY`) checks if a mail server accepts the address; Gravatar lookup retrieves profile images for emails.
- **AI persona summary** – a dedicated AI‑generated personality sketch based on collected profile bios, displayed in a new report section.
- **Web dashboard upgrade streaming** – live pip upgrade output displayed in the Logs tab when using the “Upgrade All Tools” button.

### Changed
- **Blackbird results** – HTML report now shows only Blackbird files created during the current investigation, eliminating stale data from previous runs.
- **Sociopath** – migrated to the Go‑based `sociopath` binary by codeGROOVE-dev due to the original Python repo being unavailable. The pipeline command was updated accordingly.
- **Email verification** – removed the old `SMTP_CHECK` guard from the advanced verification function; control is now solely via `ENABLE_EMAIL_VERIFY`.

### Fixed
- Fixed stale Blackbird results copying all historical JSON files into the report cache.
- Fixed persona summary ignoring bios stored inside `socid_raw` data.
- Fixed `SyntaxError` in `utils.py` after debug log refactoring.

## [1.0.2] – 2026-05-02

### Added
- **Web dashboard** – full Flask‑based dark‑themed SPA with Investigation, Configuration, Live Logs (SSE), and Report tabs.
- **Enhanced AI report** – Groq‑generated markdown now includes relationship analysis and critical points of attention.
- **Enriched profile data** – socid‑extractor results displayed in a dedicated report section.
- **Blackbird results** – dedicated report section with avatars for all discovered accounts.
- **Formatted breaches** – clean, readable cards with optional raw detail toggles.
- **One‑click launcher** – `run.sh` starts the dashboard without a terminal.
- **Stop button** – ability to kill a running investigation from the web UI.
- **Token status** – dashboard badges update instantly when tokens are saved.
- **Centralised logging** – structured logging via `logger.py`.

### Changed
- Switched to a dark monochrome color theme for all reports.
- Removed forced `--debug` in web UI; pipeline runs quieter by default.

## [1.0.1] 

### Added
- **Blackbird integration** – email‑based discovery and 600+ additional username sites. Auto‑download of `wmn-data.json`.
- **GHunt** – Google account info extraction (requires `ghunt login`).

### Removed
- Email guesser module; only user‑supplied emails are now processed.

## [1.0.0] 

- Initial public release.
- Core pipeline with Sherlock, Maigret, Holehe, h8mail, GitFive, etc.
- Interactive menu, web dashboard planned.

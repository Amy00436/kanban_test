# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file IT PMO Kanban board for a **fictitious "Demo Bank"**, used as an internal demo/training tool. Everything lives in `index.html` (markup + one `<style>` + one `<script>`).

## Hard constraints (keep these)

- Vanilla HTML/CSS/JS only: no frameworks, libraries, build step, npm, CDN scripts, web fonts or image files. Icons and the logo are inline SVG or Unicode.
- Must run by double-clicking `index.html` (file://), with no server needed.
- **No persistence.** State is in memory only; never use localStorage, sessionStorage, IndexedDB or cookies. A refresh resets the board to the seed data on purpose, and the header note says so.
- **No real-bank branding.** Do not reintroduce "UOB" or any real bank's name, logo or trademarks. The brand is "Demo Bank", task IDs are `DEMO-ITPM-####`, and the logo is a generic inline SVG.
- The only network call is to FormSubmit (`FORMSUBMIT_ENDPOINT`, the first line of the script). Keep the placeholder `YOUR_EMAIL@example.com`; don't put real addresses in the file.
- No `alert()`, `confirm()` or `!important`. Colours and spacing come from CSS custom properties on `:root`.

## Running and checking

- Open in a browser: `Start-Process index.html` (PowerShell).
- Node is **not** installed. For automated checks, use headless Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`:
  - Screenshot: `chrome --headless=new --window-size=1400,1100 --screenshot=out.png file:///.../index.html`
  - Scripted checks: copy `index.html` to the scratchpad, replace the final `init();` line with `init();` followed by test code that writes results to `document.title`, then run `chrome --headless=new --virtual-time-budget=8000 --dump-dom file:///.../probe.html` and grep the `<title>`.
  - Headless Chrome on Windows won't make the window narrower than about 504px. Measure `innerWidth` instead of trusting the screenshot width.
- Forbidden-API scan: `grep -nE "localStorage|sessionStorage|indexedDB|document\.cookie|<script src|<link|!important|alert\(|confirm\(" index.html` should return nothing.

## Script architecture

- `state = { tasks, filters }` is the single source of truth. `uiState` holds UI-only state (`confirmDeleteId`, `focusAfterRender` CSS selector, `sending`).
- One-way flow: the mutations (`addTask`, `moveTask`, `deleteTask`) change `state`, then call `renderBoard()`. `renderBoard()` rebuilds all four columns from `applyFilters(state.tasks)`, then calls `renderSummary()` (which counts **unfiltered** tasks) and `restoreFocus()`. Don't change card contents anywhere except through `renderBoard()`/`renderCard()`.
- Because each render replaces the cards, all board events (click, change, drag*) are **delegated** on `#board` and use `data-action` / `data-id` attributes. To keep keyboard focus across a re-render, set `uiState.focusAfterRender` to a selector before rendering.
- Every interpolated string must pass through `escapeHtml()`. Toasts use `textContent`.
- Dates are local `YYYY-MM-DD` strings (`toISODate`/`todayISO`), compared as strings. Seed due dates are relative to today (`daysFromToday`), so some tasks are always overdue.
- Read form fields as `form.elements.<name>`, not `form.<name>`, because names like `title` clash with built-in form properties.
- Add Task is optimistic: the card is added and the form reset first, then `notifyNewTask()` runs. A failure only shows a warning toast. The modal stays open after a submit, so the "Sending…" button state is visible.

## Versions: v1 (`index.html`) and v2 (`v2/index.html`)

- Both are deployed: v1 at the Pages root, v2 at `/v2/`. **Leave v1 unchanged**; new work goes into `v2/index.html`. Every rule in this file applies to both files, and CI checks both.
- v2 adds a dark theme: colour tokens on `:root` are redefined under `:root[data-theme="dark"]` and under `@media (prefers-color-scheme: dark)` with `:root:not([data-theme="light"])`. Keep the two dark blocks identical. The toggle choice is `uiState.theme` (in memory only; `null` follows the OS).
- v2 has a CSP `<meta>` (`connect-src https://formsubmit.co` only). If you add a network call or resource, update the CSP too. The favicon is a data-URI `link` added from JS by `setFavicon()`.
- v2 shows a dismissible "IT Project Briefing" announcement (`#briefing`, `wireBriefing()`) once the tab has been visible for `BRIEFING_DELAY_MS` (10s). It stops appearing after `BRIEFING_DATE`, so update both the date constant and the `<aside>` text for a new meeting.
- v2's assignee filter uses `scheduleRender()` (one render per animation frame). Other mutations still call `renderBoard()` directly.

## Project skills (`.claude/skills/`)

- `frontend-design` (anthropics/skills): visual direction. `ui-ux-pro-max` (nextlevelbuilder): UX/accessibility search (`python .claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --domain ux`). `cybersecurity-analyst` (rysweet/amplihack): threat model and audit commands for this app.
- Each SKILL.md opens with a "Project overrides: Demo Bank IT PMO Kanban" section that adapts the upstream guidance to the constraints above (no web fonts, no libraries, no persistence, existing `:root` tokens). Those overrides, and this file, win over the upstream text below them.
- `skills-lock.json` tracks the two installed with `npx skills add`. `cybersecurity-analyst` was copied manually (that repo can't be cloned on Windows), so re-apply the overrides by hand if you update it.

## Project agents (`.claude/agents/`)

- `security-scanner`: scans both pages, the workflow and `.claude/` tooling, classifies findings (severity, OWASP 2021, CWE, boundary B1–B5) and writes a .docx report to `security-reports/` (git-ignored, since it lists unfixed issues). It is read-only on site code and only recommends fixes.
- The .docx is built by `.claude/scripts/security_report_docx.py` (stdlib only, because python-docx and Node aren't installed) from a findings JSON. The schema is in the script's docstring.

## FormSubmit gotchas

- FormSubmit often returns **HTTP 200 with `{"success":"false"}`** for failures, so `notifyNewTask()` checks the `success` field as well as `res.ok`.
- Pages opened via file:// always fail ("open this page through a web server"). To test real email delivery, serve the folder over http (e.g. `python -m http.server`).
- A new address needs a one-time activation: the first submission sends a confirmation email, and nothing is delivered until its link is clicked.

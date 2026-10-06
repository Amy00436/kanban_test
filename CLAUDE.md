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

## FormSubmit gotchas

- FormSubmit often returns **HTTP 200 with `{"success":"false"}`** for failures, so `notifyNewTask()` checks the `success` field as well as `res.ok`.
- Pages opened via file:// always fail ("open this page through a web server"). To test real email delivery, serve the folder over http (e.g. `python -m http.server`).
- A new address needs a one-time activation: the first submission sends a confirmation email, and nothing is delivered until its link is clicked.

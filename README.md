# kanban_test: Demo Bank IT PMO Kanban

A single-file IT PMO Kanban board for the fictitious **Demo Bank**, built as a demo and training tool. The whole app (markup, styles and script) lives in one `index.html` written in vanilla HTML, CSS and JavaScript. There are no frameworks, build step or dependencies, and it runs straight from your file system.

**Live demo:** https://amy00436.github.io/kanban_test/

## Features

- **Four columns:** Backlog, In Progress, Blocked and Done, each with a task count.
- **Seed data:** eight sample IT PMO tasks (IDs `DEMO-ITPM-0001` onwards). Due dates are relative to today, so some tasks are always overdue.
- **Add tasks** through a modal form with validation (title, description, project/workstream, category, assignee, priority, due date, status).
- **Move tasks** by drag and drop between columns, or with the keyboard-accessible "Move ▸" menu on each card.
- **Delete tasks** with an inline Yes/No confirmation.
- **Filters** by project, assignee (text match) and priority, with a "Showing X of Y tasks" note and a Clear filters button.
- **Summary strip** in the header with totals per status and an overdue count, always covering all tasks, whatever the filters.
- **Overdue highlighting:** unfinished tasks past their due date get an "Overdue" badge.
- **Priority colour coding** (Critical, High, Medium, Low) on each card's edge and pill.
- **Email notification** for every new task via [FormSubmit](https://formsubmit.co/) (see below).
- Accessible and responsive: keyboard focus is kept across re-renders, toasts are announced to screen readers, and the columns stack on narrow screens.

## How to run

1. Download or clone this repository.
2. Double-click `index.html`.

That's all. There's no build, no server and nothing to install.

> **No persistence, by design.** Tasks are held in memory only. Refreshing the page resets the board to the sample data. The app never uses localStorage, cookies or any other browser storage.

## Email notification setup (optional)

When a task is added, the app POSTs it to FormSubmit, which emails it to an address you choose. The card is added right away, and if the email fails you only get a warning toast.

1. In your **local copy** of `index.html`, find the first line of the script:
   ```js
   const FORMSUBMIT_ENDPOINT = "https://formsubmit.co/ajax/YOUR_EMAIL@example.com";
   ```
   Replace `YOUR_EMAIL@example.com` with your address.
2. Serve the folder over http, because FormSubmit always rejects pages opened via `file://`:
   ```sh
   python -m http.server
   ```
   Then open http://localhost:8000/.
3. Add a task. The first submission to a new address triggers a **one-time activation email** from FormSubmit. Click its link, and later tasks will be delivered.

> **Do not commit a real email address.** Keep the `YOUR_EMAIL@example.com` placeholder in the repository. The CI check fails if any other address appears in `index.html`.

## Project structure

```
index.html                    The whole app: markup, <style> and <script>
README.md                     This file
CLAUDE.md                     Constraints and architecture notes for contributors
.github/workflows/pages.yml   CI checks and GitHub Pages deployment
.gitignore
```

## CI/CD

`.github/workflows/pages.yml` runs on every push and pull request to `main`, and can be started by hand.

The **check** job fails the build if:

- `index.html` uses a forbidden API or pattern: `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie`, external `<script src>` or `<link>`, `!important`, `alert()` or `confirm()`;
- `index.html` mentions a real bank's name;
- `index.html` contains an email address other than `YOUR_EMAIL@example.com`;
- `index.html` is missing or its HTML does not parse;
- [gitleaks](https://github.com/gitleaks/gitleaks) finds a secret anywhere in the git history.

The **deploy** job runs only after the checks pass, on pushes to `main` (and on manual runs). It publishes **only `index.html`** to GitHub Pages, so nothing else in the repository is put on the site.

## Disclaimer

"Demo Bank" is a fictitious organisation created for demonstration and training. This project is not affiliated with, endorsed by or connected to any real bank or financial institution. All tasks, names and data are made up.

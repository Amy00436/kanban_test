---
description: Security-scan, document, push this project to GitHub, deploy GitHub Pages with CI/CD, and fill in the repo About section
argument-hint: <github-repo-url>  e.g. https://github.com/owner/repo
allowed-tools: Bash, PowerShell, Read, Write, Edit, Glob, Grep, WebFetch
---

# Publish this project to GitHub

Target repository: **$ARGUMENTS**

Follow the steps below in order. The security scan runs **before** anything is pushed, even though it is the last thing the user cares about: a secret that reaches GitHub has to be treated as leaked, even if it is deleted afterwards.

Respect every constraint in `CLAUDE.md` (vanilla single-file app, no persistence, no real-bank branding, FormSubmit placeholder `YOUR_EMAIL@example.com`, etc.). Do not change `index.html` unless the security scan requires it.

## 0. Validate input and tooling

1. If `$ARGUMENTS` is empty, ask the user for the GitHub repo URL and stop until you have it.
2. Parse `OWNER` and `REPO` from the URL. Accept `https://github.com/OWNER/REPO`, `https://github.com/OWNER/REPO.git` and `git@github.com:OWNER/REPO.git`. Reject anything that isn't on github.com.
3. Work out how to talk to the GitHub API, in this order of preference:
   - `gh` CLI, if `gh auth status` succeeds.
   - Otherwise `curl` against `https://api.github.com` with a token from the `GH_TOKEN` or `GITHUB_TOKEN` environment variable (`-H "Authorization: Bearer $GH_TOKEN"`). Never print the token, never write it to a file, never put it in a git remote URL.
   - If neither is available, carry on with the git-only steps (1–5) and at the end give the user the exact manual steps for steps 6–7 (repo Settings → Pages → Source: GitHub Actions; repo home → About ⚙ → description, website, topics).
4. Run `git status` and `git remote -v`. If there are uncommitted changes that were not made by this command, show them to the user and ask whether to include them.

## 1. Create or update README.md

Read `index.html` and `CLAUDE.md`, then write `README.md` for someone landing on the GitHub repo. Keep any useful content already in the README. It should include:

- Title and a one-paragraph summary: a single-file IT PMO Kanban board for the fictitious **Demo Bank**, used as a demo/training tool.
- **Live demo** link: `https://OWNER.github.io/REPO/` (lower-case the owner).
- Features, taken from what the app really does (columns, filters, add/move/delete tasks, drag and drop, summary counts, overdue highlighting, email notification via FormSubmit).
- How to run: download and double-click `index.html`; no build, no server, no dependencies.
- A note that state is in memory only and a refresh resets the board, on purpose.
- Email notification setup: replace `YOUR_EMAIL@example.com` in `FORMSUBMIT_ENDPOINT` locally, serve over http (`python -m http.server`) because file:// fails, and click FormSubmit's one-time activation email. Say clearly not to commit a real address.
- Project structure, CI/CD (what the workflow checks and that `main` deploys to Pages), and a disclaimer that Demo Bank is fictitious and not affiliated with any real bank.

Do not put real email addresses, tokens, names of real banks, or internal URLs in the README.

## 2. Create or update the CI/CD workflow

Make sure `.github/workflows/pages.yml` (keep the existing file name if one exists) does both CI and CD:

- Triggers: `push` to `main`, `pull_request` to `main`, and `workflow_dispatch`.
- A **`check`** job (runs for every trigger) on `ubuntu-latest` that fails the build if:
  - the forbidden-API scan from `CLAUDE.md` finds anything in `index.html` (`localStorage|sessionStorage|indexedDB|document\.cookie|<script src|<link|!important|alert\(|confirm\(`);
  - `index.html` contains `UOB` (case-insensitive, whole word);
  - `index.html` contains an email address other than `YOUR_EMAIL@example.com`;
  - `index.html` is missing or its HTML does not parse (e.g. `python3 -c "import html.parser,sys; html.parser.HTMLParser().feed(open('index.html',encoding='utf-8').read())"`);
  - a secret scanner finds anything, using `gitleaks/gitleaks-action@v2` with `fetch-depth: 0` on checkout (it needs `GITHUB_TOKEN` in `env`).
- A **`deploy`** job with `needs: check`, which only runs on `push` to `main` or `workflow_dispatch` (`if: github.event_name != 'pull_request'`). It stages only `index.html` into `_site/` (never the whole repo, so `CLAUDE.md`, `.claude/` and `.github/` are not published), then uses `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3` and `actions/deploy-pages@v4`, with the `github-pages` environment.
- Least-privilege permissions: `contents: read` at the top level; `pages: write` and `id-token: write` only on the deploy job. Keep a `concurrency: { group: pages, cancel-in-progress: false }` block.

Before relying on the shell commands in the workflow, run the same grep checks locally against `index.html` and confirm they pass.

## 3. Security scan (blocking)

Scan **everything that will be pushed**: tracked files, new files about to be committed, and the full git history (`git log -p --all`). Use `git ls-files` plus `git status --porcelain` to get the file list, and ignore `.git/`.

Look for:

- Secrets: private keys (`-----BEGIN .*PRIVATE KEY-----`), GitHub tokens (`gh[pousr]_[A-Za-z0-9]{36,}`, `github_pat_`), AWS keys (`AKIA[0-9A-Z]{16}`), Slack tokens (`xox[baprs]-`), Google API keys (`AIza[0-9A-Za-z_-]{35}`), Anthropic/OpenAI keys (`sk-ant-`, `sk-[A-Za-z0-9]{20,}`), JWTs (`eyJ[A-Za-z0-9_-]+\.eyJ`), and generic assignments such as `(api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*['"][^'"]{8,}`.
- Credentials in URLs: `https?://[^/\s:@]+:[^/\s@]+@`.
- Sensitive files: `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `*.sqlite`, `*.db`, `credentials*`, `secrets*`, `.claude/settings.local.json`, and any memory/transcript files.
- Personal data: any email address except `YOUR_EMAIL@example.com`, `noreply@anthropic.com` (commit trailers), and GitHub `users.noreply.github.com` addresses. Also phone numbers and IDs that look real.
- Project-specific rules: no `UOB` or other real bank names/logos, and `FORMSUBMIT_ENDPOINT` still uses the placeholder.
- Large or binary files that don't belong in a single-file HTML project.

If `gitleaks` or `trufflehog` is installed locally, also run it (`gitleaks detect --source . --log-opts="--all"`), but don't rely on it alone.

Create or update `.gitignore` so it covers `.env*`, key files, `.claude/settings.local.json`, OS junk (`Thumbs.db`, `.DS_Store`) and editor folders.

**If anything is found:** stop. Report each finding with file, line and the reason, with the secret masked (show at most the first 4 characters). Do not push. For problems in the working tree, propose the fix. For problems in git history, explain that the history has to be rewritten (e.g. `git filter-repo`) and that the secret must be rotated, and only do this if the user explicitly agrees, because it is destructive. Continue only once the scan is clean or the user has explicitly accepted each remaining finding.

## 4. Commit

Stage only the files this command created or changed, plus any the user approved in step 0 (use explicit paths, not `git add -A`). Show `git diff --cached --stat`, then commit with a clear message, e.g. `Add README, CI/CD workflow and repo metadata`, following the repo's commit attribution rules.

## 5. Push

1. If there's no `origin`, add it with the repo URL. If `origin` points somewhere else, show both URLs and ask before changing it.
2. Make sure the branch is `main` (`git branch -M main` only if the repo has a single local branch and the user agrees).
3. `git push -u origin main`. Never use `--force`. If the push is rejected because the remote has commits we don't have, stop and explain the options (pull/rebase, or the user deciding to overwrite). Don't pick one yourself.
4. If the remote repo doesn't exist and you have API access, ask the user whether to create it (public or private) before doing so.

## 6. Enable or update GitHub Pages

Use the API (`gh api` or curl):

- `GET /repos/OWNER/REPO/pages`. If it returns 404, `POST /repos/OWNER/REPO/pages` with `{"build_type":"workflow"}`. If Pages exists but `build_type` isn't `workflow`, `PUT` it to `workflow`.
- Note: Pages on a **private** repo needs a paid plan. If the API says so, tell the user.
- Watch the latest workflow run (`gh run watch`, or poll `GET /repos/OWNER/REPO/actions/runs?branch=main&per_page=1` about every 30s, for up to 10 minutes). If it fails, fetch the failed job's logs, fix the cause, commit and push again (at most two attempts before asking the user).
- Once it's deployed, read `html_url` from `GET /repos/OWNER/REPO/pages` and confirm the page returns HTTP 200 (`curl -sI`).

## 7. Update the repo About section

`PATCH /repos/OWNER/REPO` with:

- `description`: one line, under 350 characters, e.g. "Single-file IT PMO Kanban board for the fictitious Demo Bank: vanilla HTML/CSS/JS, no build, no dependencies."
- `homepage`: the Pages URL from step 6.

Then `PUT /repos/OWNER/REPO/topics` with `{"names":["kanban","project-management","pmo","vanilla-javascript","html","github-pages","demo"]}` (topics must be lower-case and hyphenated).

Read the repo back with `GET /repos/OWNER/REPO` and check that `description`, `homepage` and `topics` are set.

## 8. Report

Finish with a short summary:

- Repo URL, commit SHA pushed, and the live GitHub Pages URL.
- Result of the latest workflow run (check and deploy jobs).
- Security scan: clean, or the findings and what was decided about each one.
- Anything the user still has to do by hand (for example, steps that were skipped because there was no API access, or the FormSubmit activation).

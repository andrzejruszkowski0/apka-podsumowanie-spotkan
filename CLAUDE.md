# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Solo-dev Polish-language app: turns a meeting recording/transcript into RACI
tasks, sends deadline reminders by email, and keeps a searchable decision
log. Stack, live demo URLs, and the full docs index are in
@README.md — read that first for the big picture; this file only covers
what you'd otherwise get wrong.

This is a live personal deployment with real data (Supabase Postgres,
production Google Sheets), not a throwaway sandbox — be careful with
destructive DB operations and Render deploys.

## Backend (`backend/`)

- Venv already exists at `backend/.venv` (Windows). Run tests with:
  `backend/.venv/Scripts/python.exe -m pytest -q` (73 tests, ~3s, no config
  file needed — defaults apply).
- Ruff is configured in `backend/ruff.toml` (line-length 120, rules E/F/I/W,
  `known-first-party = ["app"]`) and installed from
  `backend/requirements-dev.txt`, not from `requirements.txt`. Lint with
  `backend/.venv/Scripts/python.exe -m ruff check app`. `ruff format` runs
  automatically on edited `backend/**/*.py` via `backend/scripts/format_hook.py`,
  wired as a PostToolUse hook in `.claude/settings.json` (untracked — set it up
  locally if you want the hook). Black is not used. Match the surrounding
  style: 4-space indent, type hints, Polish comments only where they explain a
  non-obvious *why* (a rejected SPEC.md assumption, a Google API quirk, a
  workaround) — not what the code does.
- `app/config.py` is a single pydantic `Settings` class reading `.env`
  (`extra="ignore"`). Comments there explain several non-obvious decisions
  (deprecated Gemini embedding model swap, scheduler double-start risk under
  `--reload`, cross-site cookie requirements) — read them before touching
  related code.
- Structure convention: one package per domain under `app/` (`auth`,
  `people`, `meetings`, `tasks`, `decisions`, `notifications`, `briefing`),
  each with a `router.py`; domain-specific logic lives in sibling files
  (e.g. `people/sync.py` + `people/sheets_client.py`,
  `tasks/sheets_sync.py` + `tasks/sheets_client.py`,
  `meetings/gemini_client.py` + `extraction.py` + `chunking.py`). Follow
  this pattern for new domains rather than growing `router.py` files.

## Frontend (`frontend/`)

React 19 + Vite + TypeScript + Tailwind. `npm run dev` / `npm run build`
(`tsc -b && vite build`) / `npm run lint` (oxlint, not eslint). No test
framework is configured.

## Google integrations — two different auth mechanisms, don't mix them up

- **Gmail** (briefing, task reminders, meeting-summary drafts) uses the
  logged-in user's OAuth token via `app/auth/tokens.py:get_valid_access_token`.
  This app's OAuth consent screen is External, not Google Workspace, so the
  refresh token expires roughly every 7 days in Testing status — see
  OGRANICZENIA.md §2.
- **Google Sheets** (arkusze „Osoby" i „Zadania RACI") uses a **Service
  Account**, not the user's OAuth token — `app/auth/service_account.py`,
  configured via the `GOOGLE_SERVICE_ACCOUNT_JSON` env var. This was a
  deliberate fix (2026-08-02): the Sheets API returned 403 PERMISSION_DENIED
  for every call made from Render, even though the identical user OAuth
  token worked when called directly from a local machine — an unverified
  OAuth app in Testing/Production restricts sensitive-scope API calls from
  server contexts. Do not revert Sheets calls back to the user's OAuth
  token. Full story: GOOGLE_OAUTH_SETUP.md, section „Konto serwisowe do
  Google Sheets".

## Deploy

- Render backend service has **autoDeploy off**. Pushing to `master` does
  **not** trigger a build — a deploy must be triggered explicitly (Render
  dashboard, or the `render-deploy` skill / `mcp__render__trigger_deploy`).
- Build command runs `alembic upgrade head`, so schema migrations apply
  automatically on deploy — write migrations that are safe to run against
  the live database.
- Frontend is deployed separately (Vercel).

## Git

Solo project: commits and pushes go directly to `master`, no branch/PR
workflow. Commit messages are descriptive Polish sentences, no
conventional-commits prefixes.

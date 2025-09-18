# Project Board Workflow (CLI + Agent)

This doc defines how we’ll collaborate using the GitHub Project board (Projects v2) for open‑srma.

## Overview
- You add or update issues on the Project board “Fix and enhance open-srma”.
- Columns we care about: “Todo” and “In Progress”.
- I fetch the latest items from those columns and implement the requested work.

## Auth setup (one time)
- Create a GitHub token with read access to user Projects (Projects v2) and Issues.
  - Classic PAT: scope `project` (read) and `public_repo` (or `repo` if private).
  - Fine‑grained PAT: Account permissions → Projects (Read), and repository read for `ganeshbmc/open-srma`.
- Save it locally (not committed):
  - Add to `.env` as `GH_TOKEN=ghp_xxx`
  - Or export in your shell: `export GH_TOKEN=ghp_xxx`

## Fetching current board items
We provide a small script that reads your user Project board via the GraphQL API and lists items by Status.

Examples:
- List “In Progress” issues:
  - `make project-list STATUS="In Progress"`
- List “Todo” issues:
  - `make project-list STATUS="Todo"`

Notes:
- The Make target sources `.env` automatically. Alternatively run:
  - `python scripts/fetch_project_items.py --user ganeshbmc --project 2 --status "In Progress"`

## Workflow with the Agent
1. You move or add issues to “Todo” or “In Progress” on the board.
2. You ask me to “fetch the current list and act on it”.
3. I run the fetch, summarize, confirm priorities/ordering if needed, and implement.
4. I report back with changes and link to updated issues/PRs.

## Troubleshooting
- If the fetch returns “No project found or access denied”: verify your token scopes include user Projects (v2) read and that `GH_TOKEN` is set in the environment where the command is run.
- Token hygiene:
  - Keep least privilege.
  - Short expiry.
  - Revoke when no longer needed.

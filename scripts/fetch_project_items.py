#!/usr/bin/env python3
"""
Fetch issues from a GitHub Projects v2 board by Status.

Reads GH_TOKEN from environment.

Usage:
  python scripts/fetch_project_items.py --user USER --project 2 --status "In Progress"

Outputs a simple list of issues matching the Status in the board.
"""
import argparse
import json
import os
import sys
import urllib.request
import textwrap


GRAPHQL_ENDPOINT = "https://api.github.com/graphql"


def gql_query(token: str, query: str, variables: dict | None = None) -> dict:
    req = urllib.request.Request(
        GRAPHQL_ENDPOINT,
        data=json.dumps({"query": query, "variables": variables or {}}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "open-srma-cli",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    try:
        return json.loads(body)
    except Exception as e:
        print("Failed to parse GraphQL response", file=sys.stderr)
        print(body[:500], file=sys.stderr)
        raise e


def build_query() -> str:
    # Use variables and paginate items (GraphQL limit is 100)
    return """
query FetchProjectItems($login: String!, $number: Int!, $after: String) {
  user(login: $login) {
    projectV2(number: $number) {
      title
      items(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          content {
            __typename
            ... on Issue { number title url state body repository { nameWithOwner } }
            ... on PullRequest { number title url state body repository { nameWithOwner } }
          }
          fieldValues(first: 50) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { __typename ... on ProjectV2SingleSelectField { name } }
              }
            }
          }
        }
      }
    }
  }
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="List GitHub Project v2 issues by Status")
    ap.add_argument("--user", required=True, help="GitHub username that owns the Project v2 board")
    ap.add_argument("--project", type=int, required=True, help="Project v2 number (from URL)")
    ap.add_argument("--status", default="In Progress", help="Board Status value to filter (default: In Progress)")
    ap.add_argument("--include-prs", action="store_true", help="Also include pull requests (default: issues only)")
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN")
    if not token:
        print("GH_TOKEN is not set in environment", file=sys.stderr)
        return 2

    query = build_query()
    variables = {"login": args.user, "number": args.project, "after": None}
    nodes = []
    title = None
    # Paginate through all items
    while True:
        data = gql_query(token, query, variables)
        if "errors" in data:
            print("GraphQL errors:", file=sys.stderr)
            print(json.dumps(data["errors"], indent=2), file=sys.stderr)
            return 3
        user = (data.get("data") or {}).get("user") or {}
        proj = user.get("projectV2") or {}
        if not proj:
            print("No project found or access denied.", file=sys.stderr)
            return 4
        if title is None:
            title = proj.get("title")
        items = (proj.get("items") or {})
        nodes.extend(items.get("nodes") or [])
        page = items.get("pageInfo") or {}
        if page.get("hasNextPage"):
            variables["after"] = page.get("endCursor")
            continue
        break
    def _norm(s: str) -> str:
        s = (s or "").strip().lower()
        # Normalize common variants like "to do" vs "todo"
        return "".join(ch for ch in s if ch.isalnum())

    want = _norm(args.status)
    out = []
    for it in nodes:
        fvals = ((it.get("fieldValues") or {}).get("nodes")) or []
        status = None
        for n in fvals:
            if n.get("__typename") == "ProjectV2ItemFieldSingleSelectValue" and ((n.get("field") or {}).get("name") or "").lower() == "status":
                status = _norm(n.get("name") or "")
                break
        if status != want:
            continue
        content = it.get("content") or {}
        if content.get("__typename") == "Issue":
            out.append({
                "kind": "Issue",
                "repo": ((content.get("repository") or {}).get("nameWithOwner")),
                "number": content.get("number"),
                "title": content.get("title"),
                "url": content.get("url"),
                "state": content.get("state"),
                "body": content.get("body") or "",
            })
        elif args.include_prs and content.get("__typename") == "PullRequest":
            out.append({
                "kind": "PullRequest",
                "repo": ((content.get("repository") or {}).get("nameWithOwner")),
                "number": content.get("number"),
                "title": content.get("title"),
                "url": content.get("url"),
                "state": content.get("state"),
                "body": content.get("body") or "",
            })

    if not out:
        print(f"No items in \"{args.status}\".")
        return 0

    for r in out:
        prefix = r["repo"] + (" PR#" if r["kind"] == "PullRequest" else "#")
        body = (r.get("body") or "").rstrip()
        if body:
            # Preserve author formatting but indent subsequent lines for readability.
            lines = textwrap.dedent(body).splitlines()
        else:
            lines = ["(no description)"]

        print(f"- {prefix}{r['number']} | {r['title']}")
        print(f"  {r['url']} (state: {r['state']})")
        print(f"  Description: {lines[0] if lines else ''}")
        for extra in lines[1:]:
            print(f"               {extra}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

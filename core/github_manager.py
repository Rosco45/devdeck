# -*- coding: utf-8 -*-
"""GitHub API Integration for DevDeck.
Fetches user repositories, pull requests, issues, and workflow runs via GitHub REST API.
"""
import json
import urllib.request
import urllib.error
import re
import logging

def parse_github_owner_repo(remote_url):
    """Extracts 'owner/repo' from an HTTPS or SSH git remote url."""
    if not remote_url:
        return None, None
    m = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', remote_url)
    if m:
        return m.group(1), m.group(2).replace(".git", "")
    return None, None

def github_request(endpoint, token=None):
    url = f"https://api.github.com{endpoint}" if not endpoint.startswith("https://") else endpoint
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DevDeck-App/1.0"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
            return True, json.loads(data.decode("utf-8")), resp.getcode()
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            msg = err_body.get("message", str(e))
        except Exception:
            msg = str(e)
        return False, {"error": msg}, e.code
    except Exception as e:
        return False, {"error": str(e)}, 500

def get_repo_details(owner, repo, token=None):
    ok, data, code = github_request(f"/repos/{owner}/{repo}", token)
    return data if ok else None

def get_pull_requests(owner, repo, token=None, state="open"):
    ok, data, _ = github_request(f"/repos/{owner}/{repo}/pulls?state={state}&per_page=10", token)
    if not ok or not isinstance(data, list):
        return []
    prs = []
    for p in data:
        prs.append({
            "number": p.get("number"),
            "title": p.get("title"),
            "author": p.get("user", {}).get("login"),
            "state": p.get("state"),
            "created_at": p.get("created_at"),
            "html_url": p.get("html_url"),
            "draft": p.get("draft", False),
            "branch": p.get("head", {}).get("ref")
        })
    return prs

def get_issues(owner, repo, token=None, state="open"):
    ok, data, _ = github_request(f"/repos/{owner}/{repo}/issues?state={state}&per_page=10", token)
    if not ok or not isinstance(data, list):
        return []
    issues = []
    for i in data:
        # Ignore pull requests which are also returned in issues API
        if "pull_request" in i:
            continue
        issues.append({
            "number": i.get("number"),
            "title": i.get("title"),
            "author": i.get("user", {}).get("login"),
            "state": i.get("state"),
            "created_at": i.get("created_at"),
            "html_url": i.get("html_url"),
            "labels": [l.get("name") for l in i.get("labels", [])]
        })
    return issues

def get_actions_runs(owner, repo, token=None):
    ok, data, _ = github_request(f"/repos/{owner}/{repo}/actions/runs?per_page=6", token)
    if not ok or "workflow_runs" not in data:
        return []
    runs = []
    for r in data["workflow_runs"]:
        runs.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "status": r.get("status"),       # "completed", "in_progress", "queued"
            "conclusion": r.get("conclusion"), # "success", "failure", "cancelled"
            "branch": r.get("head_branch"),
            "event": r.get("event"),
            "html_url": r.get("html_url"),
            "created_at": r.get("created_at")
        })
    return runs

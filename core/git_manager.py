# -*- coding: utf-8 -*-
"""Git Manager for local repositories.
Provides Git status, branches, commits, pull, push, stage, commit, and branch switching.
"""
import os
import subprocess
import logging

def _run_git(args, cwd):
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def get_git_info(cwd):
    if not os.path.isdir(os.path.join(cwd, ".git")):
        return {"is_git": False}

    # 1. Current branch
    ok, branch, _ = _run_git(["branch", "--show-current"], cwd)
    if not ok or not branch:
        # Check detached HEAD
        _, branch, _ = _run_git(["rev-parse", "--short", "HEAD"], cwd)

    # 2. Remote URL
    _, remote_url, _ = _run_git(["config", "--get", "remote.origin.url"], cwd)

    # 3. Status porcelain
    ok, status_out, _ = _run_git(["status", "--porcelain=v1"], cwd)
    modified = []
    staged = []
    untracked = []
    if ok and status_out:
        for line in status_out.split("\n"):
            if len(line) >= 3:
                x = line[0]
                y = line[1]
                filename = line[3:].strip()
                if x in ["M", "A", "D", "R", "C"]:
                    staged.append(filename)
                if y in ["M", "D"]:
                    modified.append(filename)
                elif x == "?" and y == "?":
                    untracked.append(filename)

    # 4. Ahead / Behind
    ahead, behind = 0, 0
    ok, counts, _ = _run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"], cwd)
    if ok and counts:
        parts = counts.split()
        if len(parts) == 2:
            try:
                ahead = int(parts[0])
                behind = int(parts[1])
            except ValueError:
                pass

    # 5. Recent commits (last 5)
    commits = []
    ok, log_out, _ = _run_git(["log", "-n", "5", "--pretty=format:%h|%an|%ar|%s"], cwd)
    if ok and log_out:
        for line in log_out.split("\n"):
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })

    # 6. Local branches
    branches = []
    ok, branch_out, _ = _run_git(["branch", "--format=%(refname:short)"], cwd)
    if ok and branch_out:
        branches = [b.strip() for b in branch_out.split("\n") if b.strip()]

    return {
        "is_git": True,
        "branch": branch or "main",
        "remote_url": remote_url or "",
        "clean": len(modified) == 0 and len(staged) == 0 and len(untracked) == 0,
        "modified": modified,
        "staged": staged,
        "untracked": untracked,
        "ahead": ahead,
        "behind": behind,
        "recent_commits": commits,
        "branches": branches
    }

def git_action(action, cwd, extra_args=None):
    if not os.path.isdir(os.path.join(cwd, ".git")):
        return False, "Not a git repository"

    extra_args = extra_args or {}

    if action == "pull":
        ok, out, err = _run_git(["pull"], cwd)
        return ok, out or err
    elif action == "push":
        ok, out, err = _run_git(["push"], cwd)
        return ok, out or err
    elif action == "fetch":
        ok, out, err = _run_git(["fetch"], cwd)
        return ok, out or err
    elif action == "commit":
        msg = extra_args.get("message", "DevDeck auto-commit")
        # Stage all if requested
        if extra_args.get("stage_all", True):
            _run_git(["add", "-A"], cwd)
        ok, out, err = _run_git(["commit", "-m", msg], cwd)
        return ok, out or err
    elif action == "switch_branch":
        target = extra_args.get("branch")
        if not target:
            return False, "Branch name is required"
        ok, out, err = _run_git(["checkout", target], cwd)
        return ok, out or err
    elif action == "create_branch":
        target = extra_args.get("branch")
        if not target:
            return False, "Branch name is required"
        ok, out, err = _run_git(["checkout", "-b", target], cwd)
        return ok, out or err
    elif action == "diff":
        ok, out, err = _run_git(["diff"], cwd)
        return ok, out
    else:
        return False, f"Unknown action: {action}"

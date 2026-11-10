# -*- coding: utf-8 -*-
"""Docker and Docker Compose Integration.
Lists containers, manages services for projects with compose files, and handles lifecycle actions.
"""
import json
import subprocess
import os

def is_docker_available():
    try:
        res = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=3
        )
        return res.returncode == 0, res.stderr.strip()
    except FileNotFoundError:
        return False, "Docker CLI not found on this system"
    except Exception as e:
        return False, str(e)

def list_containers():
    available, err = is_docker_available()
    if not available:
        return False, [], err

    try:
        res = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode != 0:
            return False, [], res.stderr.strip()

        containers = []
        for line in res.stdout.strip().split("\n"):
            if line.strip():
                try:
                    c = json.loads(line)
                    containers.append({
                        "id": c.get("ID", ""),
                        "names": c.get("Names", ""),
                        "image": c.get("Image", ""),
                        "status": c.get("Status", ""),
                        "state": c.get("State", ""),
                        "ports": c.get("Ports", "")
                    })
                except Exception:
                    pass
        return True, containers, ""
    except Exception as e:
        return False, [], str(e)

def run_compose_command(project_path, action):
    available, err = is_docker_available()
    if not available:
        return False, err

    cmd = ["docker", "compose"]
    if action == "up":
        cmd += ["up", "-d"]
    elif action == "down":
        cmd += ["down"]
    elif action == "restart":
        cmd += ["restart"]
    elif action == "ps":
        cmd += ["ps", "--format", "json"]
    elif action == "logs":
        cmd += ["logs", "--tail", "50"]
    else:
        return False, f"Unsupported compose action: {action}"

    try:
        res = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        return res.returncode == 0, res.stdout or res.stderr
    except Exception as e:
        return False, str(e)

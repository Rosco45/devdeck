# -*- coding: utf-8 -*-
"""DevDeck Configuration and persistence manager.
Stores projects, settings, and environments in JSON format with safe atomic writes.
"""
import os
import json
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    "host": "127.0.0.1",
    "port": 8888,
    "theme": "dark",
    "default_scan_dir": os.path.expanduser("~"),
    "github_token": "",
    "max_log_lines": 1000,
    "auto_open_browser": True
}

def safe_read_json(filepath, default):
    if not os.path.isfile(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading {filepath}: {e}")
        return default

def safe_write_json(filepath, data):
    tmp_path = filepath + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
        return True
    except Exception as e:
        logging.error(f"Error writing {filepath}: {e}")
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False

def get_settings():
    settings = safe_read_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    # Ensure all defaults exist
    for k, v in DEFAULT_SETTINGS.items():
        if k not in settings:
            settings[k] = v
    return settings

def update_settings(new_settings):
    current = get_settings()
    current.update(new_settings)
    safe_write_json(SETTINGS_FILE, current)
    return current

def get_projects():
    return safe_read_json(PROJECTS_FILE, [])

def save_projects(projects):
    return safe_write_json(PROJECTS_FILE, projects)

def get_project(project_id):
    projects = get_projects()
    for p in projects:
        if p.get("id") == project_id:
            return p
    return None

def upsert_project(project_data):
    projects = get_projects()
    pid = project_data.get("id")
    found = False
    for i, p in enumerate(projects):
        if p.get("id") == pid:
            projects[i] = project_data
            found = True
            break
    if not found:
        projects.append(project_data)
    save_projects(projects)
    return project_data

def delete_project(project_id):
    projects = get_projects()
    new_projects = [p for p in projects if p.get("id") != project_id]
    save_projects(new_projects)
    return len(new_projects) != len(projects)

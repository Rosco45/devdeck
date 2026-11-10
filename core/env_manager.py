# -*- coding: utf-8 -*-
"""Environment Variables (.env) Manager and Inspector.
Reads, compares (.env vs .env.example), masks secrets, and writes project environments.
"""
import os
import shutil
import re

SENSITIVE_KEY_PATTERNS = [
    r'secret', r'password', r'token', r'key', r'auth', r'credential', r'private'
]

def is_sensitive(key_name):
    low = key_name.lower()
    return any(re.search(p, low) for p in SENSITIVE_KEY_PATTERNS)

def list_env_files(project_path):
    candidates = [
        ".env", ".env.local", ".env.development", ".env.production",
        ".env.test", ".env.example", ".env.sample"
    ]
    found = []
    for c in candidates:
        fp = os.path.join(project_path, c)
        if os.path.isfile(fp):
            found.append(c)
    return found

def parse_env_file(filepath):
    """Parses an env file and returns a list of items preserving comments and structure."""
    if not os.path.isfile(filepath):
        return []

    items = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f):
            stripped = line.strip()
            if not stripped:
                items.append({"type": "blank", "line": line})
            elif stripped.startswith("#"):
                items.append({"type": "comment", "comment": stripped[1:].strip(), "line": line})
            elif "=" in stripped:
                key, val = stripped.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Remove quotes if enclosed
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                items.append({
                    "type": "variable",
                    "key": key,
                    "value": val,
                    "is_sensitive": is_sensitive(key)
                })
            else:
                items.append({"type": "raw", "line": line})
    return items

def get_env_dict(filepath):
    items = parse_env_file(filepath)
    return {it["key"]: it["value"] for it in items if it.get("type") == "variable"}

def compare_env_with_example(project_path):
    """Compares .env with .env.example to find missing or extra variables."""
    main_env = os.path.join(project_path, ".env")
    if not os.path.isfile(main_env):
        main_env = os.path.join(project_path, ".env.local")

    example_env = os.path.join(project_path, ".env.example")
    if not os.path.isfile(example_env):
        example_env = os.path.join(project_path, ".env.sample")

    cur_vars = get_env_dict(main_env) if os.path.isfile(main_env) else {}
    ex_vars = get_env_dict(example_env) if os.path.isfile(example_env) else {}

    missing_in_cur = [k for k in ex_vars if k not in cur_vars]
    extra_in_cur = [k for k in cur_vars if k not in ex_vars]

    return {
        "has_env": os.path.isfile(main_env),
        "has_example": os.path.isfile(example_env),
        "total_variables": len(cur_vars),
        "missing_keys": missing_in_cur,
        "extra_keys": extra_in_cur
    }

def save_env_file(filepath, variables):
    """Saves a dictionary of key-values to a .env file with automatic backup."""
    # Create backup if exists
    if os.path.isfile(filepath):
        shutil.copy2(filepath, filepath + ".bak")

    lines = []
    lines.append(f"# DevDeck generated environment file\n")
    for k, v in variables.items():
        k = k.strip()
        v = str(v).strip()
        # Quote if contains spaces or special characters
        if " " in v or "#" in v or "\n" in v:
            lines.append(f'{k}="{v}"\n')
        else:
            lines.append(f'{k}={v}\n')

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True

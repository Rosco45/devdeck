# -*- coding: utf-8 -*-
"""Project Stack & Configuration Auto-Detector.
Inspects a directory and determines its tech stack, framework, package manager,
suggested dev/prod/test commands, and default ports.
"""
import os
import json
import re

FRAMEWORK_PORTS = {
    "Next.js": 3000,
    "Vite": 5173,
    "React (CRA)": 3000,
    "Vue (CLI)": 8080,
    "Nuxt": 3000,
    "Astro": 4321,
    "SvelteKit": 5173,
    "Remix": 3000,
    "Angular": 4200,
    "Django": 8000,
    "FastAPI": 8000,
    "Flask": 5000,
    "Express": 3000,
    "NestJS": 3000,
    "Laravel": 8000,
    "Spring Boot": 8080,
    "Static HTML": 8000,
}

def detect_project(directory):
    """Analyzes a project directory and returns a structured metadata dictionary."""
    if not os.path.isdir(directory):
        return None

    name = os.path.basename(os.path.abspath(directory))
    stack = []
    framework = "Custom / Unknown"
    pkg_manager = "none"
    dev_cmd = ""
    prod_cmd = ""
    test_cmd = ""
    build_cmd = ""
    suggested_port = None
    scripts = {}
    is_git = os.path.isdir(os.path.join(directory, ".git"))
    has_docker = os.path.isfile(os.path.join(directory, "docker-compose.yml")) or \
                 os.path.isfile(os.path.join(directory, "compose.yaml")) or \
                 os.path.isfile(os.path.join(directory, "Dockerfile"))
    has_env = os.path.isfile(os.path.join(directory, ".env")) or \
              os.path.isfile(os.path.join(directory, ".env.local"))

    # 1. Check Node.js (package.json)
    pkg_json_path = os.path.join(directory, "package.json")
    if os.path.isfile(pkg_json_path):
        stack.append("Node.js")
        # Detect package manager
        if os.path.isfile(os.path.join(directory, "pnpm-lock.yaml")):
            pkg_manager = "pnpm"
        elif os.path.isfile(os.path.join(directory, "yarn.lock")):
            pkg_manager = "yarn"
        elif os.path.isfile(os.path.join(directory, "bun.lockb")) or os.path.isfile(os.path.join(directory, "bun.lock")):
            pkg_manager = "bun"
        else:
            pkg_manager = "npm"

        try:
            with open(pkg_json_path, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
            scripts = pkg_data.get("scripts", {})
            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

            # Framework detection
            if "next" in deps:
                framework = "Next.js"
            elif "vite" in deps:
                framework = "Vite"
            elif "nuxt" in deps:
                framework = "Nuxt"
            elif "astro" in deps:
                framework = "Astro"
            elif "@sveltejs/kit" in deps:
                framework = "SvelteKit"
            elif "@remix-run/react" in deps:
                framework = "Remix"
            elif "@angular/core" in deps:
                framework = "Angular"
            elif "@nestjs/core" in deps:
                framework = "NestJS"
            elif "react" in deps:
                framework = "React"
            elif "vue" in deps:
                framework = "Vue"
            elif "express" in deps:
                framework = "Express"

            # Commands detection
            run_prefix = f"{pkg_manager} run " if pkg_manager in ["npm", "pnpm", "yarn", "bun"] else "npm run "
            
            if "dev" in scripts:
                dev_cmd = f"{run_prefix}dev"
            elif "start" in scripts and "build" not in scripts:
                dev_cmd = f"{run_prefix}start"
            elif "serve" in scripts:
                dev_cmd = f"{run_prefix}serve"

            if "build" in scripts:
                build_cmd = f"{run_prefix}build"
                if "start" in scripts:
                    prod_cmd = f"{run_prefix}build && {run_prefix}start"
                else:
                    prod_cmd = f"{run_prefix}build"
            elif "start" in scripts:
                prod_cmd = f"{run_prefix}start"

            if "test" in scripts:
                test_cmd = f"{run_prefix}test"

            suggested_port = FRAMEWORK_PORTS.get(framework)

        except Exception:
            pass

    # 2. Check Python
    py_indicators = [
        "requirements.txt", "pyproject.toml", "Pipfile", "setup.py",
        "manage.py", "app.py", "main.py", "wsgi.py"
    ]
    has_python = any(os.path.isfile(os.path.join(directory, f)) for f in py_indicators)
    if has_python:
        stack.append("Python")
        # Check for virtualenv
        py_exec = "python3"
        for venv_dir in [".venv", "venv", "env"]:
            candidate = os.path.join(directory, venv_dir, "bin", "python")
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                py_exec = f"{venv_dir}/bin/python"
                break

        # Frameworks
        if os.path.isfile(os.path.join(directory, "manage.py")):
            framework = "Django"
            dev_cmd = dev_cmd or f"{py_exec} manage.py runserver"
            prod_cmd = prod_cmd or f"{py_exec} -m gunicorn myproject.wsgi:application"
            test_cmd = test_cmd or f"{py_exec} manage.py test"
            suggested_port = 8000
        elif os.path.isfile(os.path.join(directory, "main.py")) or os.path.isfile(os.path.join(directory, "app.py")):
            entry_file = "main.py" if os.path.isfile(os.path.join(directory, "main.py")) else "app.py"
            try:
                with open(os.path.join(directory, entry_file), "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(2048)
                if "fastapi" in content.lower():
                    framework = "FastAPI"
                    module_name = entry_file.replace(".py", "")
                    dev_cmd = dev_cmd or f"{py_exec} -m uvicorn {module_name}:app --reload --port 8000"
                    prod_cmd = prod_cmd or f"{py_exec} -m uvicorn {module_name}:app --host 0.0.0.0 --port 8000"
                    suggested_port = 8000
                elif "flask" in content.lower():
                    framework = "Flask"
                    dev_cmd = dev_cmd or f"{py_exec} {entry_file}"
                    suggested_port = 5000
                elif "streamlit" in content.lower():
                    framework = "Streamlit"
                    dev_cmd = dev_cmd or f"{py_exec} -m streamlit run {entry_file}"
                    suggested_port = 8501
                else:
                    if not dev_cmd:
                        dev_cmd = f"{py_exec} {entry_file}"
            except Exception:
                if not dev_cmd:
                    dev_cmd = f"{py_exec} {entry_file}"

    # 3. Check Go
    if os.path.isfile(os.path.join(directory, "go.mod")):
        stack.append("Go")
        framework = "Go"
        dev_cmd = dev_cmd or "go run ."
        prod_cmd = prod_cmd or "go build -o server && ./server"
        test_cmd = test_cmd or "go test ./..."
        suggested_port = suggested_port or 8080

    # 4. Check Rust
    if os.path.isfile(os.path.join(directory, "Cargo.toml")):
        stack.append("Rust")
        framework = "Rust"
        dev_cmd = dev_cmd or "cargo run"
        prod_cmd = prod_cmd or "cargo run --release"
        test_cmd = test_cmd or "cargo test"
        suggested_port = suggested_port or 8080

    # 5. Check Static HTML / Web
    if not stack and os.path.isfile(os.path.join(directory, "index.html")):
        stack.append("HTML/JS")
        framework = "Static Web"
        dev_cmd = "python3 -m http.server 3000"
        prod_cmd = "python3 -m http.server 8080"
        suggested_port = 3000

    # 6. Parse port from .env or .env.local if present
    for env_name in [".env.local", ".env"]:
        env_file = os.path.join(directory, env_name)
        if os.path.isfile(env_file):
            try:
                with open(env_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("PORT=") or line.startswith("VITE_PORT="):
                            parts = line.split("=", 1)
                            if len(parts) == 2 and parts[1].strip().isdigit():
                                suggested_port = int(parts[1].strip())
                                break
            except Exception:
                pass

    # 7. Check Git Remote
    git_remote = None
    git_branch = None
    if is_git:
        git_config_path = os.path.join(directory, ".git", "config")
        if os.path.isfile(git_config_path):
            try:
                with open(git_config_path, "r", encoding="utf-8", errors="ignore") as f:
                    cfg = f.read()
                    m = re.search(r'url\s*=\s*(.+)', cfg)
                    if m:
                        git_remote = m.group(1).strip()
            except Exception:
                pass
        head_path = os.path.join(directory, ".git", "HEAD")
        if os.path.isfile(head_path):
            try:
                with open(head_path, "r", encoding="utf-8", errors="ignore") as f:
                    head_content = f.read().strip()
                    if head_content.startswith("ref: refs/heads/"):
                        git_branch = head_content.replace("ref: refs/heads/", "")
            except Exception:
                pass

    return {
        "id": re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower()),
        "name": name,
        "path": os.path.abspath(directory),
        "stack": stack or ["Generic"],
        "framework": framework,
        "pkg_manager": pkg_manager,
        "dev_cmd": dev_cmd,
        "prod_cmd": prod_cmd,
        "build_cmd": build_cmd,
        "test_cmd": test_cmd,
        "custom_cmd": "",
        "port": suggested_port or 3000,
        "is_git": is_git,
        "git_remote": git_remote,
        "git_branch": git_branch,
        "has_docker": has_docker,
        "has_env": has_env,
        "scripts": scripts
    }

def scan_directory_for_projects(root_dir, max_depth=1):
    """Scans root_dir up to max_depth and returns a list of detected projects."""
    found = []
    if not os.path.isdir(root_dir):
        return found

    ignored_names = {
        ".git", "node_modules", ".cache", ".local", ".config", ".npm",
        "snap", ".vscode", "venv", ".venv", "env", "dist", "build",
        "Téléchargements", "Bureau", "Documents", "Images", "Musique",
        "Vidéos", "Modèles", "Public", "Android", "android-studio"
    }

    try:
        entries = sorted(os.listdir(root_dir))
    except Exception:
        return found

    for entry in entries:
        if entry in ignored_names or entry.startswith("."):
            continue
        full_path = os.path.join(root_dir, entry)
        if os.path.isdir(full_path):
            proj = detect_project(full_path)
            # Only consider it a project if it has recognized files
            if proj and (proj["is_git"] or proj["stack"] != ["Generic"] or proj["has_docker"]):
                found.append(proj)

    return found

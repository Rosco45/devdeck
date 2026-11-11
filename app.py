# -*- coding: utf-8 -*-
"""DevDeck Application Server.
Main entry point serving the web dashboard, REST APIs, and real-time SSE log streams.
"""
import json
import logging
import os
import queue
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core import config
from core import detector
from core import docker_manager
from core import env_manager
from core import git_manager
from core import github_manager
from core import port_manager
from core import tools_manager
from core import tunnel_manager
from core.process_manager import ProcessManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}

class DevDeckHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Reduce noisy static file logs, keep API logs
        if "/api/" in str(args[0]):
            logging.info("%s - %s", self.address_string(), format % args)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def read_json_body(self):
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw = self.rfile.read(content_len).decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # -------------------------------------------------------------------
        # SSE Stream: /api/projects/{id}/logs/stream
        # -------------------------------------------------------------------
        stream_match = re.match(r"^/api/projects/([^/]+)/logs/stream$", path)
        if stream_match:
            project_id = stream_match.group(1)
            self.handle_sse_logs(project_id)
            return

        # -------------------------------------------------------------------
        # REST APIs
        # -------------------------------------------------------------------
        if path == "/api/projects":
            projects = config.get_projects()
            statuses = ProcessManager.get_instance().get_all_statuses()
            tunnels = tunnel_manager.TunnelManager.get_instance().get_all_tunnels()
            for p in projects:
                pid = p.get("id")
                p["runtime"] = statuses.get(pid, {
                    "status": "stopped",
                    "pid": None,
                    "uptime_seconds": 0,
                    "ready": False,
                    "ready_time_ms": None,
                    "cpu_percent": 0.0,
                    "ram_mb": 0.0,
                    "crash_diagnosis": None
                })
                p["tunnel"] = tunnels.get(pid)
            self.send_json(projects)

        elif path == "/api/workspaces":
            workspaces = config.get_workspaces()
            self.send_json(workspaces)

        elif path == "/api/system/network-info":
            net_info = port_manager.get_network_info()
            self.send_json(net_info)

        elif path.startswith("/api/projects/scan"):
            scan_dir = query.get("path", [config.get_settings().get("default_scan_dir", os.path.expanduser("~"))])[0]
            scan_dir = os.path.expanduser(scan_dir)
            results = detector.scan_directory_for_projects(scan_dir)
            self.send_json({"scanned_directory": scan_dir, "projects": results})

        elif path == "/api/ports":
            ports = port_manager.scan_listening_ports()
            self.send_json(ports)

        elif path == "/api/git/info":
            proj_path = query.get("path", [""])[0]
            if not proj_path or not os.path.isdir(proj_path):
                self.send_json({"error": "Invalid directory"}, 400)
                return
            info = git_manager.get_git_info(proj_path)
            self.send_json(info)

        elif path == "/api/github/overview":
            remote_url = query.get("remote", [""])[0]
            owner, repo = github_manager.parse_github_owner_repo(remote_url)
            if not owner or not repo:
                self.send_json({"error": "No valid GitHub remote URL"}, 400)
                return
            token = config.get_settings().get("github_token") or os.environ.get("GITHUB_TOKEN")
            prs = github_manager.get_pull_requests(owner, repo, token)
            issues = github_manager.get_issues(owner, repo, token)
            actions = github_manager.get_actions_runs(owner, repo, token)
            self.send_json({
                "owner": owner,
                "repo": repo,
                "pull_requests": prs,
                "issues": issues,
                "actions": actions
            })

        elif path == "/api/env":
            proj_path = query.get("path", [""])[0]
            if not proj_path or not os.path.isdir(proj_path):
                self.send_json({"error": "Invalid directory"}, 400)
                return
            files = env_manager.list_env_files(proj_path)
            comparison = env_manager.compare_env_with_example(proj_path)
            self.send_json({"files": files, "comparison": comparison})

        elif path == "/api/env/file":
            proj_path = query.get("path", [""])[0]
            file_name = query.get("file", [".env"])[0]
            full_path = os.path.join(proj_path, file_name)
            if not os.path.isfile(full_path):
                self.send_json({"error": "File not found"}, 404)
                return
            parsed_items = env_manager.parse_env_file(full_path)
            self.send_json({"items": parsed_items, "path": full_path})

        elif path == "/api/docker/containers":
            ok, containers, err = docker_manager.list_containers()
            self.send_json({"available": ok, "containers": containers, "error": err})

        elif path == "/api/tools/tokens":
            tokens = tools_manager.generate_tokens()
            self.send_json(tokens)

        elif path == "/api/workspaces":
            if not body.get("name") or not body.get("project_ids"):
                self.send_json({"error": "Name and project_ids are required"}, 400)
                return
            if not body.get("id"):
                body["id"] = re.sub(r'[^a-zA-Z0-9_-]', '_', body["name"].lower())
            saved = config.upsert_workspace(body)
            self.send_json({"success": True, "workspace": saved})

        elif re.match(r"^/api/workspaces/([^/]+)/start$", path):
            wid = re.match(r"^/api/workspaces/([^/]+)/start$", path).group(1)
            workspaces = config.get_workspaces()
            target_ws = next((w for w in workspaces if w.get("id") == wid), None)
            if not target_ws:
                self.send_json({"error": "Workspace not found"}, 404)
                return

            def _start_ws():
                for pid in target_ws.get("project_ids", []):
                    p = config.get_project(pid)
                    if p:
                        ProcessManager.get_instance().start_project(p, mode="dev")
                        time.sleep(0.8)

            threading.Thread(target=_start_ws, daemon=True).start()
            self.send_json({"success": True, "message": f"Démarrage du groupe {target_ws.get('name')} en cours..."})

        elif re.match(r"^/api/workspaces/([^/]+)/stop$", path):
            wid = re.match(r"^/api/workspaces/([^/]+)/stop$", path).group(1)
            workspaces = config.get_workspaces()
            target_ws = next((w for w in workspaces if w.get("id") == wid), None)
            if not target_ws:
                self.send_json({"error": "Workspace not found"}, 404)
                return

            for pid in target_ws.get("project_ids", []):
                ProcessManager.get_instance().stop_project(pid)
            self.send_json({"success": True, "message": f"Groupe {target_ws.get('name')} arrêté"})

        elif re.match(r"^/api/projects/([^/]+)/tunnel/start$", path):
            pid = re.match(r"^/api/projects/([^/]+)/tunnel/start$", path).group(1)
            project = config.get_project(pid)
            if not project or not project.get("port"):
                self.send_json({"error": "Project or port not found"}, 400)
                return
            ok, url_or_err = tunnel_manager.TunnelManager.get_instance().start_tunnel(pid, project["port"])
            self.send_json({"success": ok, "url": url_or_err if ok else None, "error": None if ok else url_or_err})

        elif re.match(r"^/api/projects/([^/]+)/tunnel/stop$", path):
            pid = re.match(r"^/api/projects/([^/]+)/tunnel/stop$", path).group(1)
            ok, msg = tunnel_manager.TunnelManager.get_instance().stop_tunnel(pid)
            self.send_json({"success": ok, "message": msg})

        elif re.match(r"^/api/projects/([^/]+)/fix$", path):
            pid = re.match(r"^/api/projects/([^/]+)/fix$", path).group(1)
            project = config.get_project(pid)
            if not project:
                self.send_json({"error": "Project not found"}, 404)
                return
            proc = ProcessManager.get_instance().get_process(pid)
            diag = proc.crash_diagnosis if proc else None
            if not diag or not diag.get("fix_command"):
                self.send_json({"error": "No fix command available"}, 400)
                return

            cmd = diag["fix_command"]
            if cmd.startswith("kill_port"):
                parts = cmd.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    ok, msg = port_manager.kill_port(int(parts[1]), force=True)
                    self.send_json({"success": ok, "output": msg})
                    return

            try:
                res = subprocess.run(
                    ["/bin/bash", "-c", cmd],
                    cwd=project["path"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                self.send_json({
                    "success": res.returncode == 0,
                    "output": res.stdout or res.stderr
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)

        elif path == "/api/tools/db-ping":
            host = body.get("host", "127.0.0.1")
            port = body.get("port", 5432)
            db_type = body.get("db_type", "postgres")
            res = tools_manager.ping_database(host, port, db_type)
            self.send_json(res)

        elif path == "/api/tools/generate-config":
            config_type = body.get("config_type", "gitignore")
            stack = body.get("stack", "Node.js")
            proj_path = body.get("path", "")
            env_file = os.path.join(proj_path, ".env") if proj_path else None
            content = tools_manager.generate_config_file(config_type, stack, env_file)
            self.send_json({"success": True, "content": content})

        elif path == "/api/settings":
            self.send_json(config.get_settings())

        elif path.startswith("/api/projects/") and path.endswith("/logs"):
            m = re.match(r"^/api/projects/([^/]+)/logs$", path)
            if m:
                pid = m.group(1)
                logs = ProcessManager.get_instance().get_logs(pid)
                self.send_json({"logs": logs})
            else:
                self.send_json({"error": "Invalid route"}, 404)

        # -------------------------------------------------------------------
        # Static files serving from web/
        # -------------------------------------------------------------------
        else:
            self.serve_static(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        if path == "/api/projects":
            # Add or update project
            if not body.get("name") or not body.get("path"):
                self.send_json({"error": "Project name and path are required"}, 400)
                return
            if not body.get("id"):
                name = body["name"]
                body["id"] = re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
            saved = config.upsert_project(body)
            self.send_json({"success": True, "project": saved})

        elif path == "/api/projects/import-scanned":
            # Bulk import scanned projects
            to_import = body.get("projects", [])
            for p in to_import:
                config.upsert_project(p)
            self.send_json({"success": True, "count": len(to_import)})

        elif re.match(r"^/api/projects/([^/]+)/start$", path):
            pid = re.match(r"^/api/projects/([^/]+)/start$", path).group(1)
            project = config.get_project(pid)
            if not project:
                self.send_json({"error": "Project not found"}, 404)
                return
            mode = body.get("mode", "dev")
            custom_cmd = body.get("custom_cmd", "")
            ok, msg = ProcessManager.get_instance().start_project(project, mode, custom_cmd)
            self.send_json({"success": ok, "message": msg})

        elif re.match(r"^/api/projects/([^/]+)/stop$", path):
            pid = re.match(r"^/api/projects/([^/]+)/stop$", path).group(1)
            ok, msg = ProcessManager.get_instance().stop_project(pid)
            self.send_json({"success": ok, "message": msg})

        elif re.match(r"^/api/projects/([^/]+)/restart$", path):
            pid = re.match(r"^/api/projects/([^/]+)/restart$", path).group(1)
            project = config.get_project(pid)
            if not project:
                self.send_json({"error": "Project not found"}, 404)
                return
            mode = body.get("mode", "dev")
            ok, msg = ProcessManager.get_instance().restart_project(project, mode)
            self.send_json({"success": ok, "message": msg})

        elif path == "/api/ports/kill":
            port = body.get("port")
            force = body.get("force", False)
            if not port:
                self.send_json({"error": "Port is required"}, 400)
                return
            ok, msg = port_manager.kill_port(port, force)
            self.send_json({"success": ok, "message": msg})

        elif path == "/api/git/action":
            action = body.get("action")
            cwd = body.get("path")
            extra = body.get("extra", {})
            if not cwd or not action:
                self.send_json({"error": "Path and action are required"}, 400)
                return
            ok, output = git_manager.git_action(action, cwd, extra)
            self.send_json({"success": ok, "output": output})

        elif path == "/api/env/file":
            proj_path = body.get("path")
            file_name = body.get("file", ".env")
            variables = body.get("variables", {})
            full_path = os.path.join(proj_path, file_name)
            ok = env_manager.save_env_file(full_path, variables)
            self.send_json({"success": ok})

        elif path == "/api/docker/compose":
            proj_path = body.get("path")
            action = body.get("action")
            ok, out = docker_manager.run_compose_command(proj_path, action)
            self.send_json({"success": ok, "output": out})

        elif path == "/api/tools/http":
            method = body.get("method", "GET")
            url = body.get("url")
            headers = body.get("headers", {})
            req_body = body.get("body")
            res = tools_manager.execute_http_request(method, url, headers, req_body)
            self.send_json(res)

        elif path == "/api/tools/jwt":
            token = body.get("token", "")
            res = tools_manager.decode_jwt(token)
            self.send_json(res)

        elif path == "/api/tools/hashes":
            text = body.get("text", "")
            res = tools_manager.compute_hashes(text)
            self.send_json(res)

        elif path == "/api/workspaces":
            if not body.get("name") or not body.get("project_ids"):
                self.send_json({"error": "Name and project_ids are required"}, 400)
                return
            if not body.get("id"):
                body["id"] = re.sub(r'[^a-zA-Z0-9_-]', '_', body["name"].lower())
            saved = config.upsert_workspace(body)
            self.send_json({"success": True, "workspace": saved})

        elif re.match(r"^/api/workspaces/([^/]+)/start$", path):
            wid = re.match(r"^/api/workspaces/([^/]+)/start$", path).group(1)
            workspaces = config.get_workspaces()
            target_ws = next((w for w in workspaces if w.get("id") == wid), None)
            if not target_ws:
                self.send_json({"error": "Workspace not found"}, 404)
                return

            def _start_ws():
                for pid in target_ws.get("project_ids", []):
                    p = config.get_project(pid)
                    if p:
                        ProcessManager.get_instance().start_project(p, mode="dev")
                        time.sleep(0.8)

            threading.Thread(target=_start_ws, daemon=True).start()
            self.send_json({"success": True, "message": f"Démarrage du groupe {target_ws.get('name')} en cours..."})

        elif re.match(r"^/api/workspaces/([^/]+)/stop$", path):
            wid = re.match(r"^/api/workspaces/([^/]+)/stop$", path).group(1)
            workspaces = config.get_workspaces()
            target_ws = next((w for w in workspaces if w.get("id") == wid), None)
            if not target_ws:
                self.send_json({"error": "Workspace not found"}, 404)
                return

            for pid in target_ws.get("project_ids", []):
                ProcessManager.get_instance().stop_project(pid)
            self.send_json({"success": True, "message": f"Groupe {target_ws.get('name')} arrêté"})

        elif re.match(r"^/api/projects/([^/]+)/tunnel/start$", path):
            pid = re.match(r"^/api/projects/([^/]+)/tunnel/start$", path).group(1)
            project = config.get_project(pid)
            if not project or not project.get("port"):
                self.send_json({"error": "Project or port not found"}, 400)
                return
            ok, url_or_err = tunnel_manager.TunnelManager.get_instance().start_tunnel(pid, project["port"])
            self.send_json({"success": ok, "url": url_or_err if ok else None, "error": None if ok else url_or_err})

        elif re.match(r"^/api/projects/([^/]+)/tunnel/stop$", path):
            pid = re.match(r"^/api/projects/([^/]+)/tunnel/stop$", path).group(1)
            ok, msg = tunnel_manager.TunnelManager.get_instance().stop_tunnel(pid)
            self.send_json({"success": ok, "message": msg})

        elif re.match(r"^/api/projects/([^/]+)/fix$", path):
            pid = re.match(r"^/api/projects/([^/]+)/fix$", path).group(1)
            project = config.get_project(pid)
            if not project:
                self.send_json({"error": "Project not found"}, 404)
                return
            proc = ProcessManager.get_instance().get_process(pid)
            diag = proc.crash_diagnosis if proc else None
            if not diag or not diag.get("fix_command"):
                self.send_json({"error": "No fix command available"}, 400)
                return

            cmd = diag["fix_command"]
            if cmd.startswith("kill_port"):
                parts = cmd.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    ok, msg = port_manager.kill_port(int(parts[1]), force=True)
                    self.send_json({"success": ok, "output": msg})
                    return

            try:
                res = subprocess.run(
                    ["/bin/bash", "-c", cmd],
                    cwd=project["path"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                self.send_json({
                    "success": res.returncode == 0,
                    "output": res.stdout or res.stderr
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)

        elif path == "/api/tools/db-ping":
            host = body.get("host", "127.0.0.1")
            port = body.get("port", 5432)
            db_type = body.get("db_type", "postgres")
            res = tools_manager.ping_database(host, port, db_type)
            self.send_json(res)

        elif path == "/api/tools/generate-config":
            config_type = body.get("config_type", "gitignore")
            stack = body.get("stack", "Node.js")
            proj_path = body.get("path", "")
            env_file = os.path.join(proj_path, ".env") if proj_path else None
            content = tools_manager.generate_config_file(config_type, stack, env_file)
            self.send_json({"success": True, "content": content})

        elif path == "/api/settings":
            updated = config.update_settings(body)
            self.send_json({"success": True, "settings": updated})

        elif path == "/api/system/open-folder":
            p = body.get("path")
            if p and os.path.exists(p):
                subprocess.Popen(["xdg-open", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Path does not exist"}, 400)

        elif path == "/api/system/open-editor":
            p = body.get("path")
            if p and os.path.exists(p):
                subprocess.Popen(["code", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Path does not exist"}, 400)

        else:
            self.send_json({"error": f"Unknown POST route: {path}"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        m_proj = re.match(r"^/api/projects/([^/]+)$", path)
        if m_proj:
            pid = m_proj.group(1)
            # Stop if running
            ProcessManager.get_instance().stop_project(pid)
            config.delete_project(pid)
            self.send_json({"success": True})
            return

        m_ws = re.match(r"^/api/workspaces/([^/]+)$", path)
        if m_ws:
            wid = m_ws.group(1)
            config.delete_workspace(wid)
            self.send_json({"success": True})
            return

        m_logs = re.match(r"^/api/projects/([^/]+)/logs$", path)
        if m_logs:
            pid = m_logs.group(1)
            ProcessManager.get_instance().clear_logs(pid)
            self.send_json({"success": True})
            return

        self.send_json({"error": "Not found"}, 404)

    def handle_sse_logs(self, project_id):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        log_queue = queue.Queue()
        proc = ProcessManager.get_instance().get_process(project_id)
        if proc:
            proc.add_listener(log_queue)
            # Send initial backlog
            for chunk in proc.logs:
                # SSE format: data: JSON_PAYLOAD\n\n
                payload = json.dumps({"type": "log", "chunk": chunk})
                self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
            self.wfile.flush()

        last_keepalive = time.time()
        try:
            while True:
                try:
                    chunk = log_queue.get(timeout=1.0)
                    payload = json.dumps({"type": "log", "chunk": chunk})
                    self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # Send keep-alive every 15s to keep connection alive
                    if time.time() - last_keepalive > 15:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                        last_keepalive = time.time()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            if proc:
                proc.remove_listener(log_queue)

    def serve_static(self, path):
        if path in ["", "/"]:
            path = "/index.html"

        # Sanitize path
        clean_path = os.path.normpath(path).lstrip("/")
        full_path = os.path.join(BASE_DIR, "web", clean_path)

        if not os.path.isfile(full_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        ext = os.path.splitext(full_path)[1].lower()
        mime = MIME_TYPES.get(ext, "application/octet-stream")

        try:
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))


def run_server():
    settings = config.get_settings()
    host = settings.get("host", "127.0.0.1")
    port = int(settings.get("port", 8888))

    # Fallback to next port if occupied
    attempts = 0
    while attempts < 10:
        try:
            server = ThreadingHTTPServer((host, port), DevDeckHandler)
            break
        except OSError:
            port += 1
            attempts += 1

    url = f"http://{host}:{port}"
    print(f"\n" + "=" * 60)
    print(f"🚀  DevDeck is running at: {url}")
    print(f"    Press Ctrl+C to stop the dashboard server.")
    print("=" * 60 + "\n")

    # Auto scan home projects if empty on first launch
    current_projects = config.get_projects()
    if not current_projects:
        print("🔍 First launch: scanning home directory for existing projects...")
        scanned = detector.scan_directory_for_projects(os.path.expanduser("~"))
        if scanned:
            print(f"✨ Found {len(scanned)} projects! Adding to DevDeck...")
            for p in scanned:
                config.upsert_project(p)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down DevDeck...")
        # Stop all running child processes cleanly
        statuses = ProcessManager.get_instance().get_all_statuses()
        for pid, p in statuses.items():
            if p["status"] == "running":
                ProcessManager.get_instance().stop_project(pid)
        server.server_close()
        print("DevDeck stopped safely.")

if __name__ == "__main__":
    run_server()

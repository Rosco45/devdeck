# -*- coding: utf-8 -*-
"""Process Manager for local dev, test, and prod servers.
Manages asynchronous subprocesses, pseudo-terminals (PTY), ANSI colored log buffering,
real-time health checks, process metrics (CPU/RAM), and intelligent crash diagnostics.
"""
import logging
import os
import pty
import re
import select
import signal
import socket
import subprocess
import threading
import time
import urllib.request
import urllib.error
from collections import deque

class ManagedProcess:
    def __init__(self, project_id, name, command, cwd, mode="dev", port=None, max_lines=1000):
        self.project_id = project_id
        self.name = name
        self.command = command
        self.cwd = cwd
        self.mode = mode  # "dev", "prod", "test", "custom"
        self.port = port
        self.max_lines = max_lines
        self.logs = deque(maxlen=max_lines)
        self.listeners = set()
        self.lock = threading.Lock()

        self.process = None
        self.master_fd = None
        self.pid = None
        self.status = "stopped"  # "running", "stopped", "failed"
        self.exit_code = None
        self.started_at = None
        self.reader_thread = None

        # Health check & metrics
        self.ready = False
        self.ready_time_ms = None
        self.health_thread = None
        self.last_cpu = 0.0
        self.last_ram_mb = 0.0
        self.crash_diagnosis = None

    def add_listener(self, queue):
        with self.lock:
            self.listeners.add(queue)

    def remove_listener(self, queue):
        with self.lock:
            self.listeners.discard(queue)

    def _broadcast_log(self, chunk):
        with self.lock:
            self.logs.append(chunk)
            stale = []
            for q in self.listeners:
                try:
                    q.put_nowait(chunk)
                except Exception:
                    stale.append(q)
            for s in stale:
                self.listeners.discard(s)

    def start(self):
        if self.status == "running":
            return False, "Process already running"

        try:
            master, slave = pty.openpty()
            self.master_fd = master

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["FORCE_COLOR"] = "1"
            env["TERM"] = "xterm-256color"

            self.process = subprocess.Popen(
                ["/bin/bash", "-c", self.command],
                cwd=self.cwd,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                close_fds=True,
                env=env,
                preexec_fn=os.setsid
            )
            os.close(slave)
            self.pid = self.process.pid
            self.status = "running"
            self.exit_code = None
            self.started_at = time.time()
            self.ready = False
            self.ready_time_ms = None
            self.crash_diagnosis = None

            start_msg = f"\r\n\x1b[32m[DevDeck] Started '{self.name}' ({self.mode}) -> PID {self.pid}\x1b[0m\r\n"
            start_msg += f"\x1b[90m$ cd {self.cwd} && {self.command}\x1b[0m\r\n"
            self._broadcast_log(start_msg)

            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()

            if self.port:
                self.health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
                self.health_thread.start()

            return True, f"Started with PID {self.pid}"

        except Exception as e:
            self.status = "failed"
            err_msg = f"\r\n\x1b[31m[DevDeck Error] Could not start process: {e}\x1b[0m\r\n"
            self._broadcast_log(err_msg)
            return False, str(e)

    def _health_check_loop(self):
        t0 = time.time()
        timeout = 40.0
        url = f"http://127.0.0.1:{self.port}/"

        while self.status == "running" and (time.time() - t0) < timeout:
            time.sleep(0.7)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "DevDeck-HealthCheck"})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    self.ready = True
                    self.ready_time_ms = int((time.time() - t0) * 1000)
                    ready_sec = round(self.ready_time_ms / 1000.0, 1)
                    ready_msg = f"\r\n\x1b[32m✨ [DevDeck Ready] Server online at http://localhost:{self.port} (ready in {ready_sec}s)\x1b[0m\r\n"
                    self._broadcast_log(ready_msg)
                    return
            except urllib.error.HTTPError:
                self.ready = True
                self.ready_time_ms = int((time.time() - t0) * 1000)
                ready_sec = round(self.ready_time_ms / 1000.0, 1)
                ready_msg = f"\r\n\x1b[32m✨ [DevDeck Ready] Server online at http://localhost:{self.port} (ready in {ready_sec}s)\x1b[0m\r\n"
                self._broadcast_log(ready_msg)
                return
            except (urllib.error.URLError, socket.error, TimeoutError):
                continue
            except Exception:
                continue

    def _read_output(self):
        while self.status == "running" and self.master_fd is not None:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.2)
                if r:
                    data = os.read(self.master_fd, 4096)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    self._broadcast_log(text)
            except OSError:
                break
            except Exception as e:
                logging.error(f"Error reading pty: {e}")
                break

        if self.process:
            try:
                self.process.poll()
                self.exit_code = self.process.returncode
            except Exception:
                pass

        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

        self.status = "stopped" if self.exit_code in (0, None, -signal.SIGTERM) else "failed"
        finish_msg = f"\r\n\x1b[90m[DevDeck] Process exited with code {self.exit_code}\x1b[0m\r\n"
        self._broadcast_log(finish_msg)

        if self.status == "failed":
            self.crash_diagnosis = self._diagnose_crash()

    def _diagnose_crash(self):
        all_logs = "".join(list(self.logs)[-30:])

        m = re.search(r"ModuleNotFoundError:\s+No module named\s+['\"]([^'\"]+)['\"]", all_logs)
        if m:
            pkg = m.group(1).split(".")[0]
            return {
                "type": "missing_python_module",
                "message": f"Module Python manquant : '{pkg}'",
                "suggested_action": f"Installer '{pkg}' avec pip",
                "fix_command": f"pip install {pkg}"
            }

        m = re.search(r"Cannot find module\s+['\"]([^'\"]+)['\"]", all_logs)
        if not m:
            m = re.search(r"ERR_MODULE_NOT_FOUND.*?['\"]([^'\"]+)['\"]", all_logs)
        if m:
            pkg = m.group(1)
            if not pkg.startswith("."):
                return {
                    "type": "missing_node_module",
                    "message": f"Dépendance npm manquante : '{pkg}'",
                    "suggested_action": f"Installer '{pkg}' avec npm",
                    "fix_command": f"npm install {pkg}"
                }

        m = re.search(r"EADDRINUSE.*?[:\s](\d+)", all_logs)
        if not m:
            m = re.search(r"address already in use.*?[:\s](\d+)", all_logs, re.IGNORECASE)
        port_num = m.group(1) if m else str(self.port or "")
        if "EADDRINUSE" in all_logs or "already in use" in all_logs:
            return {
                "type": "port_conflict",
                "message": f"Port {port_num} déjà occupé par un autre processus",
                "suggested_action": f"Libérer le port {port_num}",
                "fix_command": f"kill_port {port_num}",
                "port": int(port_num) if port_num.isdigit() else self.port
            }

        m = re.search(r"/bin/bash:\s+line\s+\d+:\s+([^:]+):\s+command not found", all_logs)
        if not m:
            m = re.search(r"sh:\s+\d+:\s+([^:]+):\s+not found", all_logs)
        if m:
            cmd_missing = m.group(1).strip()
            return {
                "type": "command_not_found",
                "message": f"Commande introuvable : '{cmd_missing}'",
                "suggested_action": f"Vérifier l'installation de '{cmd_missing}'",
                "fix_command": ""
            }

        if "SyntaxError" in all_logs:
            return {
                "type": "syntax_error",
                "message": "Erreur de syntaxe détectée dans le code source",
                "suggested_action": "Consultez les logs pour repérer la ligne en erreur",
                "fix_command": ""
            }

        return {
            "type": "general_error",
            "message": f"Le processus s'est arrêté avec le code {self.exit_code}",
            "suggested_action": "Consultez l'onglet Terminal pour voir le détail de l'erreur",
            "fix_command": ""
        }

    def fetch_metrics(self):
        if not self.pid or self.status != "running":
            return {"cpu_percent": 0.0, "ram_mb": 0.0}

        try:
            res = subprocess.run(
                ["ps", "-o", "%cpu,rss", "--ppid", str(self.pid), "-p", str(self.pid), "--no-headers"],
                capture_output=True,
                text=True,
                timeout=1
            )
            total_cpu = 0.0
            total_rss_kb = 0
            if res.returncode == 0:
                for line in res.stdout.strip().split("\n"):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            total_cpu += float(parts[0])
                            total_rss_kb += int(parts[1])
                        except ValueError:
                            pass
            self.last_cpu = round(total_cpu, 1)
            self.last_ram_mb = round(total_rss_kb / 1024.0, 1)
            return {"cpu_percent": self.last_cpu, "ram_mb": self.last_ram_mb}
        except Exception:
            return {"cpu_percent": self.last_cpu, "ram_mb": self.last_ram_mb}

    def stop(self, timeout=3.0):
        if not self.process or self.status != "running":
            self.status = "stopped"
            return True, "Process is not running"

        stop_msg = f"\r\n\x1b[33m[DevDeck] Stopping process group (PID {self.pid})...\x1b[0m\r\n"
        self._broadcast_log(stop_msg)

        try:
            pgid = os.getpgid(self.process.pid)
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as e:
            logging.error(f"Error terminating process group: {e}")

        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.process.poll() is not None:
                break
            time.sleep(0.1)

        if self.process.poll() is None:
            try:
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGKILL)
                kill_msg = f"\x1b[31m[DevDeck] Sent SIGKILL to PID {self.pid}\x1b[0m\r\n"
                self._broadcast_log(kill_msg)
            except Exception:
                pass

        self.status = "stopped"
        self.ready = False
        return True, "Process stopped"

    def to_dict(self):
        uptime = int(time.time() - self.started_at) if self.started_at and self.status == "running" else 0
        metrics = self.fetch_metrics()
        return {
            "project_id": self.project_id,
            "name": self.name,
            "command": self.command,
            "cwd": self.cwd,
            "mode": self.mode,
            "port": self.port,
            "status": self.status,
            "ready": self.ready,
            "ready_time_ms": self.ready_time_ms,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "uptime_seconds": uptime,
            "cpu_percent": metrics["cpu_percent"],
            "ram_mb": metrics["ram_mb"],
            "crash_diagnosis": self.crash_diagnosis
        }


class ProcessManager:
    _instance = None

    def __init__(self):
        self.processes = {}  # project_id -> ManagedProcess
        self.lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ProcessManager()
        return cls._instance

    def start_project(self, project, mode="dev", custom_cmd=""):
        pid = project["id"]
        with self.lock:
            if pid in self.processes and self.processes[pid].status == "running":
                self.processes[pid].stop()

            cmd = ""
            if mode == "dev":
                cmd = project.get("dev_cmd") or ""
            elif mode == "prod":
                cmd = project.get("prod_cmd") or ""
            elif mode == "test":
                cmd = project.get("test_cmd") or ""
            elif mode == "custom":
                cmd = custom_cmd or project.get("custom_cmd") or ""

            if not cmd.strip():
                return False, f"No command defined for mode '{mode}'"

            proc = ManagedProcess(
                project_id=pid,
                name=project.get("name", pid),
                command=cmd,
                cwd=project.get("path"),
                mode=mode,
                port=project.get("port")
            )
            self.processes[pid] = proc

        return proc.start()

    def stop_project(self, project_id):
        with self.lock:
            proc = self.processes.get(project_id)
            if not proc:
                return True, "No active process for this project"
            return proc.stop()

    def restart_project(self, project, mode=None):
        pid = project["id"]
        proc = self.get_process(pid)
        current_mode = mode or (proc.mode if proc else "dev")
        self.stop_project(pid)
        time.sleep(0.5)
        return self.start_project(project, mode=current_mode)

    def get_process(self, project_id):
        with self.lock:
            return self.processes.get(project_id)

    def get_all_statuses(self):
        with self.lock:
            return {pid: proc.to_dict() for pid, proc in self.processes.items()}

    def get_logs(self, project_id):
        with self.lock:
            proc = self.processes.get(project_id)
            if not proc:
                return []
            return list(proc.logs)

    def clear_logs(self, project_id):
        with self.lock:
            proc = self.processes.get(project_id)
            if proc:
                proc.logs.clear()
                return True
        return False

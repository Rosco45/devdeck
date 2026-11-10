# -*- coding: utf-8 -*-
"""Process Manager for local dev, test, and prod servers.
Manages asynchronous subprocesses, pseudo-terminals (PTY), ANSI colored log buffering,
and real-time event streaming to web clients.
"""
import os
import pty
import select
import signal
import subprocess
import threading
import time
from collections import deque
import logging

class ManagedProcess:
    def __init__(self, project_id, name, command, cwd, mode="dev", max_lines=1000):
        self.project_id = project_id
        self.name = name
        self.command = command
        self.cwd = cwd
        self.mode = mode  # "dev", "prod", "test", "custom"
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
            # Create a pseudo-terminal for ANSI color codes & unbuffered output
            master, slave = pty.openpty()
            self.master_fd = master

            # Prepare environment with unbuffered flags
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
                preexec_fn=os.setsid  # Create new session group to kill all child processes
            )
            os.close(slave)
            self.pid = self.process.pid
            self.status = "running"
            self.exit_code = None
            self.started_at = time.time()

            start_msg = f"\r\n\x1b[32m[DevDeck] Started '{self.name}' ({self.mode}) -> PID {self.pid}\x1b[0m\r\n"
            start_msg += f"\x1b[90m$ cd {self.cwd} && {self.command}\x1b[0m\r\n"
            self._broadcast_log(start_msg)

            # Start background reader thread
            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()
            return True, f"Started with PID {self.pid}"

        except Exception as e:
            self.status = "failed"
            err_msg = f"\r\n\x1b[31m[DevDeck Error] Could not start process: {e}\x1b[0m\r\n"
            self._broadcast_log(err_msg)
            return False, str(e)

    def _read_output(self):
        buf = ""
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

        # Check process completion
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

    def stop(self, timeout=3.0):
        if not self.process or self.status != "running":
            self.status = "stopped"
            return True, "Process is not running"

        stop_msg = f"\r\n\x1b[33m[DevDeck] Stopping process group (PID {self.pid})...\x1b[0m\r\n"
        self._broadcast_log(stop_msg)

        try:
            # Send SIGTERM to the process group
            pgid = os.getpgid(self.process.pid)
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as e:
            logging.error(f"Error terminating process group: {e}")

        # Wait up to timeout seconds
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.process.poll() is not None:
                break
            time.sleep(0.1)

        # Force kill if still running
        if self.process.poll() is None:
            try:
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGKILL)
                kill_msg = f"\x1b[31m[DevDeck] Sent SIGKILL to PID {self.pid}\x1b[0m\r\n"
                self._broadcast_log(kill_msg)
            except Exception:
                pass

        self.status = "stopped"
        return True, "Process stopped"

    def to_dict(self):
        uptime = int(time.time() - self.started_at) if self.started_at and self.status == "running" else 0
        return {
            "project_id": self.project_id,
            "name": self.name,
            "command": self.command,
            "cwd": self.cwd,
            "mode": self.mode,
            "status": self.status,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "uptime_seconds": uptime
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
            # Stop existing if any
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
                mode=mode
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

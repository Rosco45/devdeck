# -*- coding: utf-8 -*-
"""Public Tunnel Manager (Localtunnel / Bore / Cloudflared).
Allows temporary public sharing of a local development port with one click.
"""
import logging
import os
import re
import signal
import subprocess
import threading
import time

class TunnelInstance:
    def __init__(self, project_id, port):
        self.project_id = project_id
        self.port = port
        self.url = None
        self.process = None
        self.status = "starting"  # starting, online, error, stopped
        self.error = None

    def start(self):
        try:
            # Using npx localtunnel which is standard and has zero permanent install footprint
            cmd = ["npx", "--yes", "localtunnel", "--port", str(self.port)]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )

            # Read first output line to capture the public URL
            t0 = time.time()
            while time.time() - t0 < 15.0:
                if self.process.poll() is not None:
                    err = self.process.stderr.read()
                    self.status = "error"
                    self.error = err or "Tunnel process exited"
                    return False, self.error

                line = self.process.stdout.readline()
                if line:
                    m = re.search(r'(https?://[^\s]+)', line)
                    if m:
                        self.url = m.group(1).strip()
                        self.status = "online"
                        return True, self.url
                time.sleep(0.2)

            self.status = "error"
            self.error = "Timeout waiting for tunnel URL"
            return False, self.error
        except Exception as e:
            self.status = "error"
            self.error = str(e)
            return False, str(e)

    def stop(self):
        if self.process:
            try:
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGTERM)
            except Exception:
                pass
        self.status = "stopped"
        self.url = None


class TunnelManager:
    _instance = None

    def __init__(self):
        self.tunnels = {}  # project_id -> TunnelInstance
        self.lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TunnelManager()
        return cls._instance

    def start_tunnel(self, project_id, port):
        with self.lock:
            if project_id in self.tunnels and self.tunnels[project_id].status == "online":
                return True, self.tunnels[project_id].url

            inst = TunnelInstance(project_id, port)
            self.tunnels[project_id] = inst

        ok, url_or_err = inst.start()
        return ok, url_or_err

    def stop_tunnel(self, project_id):
        with self.lock:
            inst = self.tunnels.get(project_id)
            if inst:
                inst.stop()
                del self.tunnels[project_id]
                return True, "Tunnel stopped"
            return True, "No tunnel running"

    def get_tunnel(self, project_id):
        with self.lock:
            inst = self.tunnels.get(project_id)
            if inst and inst.status == "online":
                return {"status": "online", "url": inst.url, "port": inst.port}
            return None

    def get_all_tunnels(self):
        with self.lock:
            return {
                pid: {"status": t.status, "url": t.url, "port": t.port}
                for pid, t in self.tunnels.items() if t.status == "online"
            }

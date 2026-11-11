# -*- coding: utf-8 -*-
"""Port and Process Inspector & Conflict Resolver.
Scans listening network ports, maps them to processes (PID, Command, User),
and terminates offending or orphaned server processes.
"""
import os
import re
import signal
import socket
import subprocess
import logging

COMMON_DEV_PORTS = {
    3000: "Next.js / React / Express",
    3001: "Dev Server (Secondary)",
    4200: "Angular",
    4321: "Astro",
    5000: "Flask / Python Web",
    5173: "Vite Dev Server",
    5174: "Vite (Secondary)",
    8000: "Django / FastAPI / Uvicorn",
    8080: "Vue / Webpack / Spring Boot",
    8081: "Metro / React Native",
    8888: "DevDeck Server",
    9000: "PHP-FPM / SonarQube",
    5432: "PostgreSQL Database",
    3306: "MySQL / MariaDB",
    6379: "Redis Cache",
    27017: "MongoDB Database",
}

def is_port_in_use(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, int(port))) == 0

def get_network_info():
    """Detects local LAN IP address and hostname for mobile testing."""
    local_ip = "127.0.0.1"
    hostname = socket.gethostname()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    return {"local_ip": local_ip, "hostname": hostname}

def get_process_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            raw = f.read().replace(b"\x00", b" ").strip()
            return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""

def scan_listening_ports():
    """Scans all TCP listening ports using lsof and ss."""
    ports_map = {}

    # Method 1: Try lsof
    try:
        res = subprocess.run(
            ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 9:
                    cmd_name = parts[0]
                    pid_str = parts[1]
                    user = parts[2]
                    name_field = parts[8]  # e.g. *:3000 or 127.0.0.1:8000
                    if ":" in name_field:
                        port_str = name_field.rsplit(":", 1)[1]
                        if port_str.isdigit():
                            port = int(port_str)
                            pid = int(pid_str)
                            ports_map[port] = {
                                "port": port,
                                "pid": pid,
                                "command": cmd_name,
                                "full_command": get_process_cmdline(pid) or cmd_name,
                                "user": user,
                                "hint": COMMON_DEV_PORTS.get(port, "")
                            }
    except Exception as e:
        logging.error(f"lsof scan error: {e}")

    # Method 2: Try ss if lsof missed something
    try:
        res = subprocess.run(
            ["ss", "-tlpn"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if "LISTEN" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        addr_port = parts[3]
                        if ":" in addr_port:
                            port_str = addr_port.rsplit(":", 1)[1]
                            # Clean port string (e.g. "53" or "53%lo")
                            port_str = port_str.split("%")[0]
                            if port_str.isdigit():
                                port = int(port_str)
                                if port not in ports_map:
                                    pid = None
                                    proc_name = "unknown"
                                    # Extract users:(("name",pid=123,fd=4))
                                    m = re.search(r'users:\(\("([^"]+)",pid=(\d+)', line)
                                    if m:
                                        proc_name = m.group(1)
                                        pid = int(m.group(2))
                                    ports_map[port] = {
                                        "port": port,
                                        "pid": pid,
                                        "command": proc_name,
                                        "full_command": get_process_cmdline(pid) if pid else proc_name,
                                        "user": "system",
                                        "hint": COMMON_DEV_PORTS.get(port, "")
                                    }
    except Exception as e:
        logging.error(f"ss scan error: {e}")

    # Sort ports numerically
    return sorted(list(ports_map.values()), key=lambda x: x["port"])

def kill_port(port, force=False):
    """Kills the process listening on a specified port."""
    port = int(port)
    ports = scan_listening_ports()
    target = None
    for p in ports:
        if p["port"] == port:
            target = p
            break

    if not target or not target.get("pid"):
        # Port might be free already or permission denied
        return False, f"No killable process found on port {port}"

    pid = target["pid"]
    # Safety check: avoid killing init, systemd, or devdeck self
    if pid <= 1 or pid == os.getpid():
        return False, "Refused to kill critical or self process"

    try:
        sig = signal.SIGKILL if force else signal.SIGTERM
        os.kill(pid, sig)
        return True, f"Sent signal {sig.name} to PID {pid} ({target['command']})"
    except ProcessLookupError:
        return True, f"Process {pid} already terminated"
    except PermissionError:
        return False, f"Permission denied to kill PID {pid} (run with appropriate rights)"
    except Exception as e:
        return False, f"Error killing process {pid}: {e}"

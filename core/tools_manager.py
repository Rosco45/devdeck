# -*- coding: utf-8 -*-
"""Developer Utilities Manager: HTTP API Tester, JWT Decoder, Hashes, and Token Generator.
"""
import base64
import hashlib
import json
import secrets
import time
import urllib.request
import urllib.error
import uuid

def execute_http_request(method, url, headers=None, body=None, timeout=10):
    method = method.upper()
    headers = headers or {}
    data = None

    if body and method in ["POST", "PUT", "PATCH", "DELETE"]:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
        elif isinstance(body, str):
            data = body.encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            duration_ms = int((time.time() - t0) * 1000)
            res_body = response.read().decode("utf-8", errors="replace")
            res_headers = dict(response.headers)
            status_code = response.getcode()

            try:
                parsed_json = json.loads(res_body)
                pretty_body = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                is_json = True
            except Exception:
                pretty_body = res_body
                is_json = False

            return {
                "ok": True,
                "status": status_code,
                "duration_ms": duration_ms,
                "headers": res_headers,
                "body": pretty_body,
                "is_json": is_json,
                "size_bytes": len(res_body)
            }
    except urllib.error.HTTPError as e:
        duration_ms = int((time.time() - t0) * 1000)
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            pretty_body = json.dumps(json.loads(err_body), indent=2, ensure_ascii=False)
        except Exception:
            pretty_body = err_body
        return {
            "ok": False,
            "status": e.code,
            "duration_ms": duration_ms,
            "headers": dict(e.headers),
            "body": pretty_body,
            "error": str(e)
        }
    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        return {
            "ok": False,
            "status": 0,
            "duration_ms": duration_ms,
            "headers": {},
            "body": "",
            "error": str(e)
        }

def decode_jwt(token_str):
    parts = token_str.strip().split(".")
    if len(parts) < 2:
        return {"error": "Invalid JWT format. Must contain at least header and payload separated by dots."}

    def b64url_decode(s):
        s += "=" * ((4 - len(s) % 4) % 4)
        return base64.urlsafe_b64decode(s.encode("utf-8")).decode("utf-8", errors="replace")

    try:
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))

        # Format timestamps if present
        details = {}
        for k in ["exp", "iat", "nbf"]:
            if k in payload and isinstance(payload[k], (int, float)):
                details[k + "_human"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(payload[k]))
                if k == "exp":
                    details["is_expired"] = payload[k] < time.time()

        return {
            "valid": True,
            "header": header,
            "payload": payload,
            "details": details
        }
    except Exception as e:
        return {"error": f"Failed to parse JWT: {e}"}

def generate_tokens(count=5, length=32):
    return {
        "uuid_v4": [str(uuid.uuid4()) for _ in range(count)],
        "hex_secret": [secrets.token_hex(length // 2) for _ in range(count)],
        "urlsafe_token": [secrets.token_urlsafe(length) for _ in range(count)]
    }

def compute_hashes(text):
    data = text.encode("utf-8")
    return {
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "base64_encoded": base64.b64encode(data).decode("utf-8"),
        "length_chars": len(text),
        "length_bytes": len(data)
    }

# ---------------------------------------------------------------------------
# Database Connectivity Ping Tester
# ---------------------------------------------------------------------------
def ping_database(host="127.0.0.1", port=5432, db_type="postgres", timeout=2.0):
    import socket
    t0 = time.time()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            latency_ms = round((time.time() - t0) * 1000, 1)
            return {
                "ok": True,
                "host": host,
                "port": port,
                "db_type": db_type,
                "latency_ms": latency_ms,
                "message": f"Connecté à {db_type.upper()} en {latency_ms} ms"
            }
    except ConnectionRefusedError:
        return {
            "ok": False,
            "host": host,
            "port": port,
            "db_type": db_type,
            "latency_ms": None,
            "message": f"Connexion refusée sur le port {port} (service inactif)"
        }
    except Exception as e:
        return {
            "ok": False,
            "host": host,
            "port": port,
            "db_type": db_type,
            "latency_ms": None,
            "message": str(e)
        }

# ---------------------------------------------------------------------------
# Configuration File Generators (.gitignore, Dockerfile, .env.example)
# ---------------------------------------------------------------------------
def generate_config_file(config_type, stack="Node.js", existing_env_path=None):
    if config_type == "gitignore":
        if "Python" in stack:
            return """# Python Gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
.env
.env.local
.pytest_cache/
*.log
.DS_Store
"""
        else:
            return """# Node.js / Web Gitignore
node_modules/
.next/
dist/
build/
.output/
*.log
.env
.env.local
.env.production
.DS_Store
Thumbs.db
.vscode/
"""
    elif config_type == "dockerfile":
        if "Python" in stack:
            return """# Multi-stage Python Dockerfile
FROM python:3.11-slim as base
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["python3", "app.py"]
"""
        else:
            return """# Multi-stage Node.js Dockerfile
FROM node:20-alpine AS base
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build || true

EXPOSE 3000
CMD ["npm", "start"]
"""
    elif config_type == "env_example" and existing_env_path and os.path.isfile(existing_env_path):
        lines = []
        with open(existing_env_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    lines.append(line)
                elif "=" in stripped:
                    k, _ = stripped.split("=", 1)
                    k = k.strip()
                    lines.append(f"{k}=your_{k.lower()}_here\n")
        return "".join(lines)
    else:
        return "# Sample Environment\nPORT=3000\nNODE_ENV=development\nSECRET_KEY=change_me_in_production\n"

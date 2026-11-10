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

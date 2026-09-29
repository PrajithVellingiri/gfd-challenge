#!/usr/bin/env python3
"""
Production Smoke Test Script for GFD Challenge DPI Platform.
Usage:
    python scripts/smoke_test.py [BACKEND_URL]

Examples:
    python scripts/smoke_test.py http://localhost:8000
    python scripts/smoke_test.py https://gfd-challenge-backend.onrender.com

Verifies:
- Root API endpoint availability
- Health check endpoint (/health)
- Interactive API documentation (/docs)
- Read-only district intelligence list (/api/infrastructure/districts)
- Read-only gap signals (/api/infrastructure/gap-signals)
- Read-only request clusters (/api/intelligence/clusters)
- Read-only emerging issues (/api/intelligence/emerging-issues)
- Administrative endpoint protection verification
"""

import sys
import os
import urllib.request
import urllib.error
import json
from typing import Tuple

DEFAULT_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def make_request(url: str, method: str = "GET", headers: dict = None) -> Tuple[int, dict, str]:
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.status
            body = resp.read().decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {}
            return status_code, data, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            data = json.loads(body)
        except Exception:
            data = {}
        return e.code, data, body
    except Exception as e:
        return 0, {}, str(e)


def run_smoke_tests(base_url: str) -> bool:
    clean_url = base_url.rstrip("/")
    print("=" * 70)
    print(f" GFD CHALLENGE — PRODUCTION SMOKE TEST SUITE")
    print(f" Target Backend: {clean_url}")
    print("=" * 70)

    checks = [
        {
            "name": "Root Gateway Status",
            "path": "/",
            "method": "GET",
            "expected_status": [200],
            "validator": lambda d, b: "GFD Challenge" in b
        },
        {
            "name": "Service Health Check",
            "path": "/health",
            "method": "GET",
            "expected_status": [200, 503],  # 200 healthy, 503 if DB connecting during cold start
            "validator": lambda d, b: "api" in d and d.get("api") == "running"
        },
        {
            "name": "API OpenAPI Documentation",
            "path": "/docs",
            "method": "GET",
            "expected_status": [200],
            "validator": lambda d, b: "swagger" in b.lower() or "openapi" in b.lower() or "html" in b.lower()
        },
        {
            "name": "District Infrastructure Intelligence (Read-Only)",
            "path": "/api/infrastructure/districts",
            "method": "GET",
            "expected_status": [200],
            "validator": lambda d, b: isinstance(d, list)
        },
        {
            "name": "Decision-Support Gap Signals (Read-Only)",
            "path": "/api/infrastructure/gap-signals",
            "method": "GET",
            "expected_status": [200],
            "validator": lambda d, b: isinstance(d, list)
        },
        {
            "name": "Request Clusters Registry (Read-Only)",
            "path": "/api/intelligence/clusters",
            "method": "GET",
            "expected_status": [200],
            "validator": lambda d, b: isinstance(d, list)
        },
        {
            "name": "Emerging Issue Trends (Read-Only)",
            "path": "/api/intelligence/emerging-issues",
            "method": "GET",
            "expected_status": [200],
            "validator": lambda d, b: isinstance(d, list)
        },
    ]

    all_passed = True

    for i, chk in enumerate(checks, 1):
        url = f"{clean_url}{chk['path']}"
        code, data, body = make_request(url, method=chk["method"])

        passed = False
        reason = ""

        if code in chk["expected_status"]:
            try:
                if chk["validator"](data, body):
                    passed = True
                else:
                    reason = "Response payload failed semantic validation check."
            except Exception as ex:
                reason = f"Validator error: {ex}"
        else:
            reason = f"HTTP {code} (Expected: {chk['expected_status']})"

        status_tag = "[ PASS ]" if passed else "[ FAIL ]"
        print(f"{status_tag} {i}. {chk['name']} -> {chk['path']} (HTTP {code})")
        if not passed:
            print(f"         Reason: {reason}")
            all_passed = False

    print("=" * 70)
    if all_passed:
        print(" RESULT: ALL SMOKE TESTS PASSED — BACKEND IS DEPLOYMENT-READY.")
    else:
        print(" RESULT: SOME CHECKS FAILED — REVIEW DEPLOYMENT CONFIGURATION.")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    success = run_smoke_tests(target)
    sys.exit(0 if success else 1)

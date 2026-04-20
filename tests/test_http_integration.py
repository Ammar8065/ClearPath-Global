from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

ROOT_DIR = Path(__file__).resolve().parent.parent


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _request(base_url: str, path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, object]:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw_body = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type", "")
            body: object = json.loads(raw_body) if "application/json" in content_type else raw_body
            return response.status, body
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8")
        content_type = exc.headers.get("Content-Type", "")
        body = json.loads(raw_body) if raw_body and "application/json" in content_type else raw_body
        return exc.code, body


@pytest.fixture
def running_http_app(tmp_path: Path):
    db_path = tmp_path / "integration_http.db"
    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    command.upgrade(config, "head")

    port = _find_free_port()
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    env["PRIVACY_MODE"] = "1"
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    base_url = f"http://127.0.0.1:{port}"

    try:
        for _ in range(40):
            try:
                status, body = _request(base_url, "/health")
                if status == 200 and isinstance(body, dict) and body.get("status") == "ok":
                    break
            except OSError:
                pass
            time.sleep(0.25)
        else:
            output = process.stdout.read() if process.stdout is not None else ""
            raise AssertionError(f"Server did not become healthy.\n{output}")

        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def test_http_private_evaluation_flow_supports_empty_operators(running_http_app: str):
    _, source = _request(
        running_http_app,
        "/sources",
        method="POST",
        payload={
          "jurisdiction": "AU",
          "title": "HTTP Source",
          "url": "https://example.com/http-source",
          "source_type": "legislation",
        },
    )

    _request(
        running_http_app,
        "/rules",
        method="POST",
        payload={
            "rule_code": "HTTP_RES_001",
            "jurisdiction": "AU",
            "category": "residency",
            "condition_expression": {"field": "days_in_country", "operator": ">=", "value": 183},
            "description": "183 day test",
            "risk_level": "high",
            "confidence_level": "high",
            "source_id": source["id"],
            "version": 1,
            "effective_from": "2025-01-01",
            "effective_to": None,
        },
    )
    _request(
        running_http_app,
        "/rules",
        method="POST",
        payload={
            "rule_code": "HTTP_EMPTY_001",
            "jurisdiction": "AU",
            "category": "tax",
            "condition_expression": {"field": "notes", "operator": "is_empty"},
            "description": "Empty notes should trigger",
            "risk_level": "low",
            "confidence_level": "high",
            "source_id": source["id"],
            "version": 1,
            "effective_from": "2025-01-01",
            "effective_to": None,
        },
    )

    status, body = _request(
        running_http_app,
        "/evaluate/private",
        method="POST",
        payload={
            "assessment_label": "HTTP Private Review",
            "client_data": {"days_in_country": 190, "notes": ""},
        },
    )

    assert status == 200
    assert body["client_id"] is None
    assert body["assessment_label"] == "HTTP Private Review"
    assert body["warnings"] == []
    assert set(body["triggered_rules"]) == {"HTTP_RES_001", "HTTP_EMPTY_001"}


def test_http_privacy_mode_blocks_client_and_asset_storage(running_http_app: str):
    client_status, client_body = _request(running_http_app, "/clients")
    asset_status, asset_body = _request(running_http_app, "/assets")

    assert client_status == 403
    assert asset_status == 403
    assert "privacy-first mode" in client_body["detail"].lower()
    assert "privacy-first mode" in asset_body["detail"].lower()


def test_http_root_serves_private_assessment_ui(running_http_app: str):
    status, body = _request(running_http_app, "/")

    assert status == 200
    assert isinstance(body, str)
    assert "Private Assessment" in body
    assert "No stored payloads" in body

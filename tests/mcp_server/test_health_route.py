from starlette.testclient import TestClient

import mcp_server.app as app_module


def test_default_host_stays_loopback():
    assert app_module.mcp.settings.host == "127.0.0.1"


def test_host_env_var_override(monkeypatch):
    monkeypatch.setenv("HOST", "0.0.0.0")
    import importlib

    importlib.reload(app_module)
    assert app_module.mcp.settings.host == "0.0.0.0"
    monkeypatch.delenv("HOST", raising=False)
    importlib.reload(app_module)  # restore module state for later tests


def test_health_route_returns_ok():
    client = TestClient(app_module.mcp.streamable_http_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

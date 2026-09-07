import json
import os
import shutil
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")

# Honors PORT/MCP_PORT overrides the same way docker-compose.yml does, so this
# suite never collides with another stack already bound to the default host
# ports (8000/8001) in the environment running the tests.
PORT = os.environ.get("PORT", "8000")
MCP_PORT = os.environ.get("MCP_PORT", "8001")
ENV = {**os.environ, "PORT": PORT, "MCP_PORT": MCP_PORT}


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True, env=ENV)


def test_clean_checkout_single_command_bring_up_and_localhost_only_ports():
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True, env=ENV)
    subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True, env=ENV)

    _wait_for_http(f"http://localhost:{PORT}/health", timeout=90)
    _wait_for_http(f"http://localhost:{MCP_PORT}/health", timeout=90)

    config = json.loads(
        subprocess.run(
            ["docker", "compose", "config", "--format", "json"], check=True, capture_output=True, text=True, env=ENV
        ).stdout
    )
    for service in config["services"].values():
        for port in service.get("ports", []):
            host_ip = port.get("host_ip")
            assert host_ip in ("127.0.0.1", "localhost"), f"port not scoped to localhost: {port}"


def _wait_for_http(url, timeout):
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - polling until the container is ready
            last_exc = exc
        time.sleep(1)
    raise AssertionError(f"{url} never returned 200: {last_exc}")

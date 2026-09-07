import json
import shutil
import subprocess
import time

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


def test_compose_build_produces_exactly_two_images():
    subprocess.run(["docker", "compose", "build"], check=True)
    config = json.loads(
        subprocess.run(["docker", "compose", "config", "--format", "json"], check=True, capture_output=True, text=True).stdout
    )
    assert set(config["services"].keys()) == {"crm-api", "mcp-server"}


def test_crm_api_becomes_healthy_before_mcp_server_starts():
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    deadline = time.time() + 60
    crm_api_healthy_at = None
    mcp_server_running_at = None
    while time.time() < deadline and (crm_api_healthy_at is None or mcp_server_running_at is None):
        cid = subprocess.run(["docker", "compose", "ps", "-q", "crm-api"], capture_output=True, text=True).stdout.strip()
        if cid:
            state = json.loads(
                subprocess.run(["docker", "inspect", "-f", "{{json .State}}", cid], capture_output=True, text=True).stdout or "{}"
            )
            if crm_api_healthy_at is None and state.get("Health", {}).get("Status") == "healthy":
                crm_api_healthy_at = time.time()
        mcp_ps = subprocess.run(["docker", "compose", "ps", "--status", "running", "mcp-server"], capture_output=True, text=True).stdout
        if mcp_server_running_at is None and "mcp-server" in mcp_ps:
            mcp_server_running_at = time.time()
        time.sleep(1)
    assert crm_api_healthy_at is not None, "crm-api never reported healthy"
    assert mcp_server_running_at is not None, "mcp-server never started"
    assert crm_api_healthy_at <= mcp_server_running_at

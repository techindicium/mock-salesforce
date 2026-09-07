import json
import os
import shutil
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")

# Honors a PORT override the same way docker-compose.yml does, so this suite
# never collides with another stack already bound to the default host port
# 8000 in the environment running the tests.
PORT = os.environ.get("PORT", "8000")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


def test_data_survives_down_and_up_without_dash_v():
    subprocess.run(["docker", "compose", "up", "-d", "crm-api"], check=True)
    _wait_healthy("crm-api", timeout=60)

    body = {"name": "Persistence Test Co"}
    req = urllib.request.Request(
        f"http://localhost:{PORT}/accounts",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        created = json.loads(resp.read())

    subprocess.run(["docker", "compose", "down"], check=True)  # no -v
    subprocess.run(["docker", "compose", "up", "-d", "crm-api"], check=True)
    _wait_healthy("crm-api", timeout=60)

    with urllib.request.urlopen(f"http://localhost:{PORT}/accounts/{created['id']}") as resp:
        fetched = json.loads(resp.read())
    assert fetched["name"] == "Persistence Test Co"


def _wait_healthy(service, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        cid = subprocess.run(["docker", "compose", "ps", "-q", service], capture_output=True, text=True).stdout.strip()
        if cid:
            state = subprocess.run(["docker", "inspect", "-f", "{{.State.Health.Status}}", cid], capture_output=True, text=True).stdout.strip()
            if state == "healthy":
                return
        time.sleep(1)
    raise AssertionError(f"{service} never reported healthy")

import shutil
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")

IMAGE = "mock-salesforce-mcp-server-test"
CONTAINER = "mock-salesforce-mcp-server-test-run"


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)


def test_mcp_server_image_builds_and_serves_health():
    subprocess.run(
        ["docker", "build", "-f", "docker/mcp-server/Dockerfile", "-t", IMAGE, "."],
        check=True,
    )
    subprocess.run(
        [
            "docker", "run", "-d", "--name", CONTAINER, "-p", "18001:8001",
            "-e", "API_BASE_URL=http://does-not-exist.invalid:9999",
            IMAGE,
        ],
        check=True,
    )
    _wait_for_http("http://localhost:18001/health", timeout=20)
    # container must still be running (no crash-loop) despite the bad API_BASE_URL
    status = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert status == "true"


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

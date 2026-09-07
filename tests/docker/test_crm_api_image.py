import shutil
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")

IMAGE = "mock-salesforce-crm-api-test"
CONTAINER = "mock-salesforce-crm-api-test-run"


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)


def test_crm_api_image_builds_and_serves_health_and_static():
    subprocess.run(
        ["docker", "build", "-f", "docker/crm-api/Dockerfile", "-t", IMAGE, "."],
        check=True,
    )
    subprocess.run(
        ["docker", "run", "-d", "--name", CONTAINER, "-p", "18000:8000", IMAGE],
        check=True,
    )
    _wait_for_http("http://localhost:18000/health", expect_status=200)
    with urllib.request.urlopen("http://localhost:18000/") as resp:
        assert resp.status == 200


def _wait_for_http(url, expect_status, timeout=30):
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == expect_status:
                    return
        except Exception as exc:  # noqa: BLE001 - polling until the container is ready
            last_exc = exc
        time.sleep(1)
    raise AssertionError(f"{url} never returned {expect_status}: {last_exc}")

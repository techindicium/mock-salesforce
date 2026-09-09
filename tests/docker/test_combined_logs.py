import os
import shutil
import subprocess
import time

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")

# Honors PORT/MCP_PORT overrides the same way docker-compose.yml does, so this
# suite never collides with another stack already bound to the default host
# ports (8020/8021) in the environment running the tests.
ENV = {**os.environ, "PORT": os.environ.get("PORT", "8020"), "MCP_PORT": os.environ.get("MCP_PORT", "8021")}


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True, env=ENV)


def test_logs_shows_output_from_both_services():
    subprocess.run(["docker", "compose", "up", "-d"], check=True, env=ENV)
    time.sleep(5)  # let both services emit at least their startup log lines
    logs = subprocess.run(["docker", "compose", "logs"], capture_output=True, text=True, env=ENV).stdout
    assert "crm-api" in logs
    assert "mcp-server" in logs

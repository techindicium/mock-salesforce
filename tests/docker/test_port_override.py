import os
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True, env={**os.environ, "PORT": "18080", "MCP_PORT": "18081"})


def test_port_env_vars_remap_published_host_ports():
    env = {**os.environ, "PORT": "18080", "MCP_PORT": "18081"}
    subprocess.run(["docker", "compose", "up", "-d"], check=True, env=env)
    ports = subprocess.run(["docker", "compose", "port", "crm-api", "18080"], capture_output=True, text=True, env=env).stdout
    assert "18080" in ports
    mcp_ports = subprocess.run(["docker", "compose", "port", "mcp-server", "18081"], capture_output=True, text=True, env=env).stdout
    assert "18081" in mcp_ports

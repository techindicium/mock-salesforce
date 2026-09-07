import shutil

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")
def test_docker_cli_is_available():
    assert shutil.which("docker") is not None

from pathlib import Path


def test_readme_documents_docker_run_instructions():
    text = Path("README.md").read_text()
    assert "docker compose up" in text
    assert "PORT" in text
    assert "MCP_PORT" in text
    assert "localhost" in text
    assert "docker compose logs" in text
    assert "docker compose down" in text

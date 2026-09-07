import stat

import pytest


def test_startup_raises_clear_error_when_db_dir_not_writable(tmp_path, monkeypatch):
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(stat.S_IREAD | stat.S_IEXEC)  # r-x, no write
    monkeypatch.setenv("DB_PATH", str(readonly_dir / "mock_salesforce.db"))

    from mock_salesforce.db import get_connection

    with pytest.raises(RuntimeError) as exc_info:
        get_connection()
    assert "DEPLOY_VOLUME_NOT_WRITABLE" in str(exc_info.value)
    assert str(readonly_dir) in str(exc_info.value)

    readonly_dir.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)  # restore for cleanup

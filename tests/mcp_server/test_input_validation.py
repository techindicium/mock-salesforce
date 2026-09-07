import inspect

import pytest

from mcp_server.app import create_account


def test_create_account_missing_name_errors_before_any_http_call():
    with pytest.raises(TypeError):
        create_account()  # `name` has no default — enforced at call time,
        # standing in for FastMCP's own schema-derived rejection of a tool
        # call missing a required argument, before the function body (and
        # therefore any HTTP request) ever runs.


def test_create_account_name_is_required_in_signature():
    sig = inspect.signature(create_account)
    assert sig.parameters["name"].default is inspect.Parameter.empty

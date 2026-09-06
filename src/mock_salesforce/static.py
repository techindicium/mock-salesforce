import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from mock_salesforce.errors import error_body

router = APIRouter()


def get_static_dir() -> Path:
    return Path(os.environ.get("STATIC_ASSETS_PATH", "static"))


@router.get("/{full_path:path}", include_in_schema=False)
def serve_static(full_path: str):
    static_dir = get_static_dir()
    if not static_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=error_body("STATIC_ASSET_NOT_FOUND", "No static assets are present"),
        )

    requested = full_path or "index.html"
    try:
        target = (static_dir / requested).resolve()
        static_root = static_dir.resolve()
        is_outside_root = static_root != target and static_root not in target.parents
        is_missing = is_outside_root or not target.is_file()
    except (OSError, ValueError):
        # A NUL byte or an overly long path segment (both valid percent-encoded
        # input) makes Path.resolve()/is_file() raise instead of returning False.
        # Treat any such filesystem-level rejection as "asset not found" so the
        # response stays a Salesforce-shaped 404, never a bare 500.
        is_missing = True

    if is_missing:
        raise HTTPException(
            status_code=404,
            detail=error_body("STATIC_ASSET_NOT_FOUND", f"No static asset at {requested}"),
        )
    return FileResponse(target)

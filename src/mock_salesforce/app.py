from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from mock_salesforce.db import get_connection, init_db
from mock_salesforce.errors import http_exception_handler, validation_exception_handler

app = FastAPI()
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)


@app.on_event("startup")
def on_startup() -> None:
    conn = get_connection()
    init_db(conn)
    conn.close()

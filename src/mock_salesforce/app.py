from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from mock_salesforce.accounts import router as accounts_router
from mock_salesforce.contacts import router as contacts_router
from mock_salesforce.db import get_connection, init_db
from mock_salesforce.errors import http_exception_handler, validation_exception_handler
from mock_salesforce.opportunities import router as opportunities_router
from mock_salesforce.seed import seed_if_empty

app = FastAPI()
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.include_router(accounts_router)
app.include_router(contacts_router)
app.include_router(opportunities_router)


@app.on_event("startup")
def on_startup() -> None:
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    conn.close()

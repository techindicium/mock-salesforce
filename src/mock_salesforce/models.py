from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

AccountType = Literal["Customer", "Prospect", "Partner", "Other"]


class AccountCreate(BaseModel):
    name: str
    account_type: Optional[AccountType] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    billing_street: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None


class AccountOut(AccountCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    billing_street: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None


class ContactCreate(BaseModel):
    account_id: int
    first_name: Optional[str] = None
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None


class ContactOut(ContactCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None

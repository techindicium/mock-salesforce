from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel

AccountType = Literal["Customer", "Prospect", "Partner", "Other"]


class AccountCreate(BaseModel):
    external_id: Optional[str] = None
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
    external_id: Optional[str] = None
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


StageName = Literal[
    "Prospecting",
    "Qualification",
    "Needs Analysis",
    "Value Proposition",
    "Id. Decision Makers",
    "Perception Analysis",
    "Proposal/Price Quote",
    "Negotiation/Review",
    "Closed Won",
    "Closed Lost",
]
OpportunityType = Literal["New Business", "Existing Business"]
LeadSource = Literal["Web", "Phone Inquiry", "Partner Referral", "Other"]


class OpportunityCreate(BaseModel):
    account_id: int
    name: str
    stage_name: StageName = "Prospecting"
    amount: Optional[float] = None
    close_date: date
    probability: Optional[float] = None
    opportunity_type: Optional[OpportunityType] = None
    lead_source: Optional[LeadSource] = None
    next_step: Optional[str] = None


class OpportunityOut(OpportunityCreate):
    id: int
    is_closed: bool
    is_won: bool
    created_at: datetime
    updated_at: datetime


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    stage_name: Optional[StageName] = None
    amount: Optional[float] = None
    close_date: Optional[date] = None
    probability: Optional[float] = None
    opportunity_type: Optional[OpportunityType] = None
    lead_source: Optional[LeadSource] = None
    next_step: Optional[str] = None


LeadStatus = Literal["New", "Contacted", "Qualified", "Unqualified"]
LeadRating = Literal["Hot", "Warm", "Cold"]


class LeadCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: str
    company: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_source: Optional[LeadSource] = None
    status: LeadStatus = "New"
    rating: Optional[LeadRating] = None


class LeadOut(LeadCreate):
    id: int
    converted: bool
    converted_at: Optional[datetime] = None
    converted_account_id: Optional[int] = None
    converted_contact_id: Optional[int] = None
    converted_opportunity_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    rating: Optional[LeadRating] = None


class LeadConvert(BaseModel):
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    create_opportunity: bool = False
    opportunity_name: Optional[str] = None
    opportunity_close_date: Optional[date] = None

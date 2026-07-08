from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class ContactBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_favorite: Optional[bool] = False
    personal_note: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_favorite: Optional[bool] = None
    personal_note: Optional[str] = None

class ContactNoteUpdate(BaseModel):
    personal_note: Optional[str] = None

class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    is_favorite: bool
    personal_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Monica Envelope Wrappers
class DataEnvelope(BaseModel, Generic[T]):
    data: T

class PaginationMeta(BaseModel):
    current_page: int
    per_page: int
    total: int
    last_page: int

class PaginatedEnvelope(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta

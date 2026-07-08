from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.contact import Contact
from app.services.contact_service import ContactService
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactNoteUpdate,
    ContactResponse,
    DataEnvelope,
    PaginatedEnvelope,
    PaginationMeta
)

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_contacts_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    GET /api/contacts/stats
    Return summary statistics for the authenticated user's contacts.
    Runs a single optimized query.
    """
    stmt = select(
        func.count(Contact.id).label("total"),
        func.sum(case((Contact.is_favorite == True, 1), else_=0)).label("favorites"),
        func.sum(case((Contact.personal_note.isnot(None) & (Contact.personal_note != ""), 1), else_=0)).label("with_notes")
    ).filter(Contact.account_id == current_user.id)

    result = await db.execute(stmt)
    row = result.first()

    total = row.total if row and row.total else 0
    favorites = int(row.favorites) if row and row.favorites else 0
    with_notes = int(row.with_notes) if row and row.with_notes else 0

    return {
        "total_contacts": total,
        "favorite_contacts": favorites,
        "contacts_with_notes": with_notes
    }

@router.get("/favorites", response_model=PaginatedEnvelope[ContactResponse])
async def list_favorite_contacts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort: str = Query("first_name"),
    direction: str = Query("asc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    GET /api/contacts/favorites
    List favorite contacts. Uses get_paginated_contacts under the hood with favorite=1.
    """
    contacts, total_count, last_page = await ContactService.get_paginated_contacts(
        db=db,
        user_id=current_user.id,
        page=page,
        limit=limit,
        favorite=1,
        search=search,
        sort=sort,
        direction=direction
    )

    return PaginatedEnvelope(
        data=contacts,
        meta=PaginationMeta(
            current_page=page,
            per_page=limit,
            total=total_count,
            last_page=last_page
        )
    )

@router.get("", response_model=PaginatedEnvelope[ContactResponse])
async def list_contacts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    favorite: Optional[int] = Query(None, description="Filter by favorite (1 for true, 0 for false)"),
    search: Optional[str] = Query(None, description="Search term"),
    sort: str = Query("first_name"),
    direction: str = Query("asc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    GET /api/contacts
    List contacts with search, favorite filter, pagination, and sorting.
    """
    contacts, total_count, last_page = await ContactService.get_paginated_contacts(
        db=db,
        user_id=current_user.id,
        page=page,
        limit=limit,
        favorite=favorite,
        search=search,
        sort=sort,
        direction=direction
    )

    return PaginatedEnvelope(
        data=contacts,
        meta=PaginationMeta(
            current_page=page,
            per_page=limit,
            total=total_count,
            last_page=last_page
        )
    )

@router.post("", response_model=DataEnvelope[ContactResponse], status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_in: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    POST /api/contacts
    Create a new contact. Helper endpoint for seeding/testing.
    """
    contact = Contact(
        account_id=current_user.id,
        first_name=contact_in.first_name,
        last_name=contact_in.last_name,
        email=contact_in.email,
        is_favorite=contact_in.is_favorite or False,
        personal_note=contact_in.personal_note
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return DataEnvelope(data=contact)

@router.get("/{id}", response_model=DataEnvelope[ContactResponse])
async def get_contact(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    GET /api/contacts/{id}
    Include new fields (is_favorite, personal_note) in the response.
    """
    result = await db.execute(
        select(Contact).filter(Contact.id == id, Contact.account_id == current_user.id)
    )
    contact = result.scalars().first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return DataEnvelope(data=contact)

@router.post("/{id}/favorite", response_model=DataEnvelope[ContactResponse])
async def mark_contact_as_favorite(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    POST /api/contacts/{id}/favorite
    Mark contact as favorite.
    """
    result = await db.execute(
        select(Contact).filter(Contact.id == id, Contact.account_id == current_user.id)
    )
    contact = result.scalars().first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.is_favorite = True
    await db.commit()
    await db.refresh(contact)
    return DataEnvelope(data=contact)

@router.delete("/{id}/favorite", response_model=DataEnvelope[ContactResponse])
async def remove_contact_from_favorites(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    DELETE /api/contacts/{id}/favorite
    Remove contact from favorites.
    """
    result = await db.execute(
        select(Contact).filter(Contact.id == id, Contact.account_id == current_user.id)
    )
    contact = result.scalars().first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.is_favorite = False
    await db.commit()
    await db.refresh(contact)
    return DataEnvelope(data=contact)

@router.patch("/{id}/favorite", response_model=DataEnvelope[ContactResponse])
async def toggle_contact_favorite_status(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    PATCH /api/contacts/{id}/favorite
    Toggle favorite status.
    """
    result = await db.execute(
        select(Contact).filter(Contact.id == id, Contact.account_id == current_user.id)
    )
    contact = result.scalars().first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.is_favorite = not contact.is_favorite
    await db.commit()
    await db.refresh(contact)
    return DataEnvelope(data=contact)

@router.put("/{id}/note", response_model=DataEnvelope[ContactResponse])
async def update_contact_personal_note(
    id: int,
    note_in: ContactNoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    PUT /api/contacts/{id}/note
    Update contact personal note.
    """
    result = await db.execute(
        select(Contact).filter(Contact.id == id, Contact.account_id == current_user.id)
    )
    contact = result.scalars().first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.personal_note = note_in.personal_note
    await db.commit()
    await db.refresh(contact)
    return DataEnvelope(data=contact)

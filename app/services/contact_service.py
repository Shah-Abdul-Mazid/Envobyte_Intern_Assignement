from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_, desc, asc
from typing import Optional, Tuple, List
import math

from app.models.contact import Contact

class ContactService:
    @staticmethod
    def build_contacts_query(
        user_id: int,
        favorite: Optional[int] = None,
        search: Optional[str] = None,
        sort: Optional[str] = "first_name",
        direction: Optional[str] = "asc"
    ):
        """
        Builds the base query for contacts filtered by user account, search criteria,
        and favorite status. Avoids code duplication.
        """
        query = select(Contact).filter(Contact.account_id == user_id)

        # Filter by favorite status
        if favorite is not None:
            # favorite can be passed as 1 or 0 (or boolean True/False representation)
            is_fav = favorite == 1
            query = query.filter(Contact.is_favorite == is_fav)

        # Filter by search string
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Contact.first_name.ilike(search_pattern),
                    Contact.last_name.ilike(search_pattern),
                    Contact.email.ilike(search_pattern)
                )
            )

        # Handle Sorting
        # Let's dynamically map sort field
        sort_column = Contact.first_name
        if sort == "last_name":
            sort_column = Contact.last_name
        elif sort == "created_at":
            sort_column = Contact.created_at
        elif sort == "id":
            sort_column = Contact.id

        if direction == "desc":
            query = query.order_by(desc(sort_column), desc(Contact.id))
        else:
            query = query.order_by(asc(sort_column), asc(Contact.id))

        return query

    @staticmethod
    async def get_paginated_contacts(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        limit: int = 10,
        favorite: Optional[int] = None,
        search: Optional[str] = None,
        sort: Optional[str] = "first_name",
        direction: Optional[str] = "asc"
    ) -> Tuple[List[Contact], int, int]:
        """
        Executes paginated queries using build_contacts_query.
        Returns a tuple of (contacts, total_count, last_page).
        """
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10

        # Build base select query
        base_query = ContactService.build_contacts_query(
            user_id=user_id,
            favorite=favorite,
            search=search,
            sort=sort,
            direction=direction
        )

        # Count total records first
        # Extract the where clause and count
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply offset and limit
        offset = (page - 1) * limit
        paginated_query = base_query.offset(offset).limit(limit)
        
        result = await db.execute(paginated_query)
        contacts = list(result.scalars().all())

        last_page = math.ceil(total_count / limit) if total_count > 0 else 1

        return contacts, total_count, last_page

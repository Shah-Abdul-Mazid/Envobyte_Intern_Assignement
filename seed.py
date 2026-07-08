import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.contact import Contact
from app.core.security import get_password_hash

async def seed_data():
    # Make sure tables are created (in case migrations haven't run, though we will use alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        print("Seeding database...")
        # Clear existing data
        await db.execute(Base.metadata.tables["contacts"].delete())
        await db.execute(Base.metadata.tables["users"].delete())
        await db.commit()

        # Create main test user
        john = User(
            name="John Doe",
            email="john@example.com",
            hashed_password=get_password_hash("password123")
        )
        # Create another user to verify isolation
        other_user = User(
            name="Other User",
            email="other@example.com",
            hashed_password=get_password_hash("password123")
        )

        db.add(john)
        db.add(other_user)
        await db.commit()
        await db.refresh(john)
        await db.refresh(other_user)

        # Contacts for John Doe (125 contacts to simulate pagination/stats, or some count)
        # Let's seed a few distinct ones first as requested:
        contacts_data = [
            # first_name, last_name, email, is_favorite, personal_note
            ("Jane", "Doe", "jane.doe@example.com", True, "Met at the conference."),
            ("John", "Smith", "john.smith@example.com", False, "Friend from college."),
            ("Alice", "Johnson", "alice.j@example.com", True, None),
            ("Bob", "Wilson", "bob.w@example.com", False, None),
            ("Charlie", "Brown", "charlie.b@example.com", False, "Enjoys photography."),
        ]

        # Let's seed 120 more contacts for John Doe to simulate the 125 total contacts in the prompt's example
        # (Total: 125, favorite: 18, with_notes: 42)
        # Currently we have 5 contacts: 2 favorites, 3 with notes
        # We need 16 more favorites, and 39 more with notes to hit the target.
        # Let's write a loop to generate them dynamically.
        
        # Add the 5 custom contacts first
        for first, last, email, is_fav, note in contacts_data:
            contact = Contact(
                account_id=john.id,
                first_name=first,
                last_name=last,
                email=email,
                is_favorite=is_fav,
                personal_note=note
            )
            db.add(contact)

        # Add 120 extra contacts for John
        for i in range(6, 126):
            # We want:
            # - total = 125 contacts
            # - favorite = 18 contacts (we have 2, need 16 more. Let's make every 7th contact favorite)
            # - with_notes = 42 contacts (we have 3, need 39 more. Let's make every 3rd contact have a note)
            is_fav = False
            if i % 7 == 0:
                is_fav = True
            
            note = None
            if i % 3 == 0:
                note = f"Auto-generated personal note for contact {i}"
                
            contact = Contact(
                account_id=john.id,
                first_name=f"ContactFirst{i}",
                last_name=f"ContactLast{i}",
                email=f"contact{i}@example.com",
                is_favorite=is_fav,
                personal_note=note
            )
            db.add(contact)

        # Contacts for Other User (to verify they aren't returned in John's queries)
        other_contacts = [
            Contact(
                account_id=other_user.id,
                first_name="IsolatedContact",
                last_name="User",
                email="isolated@example.com",
                is_favorite=True,
                personal_note="Should not be visible to John"
            )
        ]
        for contact in other_contacts:
            db.add(contact)

        await db.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
import os

from app.main import app
from app.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.contact import Contact
from app.core.security import get_password_hash, create_access_token

# Use a test SQLite database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create async engine for test database
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    # Ensure tables are created
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with TestSessionLocal() as session:
        yield session
        # Clear database records after each test to keep tests isolated
        await session.execute(Base.metadata.tables["contacts"].delete())
        await session.execute(Base.metadata.tables["users"].delete())
        await session.commit()
        
    # Drop tables after test to clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override get_db dependency
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    hashed_pwd = get_password_hash("password123")
    user = User(
        name="Test User",
        email="test@example.com",
        hashed_password=hashed_pwd
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user: User) -> dict:
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def test_contact(db: AsyncSession, test_user: User) -> Contact:
    contact = Contact(
        account_id=test_user.id,
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        is_favorite=False,
        personal_note="Initial note"
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

@pytest.fixture
def anyio_backend():
    return "asyncio"


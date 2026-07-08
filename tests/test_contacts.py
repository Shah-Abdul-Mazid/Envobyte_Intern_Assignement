import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contact import Contact

# Use pytestmark to make all tests in this module async and run with the anyio fixture
pytestmark = pytest.mark.anyio


async def test_mark_contact_as_favorite(
    client: AsyncClient,
    test_contact: Contact,
    auth_headers: dict
):
    """
    Test POST /api/contacts/{id}/favorite
    """
    response = await client.post(
        f"/api/contacts/{test_contact.id}/favorite",
        headers=auth_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert "data" in res_data
    assert res_data["data"]["id"] == test_contact.id
    assert res_data["data"]["is_favorite"] is True

async def test_remove_contact_from_favorites(
    client: AsyncClient,
    test_contact: Contact,
    auth_headers: dict,
    db: AsyncSession
):
    """
    Test DELETE /api/contacts/{id}/favorite
    """
    # First, mark it favorite directly in DB
    test_contact.is_favorite = True
    await db.commit()

    response = await client.delete(
        f"/api/contacts/{test_contact.id}/favorite",
        headers=auth_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["data"]["is_favorite"] is False

async def test_toggle_contact_favorite_status(
    client: AsyncClient,
    test_contact: Contact,
    auth_headers: dict
):
    """
    Test PATCH /api/contacts/{id}/favorite
    """
    # Initially is_favorite is False
    assert test_contact.is_favorite is False

    # Toggle to True
    response = await client.patch(
        f"/api/contacts/{test_contact.id}/favorite",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_favorite"] is True

    # Toggle back to False
    response = await client.patch(
        f"/api/contacts/{test_contact.id}/favorite",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_favorite"] is False

async def test_update_personal_note(
    client: AsyncClient,
    test_contact: Contact,
    auth_headers: dict
):
    """
    Test PUT /api/contacts/{id}/note
    """
    new_note = "Updated personal note via API."
    response = await client.put(
        f"/api/contacts/{test_contact.id}/note",
        json={"personal_note": new_note},
        headers=auth_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["data"]["personal_note"] == new_note

async def test_filter_contacts_by_favorite(
    client: AsyncClient,
    test_user: dict,
    auth_headers: dict,
    db: AsyncSession
):
    """
    Test GET /api/contacts?favorite=1
    """
    # Seed contacts: 2 favorites, 1 non-favorite
    c1 = Contact(account_id=test_user.id, first_name="FavOne", is_favorite=True)
    c2 = Contact(account_id=test_user.id, first_name="FavTwo", is_favorite=True)
    c3 = Contact(account_id=test_user.id, first_name="NonFav", is_favorite=False)
    db.add_all([c1, c2, c3])
    await db.commit()

    # Filter favorite=1
    response = await client.get("/api/contacts?favorite=1", headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert "data" in res_data
    assert len(res_data["data"]) == 2
    assert all(c["is_favorite"] is True for c in res_data["data"])

    # Filter favorite=0
    response = await client.get("/api/contacts?favorite=0", headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data["data"]) == 1
    assert res_data["data"][0]["is_favorite"] is False

async def test_list_favorite_contacts_endpoint(
    client: AsyncClient,
    test_user: dict,
    auth_headers: dict,
    db: AsyncSession
):
    """
    Test GET /api/contacts/favorites
    """
    c1 = Contact(account_id=test_user.id, first_name="FavOne", is_favorite=True)
    c2 = Contact(account_id=test_user.id, first_name="NonFav", is_favorite=False)
    db.add_all([c1, c2])
    await db.commit()

    response = await client.get("/api/contacts/favorites", headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data["data"]) == 1
    assert res_data["data"][0]["first_name"] == "FavOne"

async def test_contacts_search(
    client: AsyncClient,
    test_user: dict,
    auth_headers: dict,
    db: AsyncSession
):
    """
    Test GET /api/contacts?search=john
    """
    c1 = Contact(account_id=test_user.id, first_name="John", last_name="Doe", email="john@example.com")
    c2 = Contact(account_id=test_user.id, first_name="Alice", last_name="Smith", email="alice@example.com")
    db.add_all([c1, c2])
    await db.commit()

    response = await client.get("/api/contacts?search=john", headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data["data"]) == 1
    assert res_data["data"][0]["first_name"] == "John"

async def test_contacts_statistics(
    client: AsyncClient,
    test_user: dict,
    auth_headers: dict,
    db: AsyncSession
):
    """
    Test GET /api/contacts/stats
    """
    c1 = Contact(account_id=test_user.id, first_name="One", is_favorite=True, personal_note="Note here")
    c2 = Contact(account_id=test_user.id, first_name="Two", is_favorite=True, personal_note=None)
    c3 = Contact(account_id=test_user.id, first_name="Three", is_favorite=False, personal_note="Another note")
    c4 = Contact(account_id=test_user.id, first_name="Four", is_favorite=False, personal_note=None)
    db.add_all([c1, c2, c3, c4])
    await db.commit()

    response = await client.get("/api/contacts/stats", headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["total_contacts"] == 4
    assert res_data["favorite_contacts"] == 2
    assert res_data["contacts_with_notes"] == 2

# Monica CRM Contact Module – FastAPI Backend

A clean, modern backend implementation of the Monica CRM assignment built with **FastAPI** and **SQLAlchemy** (async). It supports the Contact module features with Favorite status, Personal Notes, query building, pagination, search, sorting, and optimized statistics.

---

## 🚀 Features & Deliverables

- **Database Changes (Part 2):** Added `is_favorite` (boolean) and `personal_note` (nullable text) columns with proper Alembic migrations.
- **API Endpoints (Part 3):** Standardized endpoints matching Monica's conventions wrapped in `data` envelopes:
  - `GET /api/contacts/favorites` – Get all favorite contacts.
  - `POST /api/contacts/{id}/favorite` – Mark a contact as favorite.
  - `DELETE /api/contacts/{id}/favorite` – Remove a contact from favorites.
  - `PATCH /api/contacts/{id}/favorite` – Toggle favorite status.
  - `PUT /api/contacts/{id}/note` – Update contact's personal note.
  - `GET /api/contacts/{id}` – Get a single contact details (includes new fields).
- **Search, Filters & Sorting (Part 4):** A single optimized query builder that supports filtering by `favorite` status, full-text `search`, custom `sort` fields, and `direction`, complete with pagination.
- **Statistics (Part 5):** A single optimized database query that counts total contacts, favorite contacts, and contacts with notes in one call.
- **Comprehensive Tests (Part 6):** 8 test cases verifying all routes, authorization scopes, statistics, searching, and toggles.

---

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **ORM:** SQLAlchemy (async)
- **Database Driver:** `aiosqlite` (async SQLite)
- **Migrations:** Alembic
- **Testing:** `pytest` + `anyio` + `httpx`
- **Security:** Standard JWT (Bearer) authorization with `bcrypt`

---

## 📂 File Structure

```
Envobyte_Intern_Assignement/
├── app/
│   ├── core/
│   │   ├── config.py            # App settings (Pydantic Settings)
│   │   └── security.py          # Password hashing (bcrypt) & JWT operations
│   ├── models/
│   │   ├── user.py              # User account model
│   │   └── contact.py           # Contact model with new fields
│   ├── schemas/
│   │   ├── auth.py              # User registration/login validation schemas
│   │   └── contact.py           # Contact request/response & Envelope schemas
│   ├── routers/
│   │   ├── auth.py              # Registration & token login routes
│   │   └── contacts.py          # All contact endpoints (stats, favorites, search, etc.)
│   ├── services/
│   │   └── contact_service.py   # Reusable query builder with pagination & search logic
│   ├── database.py              # Async engine & session setup
│   ├── dependencies.py          # Current user context resolver
│   └── main.py                  # FastAPI application entry point
├── alembic/
│   ├── versions/
│   │   ├── 001_create_users.py  # User migration script
│   │   └── 002_add_contacts.py  # Contact migration script
│   └── env.py
├── tests/
│   ├── conftest.py              # Pytest configuration & overrides
│   └── test_contacts.py         # Contact feature tests
├── alembic.ini
├── requirements.txt
├── .env.example
├── .env
├── seed.py                      # Database seeder matching stats example
└── README.md
```

---

## 💻 Setup Instructions

### 1. Clone the repository & Create Environment
Navigate to the project root directory:
```bash
python -m venv venv
venv\Scripts\activate      # On Windows
source venv/bin/activate   # On Linux/macOS
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Configuration
Copy the environment variables:
```bash
cp .env.example .env
```

### 4. Run Database Migrations
Use Alembic to create the tables:
```bash
alembic upgrade head
```

### 5. Seed the Database
Seed the database with default test data (includes 125 contacts, 18 favorites, and 42 contacts with notes to replicate the exact statistics example):
```bash
python seed.py
```

### 6. Run the Application Local Server
```bash
uvicorn app.main:app --reload
```
The documentation is automatically generated and interactive at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔍 Part 4 – Contact Search & Filtering

The existing contact listing endpoint (`GET /api/contacts`) has been extended to support search and filtering without duplicating any query logic.

### How It Works

All query logic is encapsulated in a **single reusable function** inside `app/services/contact_service.py`:

```python
ContactService.build_contacts_query(
    user_id=...,
    favorite=...,   # 1 = favorites only, 0 = non-favorites
    search=...,     # matches first_name, last_name, or email (case-insensitive)
    sort=...,       # sort field: first_name, last_name, created_at, id
    direction=...   # asc or desc
)
```

This same builder is called internally by **both** the general listing endpoint and the `/favorites` endpoint — ensuring zero logic duplication.

### Supported Query Parameters

| Parameter   | Type    | Example              | Description                                  |
|-------------|---------|----------------------|----------------------------------------------|
| `favorite`  | int     | `?favorite=1`        | Filter by favorite (`1`=yes, `0`=no)         |
| `search`    | string  | `?search=john`       | Case-insensitive match on name/email         |
| `page`      | int     | `?page=2`            | Page number (default: 1)                     |
| `limit`     | int     | `?limit=20`          | Results per page (default: 10, max: 100)     |
| `sort`      | string  | `?sort=last_name`    | Sort field (`first_name`, `last_name`, etc.) |
| `direction` | string  | `?direction=desc`    | Sort direction (`asc` or `desc`)             |

### Example Requests

**Filter favorites only:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/contacts?favorite=1"
```

**Search by name:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/contacts?search=john"
```

**Combined – favorites named "john", page 2, sorted by last name:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/contacts?favorite=1&search=john&page=2&sort=last_name&direction=asc"
```

### Example Response

```json
{
  "data": [
    {
      "id": 3,
      "account_id": 1,
      "first_name": "John",
      "last_name": "Smith",
      "email": "john.smith@example.com",
      "is_favorite": true,
      "personal_note": "Friend from college.",
      "created_at": "2026-07-08T10:00:00",
      "updated_at": "2026-07-08T10:00:00"
    }
  ],
  "meta": {
    "current_page": 1,
    "per_page": 10,
    "total": 1,
    "last_page": 1
  }
}
```

---

## 📊 Part 5 – Statistics API

### Endpoint

```
GET /api/contacts/stats
```

**Requires:** Bearer token (authenticated user only)

### Implementation

The statistics are calculated using a **single optimized SQL query** with conditional aggregation — no contacts are ever loaded into Python memory:

```sql
SELECT
  COUNT(id)                                             AS total_contacts,
  SUM(CASE WHEN is_favorite = 1 THEN 1 ELSE 0 END)     AS favorite_contacts,
  SUM(CASE WHEN personal_note IS NOT NULL
            AND personal_note != '' THEN 1 ELSE 0 END) AS contacts_with_notes
FROM contacts
WHERE account_id = <authenticated_user_id>
```

- **Account isolation:** Only contacts belonging to the authenticated user are counted.
- **Single round-trip:** All three metrics are returned from one DB query.
- **Easy to extend:** Add new aggregation columns to the `select()` call without restructuring the endpoint.

### Example Request

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/contacts/stats"
```

### Example Response

```json
{
  "total_contacts": 125,
  "favorite_contacts": 18,
  "contacts_with_notes": 42
}
```

---

## 🧪 Part 6 – Tests

### Running the Tests

```bash
python -m pytest -p no:asyncio -v
```

> **Note:** The `-p no:asyncio` flag disables `pytest-asyncio` in favour of `anyio`, which prevents event loop scope conflicts on Python 3.13.

### Test Results

```
============================= test session starts ==============================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
plugins: anyio-4.13.0
collected 8 items

tests/test_contacts.py::test_mark_contact_as_favorite          PASSED  [ 12%]
tests/test_contacts.py::test_remove_contact_from_favorites     PASSED  [ 25%]
tests/test_contacts.py::test_toggle_contact_favorite_status    PASSED  [ 37%]
tests/test_contacts.py::test_update_personal_note              PASSED  [ 50%]
tests/test_contacts.py::test_filter_contacts_by_favorite       PASSED  [ 62%]
tests/test_contacts.py::test_list_favorite_contacts_endpoint   PASSED  [ 75%]
tests/test_contacts.py::test_contacts_search                   PASSED  [ 87%]
tests/test_contacts.py::test_contacts_statistics               PASSED  [100%]

============================== 8 passed in 6.97s ==============================
```

### Test Coverage Summary

| # | Test Name                             | Part | Endpoint Tested                      | What It Verifies                                      |
|---|---------------------------------------|------|--------------------------------------|-------------------------------------------------------|
| 1 | `test_mark_contact_as_favorite`       | 6    | `POST /api/contacts/{id}/favorite`   | `is_favorite` becomes `true`, correct `data` envelope |
| 2 | `test_remove_contact_from_favorites`  | 6    | `DELETE /api/contacts/{id}/favorite` | `is_favorite` becomes `false`                         |
| 3 | `test_toggle_contact_favorite_status` | 3    | `PATCH /api/contacts/{id}/favorite`  | Toggle true→false and false→true in two calls         |
| 4 | `test_update_personal_note`           | 6    | `PUT /api/contacts/{id}/note`        | `personal_note` field is correctly updated            |
| 5 | `test_filter_contacts_by_favorite`    | 6    | `GET /api/contacts?favorite=1`       | Only favorites returned when `favorite=1` or `0`      |
| 6 | `test_list_favorite_contacts_endpoint`| 4    | `GET /api/contacts/favorites`        | Dedicated favorites endpoint returns only favorites   |
| 7 | `test_contacts_search`                | 4    | `GET /api/contacts?search=john`      | Search matches first name, excludes other contacts    |
| 8 | `test_contacts_statistics`            | 5    | `GET /api/contacts/stats`            | Returns accurate total, favorites, and notes counts   |

### Test Architecture

- **Isolated test DB:** Each test gets a fresh in-memory SQLite database (created and dropped per test).
- **Auth simulation:** Fixtures mint a valid JWT token directly without going through the login route.
- **Dependency override:** FastAPI's `app.dependency_overrides` replaces the live `get_db` dependency with the test session.
- **No shared state:** Contacts seeded inside one test are cleaned up before the next test runs.

---

## 📖 Implementation Approach & Decisions

- **FastAPI Framework:** Implemented the backend using FastAPI as requested, keeping the file structure clean and modular.
- **Single Source of Truth Querying:** Reusable database logic is encapsulated inside `contact_service.py`'s `build_contacts_query()`. It handles pagination, search matching (`first_name`, `last_name`, `email`), sorting, and filtering without code duplication.
- **Optimized Statistics:** Calculated total contacts, favorites, and notes using standard SQL aggregation (`COUNT` and conditional `SUM(CASE)`) in **one query execution** to ensure maximum efficiency.
- **Security:** Standard JWT tokens were implemented for authenticating endpoints. The user account represents the scope of data visibility.
- **Route Order Matters:** Static routes like `/stats` and `/favorites` are registered **before** the dynamic `/{id}` route to prevent FastAPI from interpreting them as integer IDs.

---

## ⚠️ Assumptions & Trade-offs

- **User/Account Scope:** In Monica, contacts are associated with an Account, which can have multiple users. For this clean structure, contacts are linked to `User` accounts. Each user has full ownership of their contact list.
- **SQLite Engine:** SQLite with `aiosqlite` was utilized for easy local setup, but the SQLAlchemy constructs and Alembic configurations are completely PostgreSQL-ready.
- **Passlib Bcrypt Issue:** Replaced `passlib` context hashing with the standard `bcrypt` package to prevent `ValueError` wrapper errors on Python 3.12/3.13 environments.
- **Empty string notes:** A `personal_note` set to an empty string `""` is treated as "no note" in the statistics count, matching the intent of the feature.

---

## ⏱️ Estimated Time Spent

- **Total Time Spent:** 3.5 Hours

## 🎥 Live Test Recording

## 🎥 Live Test Recording
[▶️ Download / Watch Live Test Recording](https://github.com/Shah-Abdul-Mazid/Envobyte_Intern_Assignement/releases/download/Video/LiveTest.mp4)



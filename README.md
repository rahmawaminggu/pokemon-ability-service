# pokemon-ability-service

FastAPI service that fetches Pokémon ability data from PokeAPI, normalizes the `effect_entries`, persists them to PostgreSQL, and returns the results as JSON.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | FastAPI | Required by the test; async-native, fast |
| Database | PostgreSQL 16 | Production-grade; `JSONB` column for `language` is queryable |
| ORM | SQLAlchemy 2 (async) | Async-first with `asyncpg` driver — no blocking I/O |
| HTTP client | httpx (async) | Non-blocking PokeAPI calls within the same event loop |
| Containerization | Docker + docker-compose | API + DB run as isolated services with a single command |

---

## Project Structure

```
repo/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app & lifespan (auto table creation)
│   ├── database.py    # Async engine, session factory
│   ├── models.py      # SQLAlchemy ORM model
│   ├── schemas.py     # Pydantic request / response schemas
│   └── services.py    # Business logic: fetch → normalize → persist → return
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Database Schema

Table: `pokemon_ability_effects`

| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | Auto-increment |
| `raw_id` | VARCHAR(13) | 13-char alphanumeric, from request |
| `user_id` | VARCHAR(7) | 7-digit numeric string, from request |
| `pokemon_ability_id` | INTEGER | Indexed |
| `effect` | TEXT | Full effect description per language |
| `language` | JSONB | `{"name": "en", "url": "..."}` |
| `short_effect` | TEXT | Short effect description per language |

One row is inserted **per language entry** in `effect_entries`, so a single request with 9 language variants produces 9 rows.

---

## Running with Docker (Recommended)

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.  
PostgreSQL runs on port `5432`. Tables are created automatically on first startup.

---

## Running Locally (without Docker)

**Requirements:** Python 3.11+, a running PostgreSQL instance.

```bash
pip install -r requirements.txt

export DATABASE_URL="postgresql+asyncpg://flip:flip123@localhost:5432/flipdb"

uvicorn app.main:app --reload
```

---

## API Usage

### `POST /ability`

**Request body:**

```json
{
  "raw_id": "7dsa8d7sa9dsa",
  "user_id": "5199434",
  "pokemon_ability_id": "150"
}
```

**Response:**

```json
{
  "raw_id": "7dsa8d7sa9dsa",
  "user_id": "5199434",
  "returned_entries": [
    {
      "effect": "Pokémon mit dieser Fähigkeit ...",
      "language": {"name": "de", "url": "https://pokeapi.co/api/v2/language/6/"},
      "short_effect": "Verwandelt sich beim Betreten des Kampfes in den Gegner."
    },
    {
      "effect": "This Pokémon transforms into a random opponent upon entering battle...",
      "language": {"name": "en", "url": "https://pokeapi.co/api/v2/language/9/"},
      "short_effect": "Transforms upon entering battle."
    }
  ],
  "pokemon_list": ["ditto"]
}
```

**cURL example:**

```bash
curl -X POST http://localhost:8000/ability \
  -H "Content-Type: application/json" \
  -d '{"raw_id": "7dsa8d7sa9dsa", "user_id": "5199434", "pokemon_ability_id": "150"}'
```

### `GET /health`

Returns `{"status": "ok"}` — useful for container health probes.

### Interactive Docs

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Design Decisions

### Why PostgreSQL over SQLite/MySQL?
- `JSONB` type stores the `language` object natively and allows GIN-indexed queries on its fields.
- Production-closer: Flip's stack likely uses a real RDBMS; PostgreSQL is the most common choice.
- SQLite would simplify local dev but cannot be easily containerized alongside FastAPI with async drivers.

### Why async end-to-end?
FastAPI is ASGI-based. Using `asyncpg` (SQLAlchemy async) + `httpx` async keeps the entire request lifecycle non-blocking. Under load, this avoids thread-pool exhaustion that would occur with synchronous DB/HTTP calls.

### Normalization strategy
Each element of `effect_entries` becomes one row keyed by `(raw_id, user_id, pokemon_ability_id)`. This makes per-language queries trivial (`WHERE language->>'name' = 'en'`) and avoids storing arrays in a single column.

### `returned_entries` scope
The response returns **all rows** matching `(raw_id, user_id, pokemon_ability_id)` — including any previously stored from prior requests with the same identifiers. This matches the expected output in the test spec.
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PokemonAbilityEffect
from app.schemas import AbilityRequest, AbilityResponse, EffectEntry, LanguageInfo

POKEAPI_BASE = "https://pokeapi.co/api/v2/ability/{ability_id}"


async def fetch_ability(ability_id: str) -> dict:
    url = POKEAPI_BASE.format(ability_id=ability_id)
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def extract_effect_entries(data: dict) -> list[dict]:
    return [
        {
            "effect": entry["effect"],
            "language": entry["language"],
            "short_effect": entry["short_effect"],
        }
        for entry in data.get("effect_entries", [])
    ]


def extract_pokemon_names(data: dict) -> list[str]:
    return [p["pokemon"]["name"] for p in data.get("pokemon", [])]


async def save_entries(
    db: AsyncSession,
    request: AbilityRequest,
    entries: list[dict],
) -> None:
    ability_id = int(request.pokemon_ability_id)
    rows = [
        PokemonAbilityEffect(
            raw_id=request.raw_id,
            user_id=request.user_id,
            pokemon_ability_id=ability_id,
            effect=entry["effect"],
            language=entry["language"],
            short_effect=entry["short_effect"],
        )
        for entry in entries
    ]
    db.add_all(rows)
    await db.commit()


async def get_stored_entries(
    db: AsyncSession,
    raw_id: str,
    user_id: str,
    pokemon_ability_id: int,
) -> list[PokemonAbilityEffect]:
    result = await db.execute(
        select(PokemonAbilityEffect).where(
            PokemonAbilityEffect.raw_id == raw_id,
            PokemonAbilityEffect.user_id == user_id,
            PokemonAbilityEffect.pokemon_ability_id == pokemon_ability_id,
        )
    )
    return result.scalars().all()


async def process_ability(
    db: AsyncSession,
    request: AbilityRequest,
) -> AbilityResponse:
    data = await fetch_ability(request.pokemon_ability_id)

    entries = extract_effect_entries(data)
    pokemon_names = extract_pokemon_names(data)

    await save_entries(db, request, entries)

    stored = await get_stored_entries(
        db, request.raw_id, request.user_id, int(request.pokemon_ability_id)
    )

    returned_entries = [
        EffectEntry(
            effect=row.effect,
            language=LanguageInfo(**row.language),
            short_effect=row.short_effect,
        )
        for row in stored
    ]

    return AbilityResponse(
        raw_id=request.raw_id,
        user_id=request.user_id,
        returned_entries=returned_entries,
        pokemon_list=pokemon_names,
    )
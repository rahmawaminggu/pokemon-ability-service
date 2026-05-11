from pydantic import BaseModel


class AbilityRequest(BaseModel):
    raw_id: str
    user_id: str
    pokemon_ability_id: str


class LanguageInfo(BaseModel):
    name: str
    url: str


class EffectEntry(BaseModel):
    effect: str
    language: LanguageInfo
    short_effect: str


class AbilityResponse(BaseModel):
    raw_id: str
    user_id: str
    returned_entries: list[EffectEntry]
    pokemon_list: list[str]
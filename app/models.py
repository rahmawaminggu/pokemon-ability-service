from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class PokemonAbilityEffect(Base):
    __tablename__ = "pokemon_ability_effects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_id: Mapped[str] = mapped_column(String(13), nullable=False)
    user_id: Mapped[str] = mapped_column(String(7), nullable=False)
    pokemon_ability_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    effect: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[dict] = mapped_column(JSONB, nullable=False)
    short_effect: Mapped[str] = mapped_column(Text, nullable=False)
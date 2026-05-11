from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db
from app.schemas import AbilityRequest, AbilityResponse
from app.services import process_ability


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="pokemon-ability-service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/ability", response_model=AbilityResponse)
async def get_ability(
    request: AbilityRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await process_ability(db, request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/health")
async def health():
    return {"status": "ok"}
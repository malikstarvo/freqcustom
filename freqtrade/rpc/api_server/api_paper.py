from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from freqtrade.papertrade.engine import PaperEngine
from freqtrade.papertrade.store import PaperStore


router_paper = APIRouter(prefix="/api/v1/paper", tags=["PaperTrader"])


class TopUpRequest(BaseModel):
    amount: float


class PaperStatus(BaseModel):
    state: str
    equity: float
    balance: float
    total_pnl: float
    day_pnl: float
    day_trades: int
    bar_count: int
    uptime_sec: float
    position: dict | None = None


class TopUpResponse(BaseModel):
    old_balance: float
    new_balance: float
    amount: float


_engine: PaperEngine | None = None
_store: PaperStore | None = None


def set_engine(engine: PaperEngine, store: PaperStore) -> None:
    global _engine, _store
    _engine = engine
    _store = store


@router_paper.get("/status", response_model=PaperStatus)
async def paper_status() -> dict[str, Any]:
    if not _engine:
        raise HTTPException(status_code=503, detail="Paper trader not running")
    return _engine.get_state()


@router_paper.post("/topup", response_model=TopUpResponse)
async def paper_topup(req: TopUpRequest) -> dict[str, Any]:
    if not _engine:
        raise HTTPException(status_code=503, detail="Paper trader not running")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    return _engine.top_up(req.amount)


@router_paper.get("/trades")
async def paper_trades(limit: int = 50) -> list[dict[str, Any]]:
    if not _store:
        raise HTTPException(status_code=503, detail="Paper trader not running")
    return []


@router_paper.get("/account")
async def paper_account(limit: int = 100) -> list[dict[str, Any]]:
    if not _store:
        raise HTTPException(status_code=503, detail="Paper trader not running")
    return []

"""
api/main.py
API REST interne — expose les données agrégées pour le frontend.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
from database.repository import PriceRepository

app = FastAPI(title="Cardmarket Tracker API", version="1.0.0")
repo = PriceRepository()


class PricePoint(BaseModel):
    date: date
    language: str
    price_min: float
    price_max: float
    price_avg: float
    offer_count: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products/{product_id}/history", response_model=list[PricePoint])
def get_history(product_id: int, language: str = "fr"):
    """Retourne l'historique de prix agrégé pour un produit."""
    snapshots = repo.get_price_history(product_id, language)
    if not snapshots:
        raise HTTPException(status_code=404, detail="Aucune donnée trouvée")
    return [
        PricePoint(
            date=s.snapshot_date,
            language=s.language,
            price_min=s.price_min,
            price_max=s.price_max,
            price_avg=s.price_avg,
            offer_count=s.offer_count,
        )
        for s in snapshots
    ]

"""
database/repository.py
Couche d'accès aux données — insertion et lecture des snapshots de prix.
"""

from datetime import date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from database.models import Base, Expansion, Product, PriceSnapshot
from config import settings


class PriceRepository:
    def __init__(self):
        self.engine = create_engine(settings.database_url)

    def save_price_snapshot(
        self,
        expansion_name: str,
        product_name: str,
        snapshot_date: date,
        aggregated_prices: dict[str, dict],
    ):
        """Persiste les prix agrégés. Upsert par (product, date, langue)."""
        with Session(self.engine) as session:
            # Upsert expansion
            expansion = session.scalar(
                select(Expansion).where(Expansion.name == expansion_name)
            )
            if not expansion:
                expansion = Expansion(name=expansion_name)
                session.add(expansion)
                session.flush()

            # Upsert product
            product = session.scalar(
                select(Product).where(
                    Product.expansion_id == expansion.id,
                    Product.name == product_name,
                )
            )
            if not product:
                product = Product(expansion_id=expansion.id, name=product_name)
                session.add(product)
                session.flush()

            # Upsert snapshots par langue
            for lang, prices in aggregated_prices.items():
                snapshot = session.scalar(
                    select(PriceSnapshot).where(
                        PriceSnapshot.product_id == product.id,
                        PriceSnapshot.snapshot_date == snapshot_date,
                        PriceSnapshot.language == lang,
                    )
                )
                if snapshot:
                    snapshot.price_min = prices["min"]
                    snapshot.price_max = prices["max"]
                    snapshot.price_avg = prices["avg"]
                    snapshot.offer_count = prices["count"]
                else:
                    session.add(PriceSnapshot(
                        product_id=product.id,
                        snapshot_date=snapshot_date,
                        language=lang,
                        price_min=prices["min"],
                        price_max=prices["max"],
                        price_avg=prices["avg"],
                        offer_count=prices["count"],
                    ))

            session.commit()

    def get_price_history(
        self, product_id: int, language: str
    ) -> list[PriceSnapshot]:
        """Retourne l'historique complet pour un produit et une langue."""
        with Session(self.engine) as session:
            return session.scalars(
                select(PriceSnapshot)
                .where(
                    PriceSnapshot.product_id == product_id,
                    PriceSnapshot.language == language,
                )
                .order_by(PriceSnapshot.snapshot_date)
            ).all()

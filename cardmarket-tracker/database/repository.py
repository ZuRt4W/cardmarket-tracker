"""
database/repository.py
Couche d'accès aux données.

Deux responsabilités principales :
  1. register_product()     — mémorise un product_id Cardmarket (mode découverte)
  2. get_all_known_products() — liste les produits connus (mode exploitation)
  3. save_price_snapshot()  — persiste les prix agrégés du jour
  4. has_known_products()   — indique si la base est déjà peuplée
"""

from datetime import date
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from database.models import Base, Expansion, Product, PriceSnapshot
from config import settings


class PriceRepository:
    def __init__(self):
        self.engine = create_engine(settings.database_url)

    # ─────────────────────────────────────────
    # Mode découverte
    # ─────────────────────────────────────────

    def register_product(
        self,
        expansion_name: str,
        product_name: str,
        cm_product_id: int,
    ) -> Product:
        """
        Enregistre un produit Cardmarket en base.
        Idempotent — si le produit existe déjà, retourne l'existant.
        Permet au mode exploitation d'utiliser cm_product_id directement.
        """
        with Session(self.engine) as session:
            expansion = session.scalar(
                select(Expansion).where(Expansion.name == expansion_name)
            )
            if not expansion:
                expansion = Expansion(name=expansion_name)
                session.add(expansion)
                session.flush()

            product = session.scalar(
                select(Product).where(Product.cm_product_id == cm_product_id)
            )
            if not product:
                product = Product(
                    expansion_id=expansion.id,
                    name=product_name,
                    cm_product_id=cm_product_id,
                )
                session.add(product)
                session.commit()

            return product

    # ─────────────────────────────────────────
    # Mode exploitation
    # ─────────────────────────────────────────

    def has_known_products(self) -> bool:
        """Retourne True si la base contient au moins un produit connu."""
        with Session(self.engine) as session:
            count = session.scalar(select(func.count()).select_from(Product))
            return (count or 0) > 0

    def get_all_known_products(self) -> list[Product]:
        """
        Retourne tous les produits enregistrés lors de la découverte,
        avec leur expansion chargée (eager load pour éviter les N+1).
        """
        with Session(self.engine) as session:
            products = session.scalars(
                select(Product).join(Product.expansion)
            ).all()
            # Détache les objets de la session pour usage hors contexte
            for p in products:
                _ = p.expansion.name
            return products

    # ─────────────────────────────────────────
    # Snapshots (commun aux deux modes)
    # ─────────────────────────────────────────

    def save_price_snapshot(
        self,
        expansion_name: str,
        product_name: str,
        snapshot_date: date,
        aggregated_prices: dict[str, dict],
    ):
        """
        Persiste les prix agrégés du jour.
        Upsert par (product, date, langue) — idempotent.
        """
        with Session(self.engine) as session:
            expansion = session.scalar(
                select(Expansion).where(Expansion.name == expansion_name)
            )
            if not expansion:
                expansion = Expansion(name=expansion_name)
                session.add(expansion)
                session.flush()

            product = session.scalar(
                select(Product).where(
                    Product.expansion_id == expansion.id,
                    Product.name == product_name,
                )
            )
            if not product:
                return  # Produit non enregistré — ne devrait pas arriver

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

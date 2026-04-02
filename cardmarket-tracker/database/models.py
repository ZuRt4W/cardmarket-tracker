"""
database/models.py
Modèles SQLAlchemy — optimisés pour TimescaleDB (hypertable sur snapshot_date).
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Expansion(Base):
    __tablename__ = "expansions"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    products = relationship("Product", back_populates="expansion")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    expansion_id = Column(Integer, ForeignKey("expansions.id"), nullable=False)
    name = Column(String(200), nullable=False)

    # ID natif Cardmarket — permet d'appeler GET /products/{cm_product_id}/articles
    # directement en mode exploitation, sans re-scanner les 527 extensions
    cm_product_id = Column(Integer, nullable=False, unique=True)

    expansion = relationship("Expansion", back_populates="products")
    price_snapshots = relationship("PriceSnapshot", back_populates="product")

    __table_args__ = (UniqueConstraint("expansion_id", "name"),)


class PriceSnapshot(Base):
    """
    Snapshot quotidien des prix agrégés.
    Compatible TimescaleDB hypertable sur snapshot_date.
    Les données brutes ne sont jamais stockées ici.
    """
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    snapshot_date = Column(Date, nullable=False, index=True)
    language = Column(String(5), nullable=False)
    price_min = Column(Float, nullable=False)
    price_max = Column(Float, nullable=False)
    price_avg = Column(Float, nullable=False)
    offer_count = Column(Integer, nullable=False)

    product = relationship("Product", back_populates="price_snapshots")

    __table_args__ = (UniqueConstraint("product_id", "snapshot_date", "language"),)

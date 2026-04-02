"""
scripts/init_db.py
Initialise la base de données et active TimescaleDB si disponible.
Usage : python scripts/init_db.py
"""

from sqlalchemy import create_engine, text
from database.models import Base
from config import settings


def init():
    engine = create_engine(settings.database_url)

    print("Création des tables...")
    Base.metadata.create_all(engine)

    # Activation TimescaleDB (optionnel — ignore si non installé)
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            conn.execute(text(
                "SELECT create_hypertable('price_snapshots', 'snapshot_date', if_not_exists => TRUE);"
            ))
            conn.commit()
            print("TimescaleDB activé — hypertable configurée.")
        except Exception:
            print("TimescaleDB non disponible — PostgreSQL standard utilisé.")

    print("Base de données initialisée.")


if __name__ == "__main__":
    init()

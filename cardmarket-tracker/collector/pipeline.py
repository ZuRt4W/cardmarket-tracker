"""
collector/pipeline.py
Orchestration de la collecte : appel API → agrégation → stockage.
Les données brutes ne sont jamais persistées.
"""

import logging
from datetime import date

from collector.client import CardmarketClient
from processor.aggregator import aggregate_prices
from database.repository import PriceRepository

logger = logging.getLogger(__name__)


def run_collection():
    """Point d'entrée principal de la collecte quotidienne."""
    client = CardmarketClient()
    repo = PriceRepository()
    today = date.today()

    logger.info(f"Début de collecte — {today}")

    expansions = client.get_expansions()
    logger.info(f"{len(expansions)} extensions trouvées")

    collected = 0
    for expansion in expansions:
        exp_id = expansion["idExpansion"]
        exp_name = expansion["name"]

        try:
            products = client.get_products(exp_id)
            if not products:
                continue

            for product in products:
                # Agrégation immédiate — les données brutes ne sont pas conservées
                aggregated = aggregate_prices(product)
                if aggregated:
                    repo.save_price_snapshot(
                        expansion_name=exp_name,
                        product_name=product["name"],
                        snapshot_date=today,
                        aggregated_prices=aggregated,
                    )
                    collected += 1

        except Exception as e:
            logger.error(f"Erreur extension {exp_name}: {e}")
            continue

    logger.info(f"Collecte terminée — {collected} snapshots enregistrés")
    return collected

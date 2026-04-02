"""
collector/pipeline.py

Deux modes de collecte selon l'état de la base de données :

  MODE DÉCOUVERTE (premier cycle ou rescan forcé)
  ────────────────────────────────────────────────
  1 requête  → GET /expansions/game/3           liste toutes les extensions
  527 req.   → GET /expansions/{id}/products    une par extension BB + ETB
  N req.     → GET /products/{id}/articles      une par produit ayant des offres
  → Les product_id trouvés sont persistés en base pour les cycles suivants.

  MODE EXPLOITATION (cycles quotidiens normaux)
  ───────────────────────────────────────────────
  N req.     → GET /products/{id}/articles      directement sur les produits connus
  → Les 527 requêtes de scan d'extensions sont évitées entièrement.

  Dans les deux modes :
  - Les articles bruts sont agrégés immédiatement (min/max/avg par langue)
  - Les données brutes ne sont jamais persistées
"""

import logging
from datetime import date

from collector.client import CardmarketClient
from processor.aggregator import aggregate_articles
from database.repository import PriceRepository

logger = logging.getLogger(__name__)


def _collect_articles(
    client: CardmarketClient,
    repo: PriceRepository,
    product_id: int,
    product_name: str,
    expansion_name: str,
    today: date,
    stats: dict,
):
    """
    Collecte et agrège les articles d'un produit connu.
    Fonction partagée entre les deux modes.
    """
    try:
        articles = client.get_product_articles(product_id)

        if not articles:
            logger.debug(f"  └── {product_name} : aucune offre disponible")
            return

        # Agrégation immédiate — les articles bruts ne sont jamais conservés
        aggregated = aggregate_articles(articles)

        if aggregated:
            repo.save_price_snapshot(
                expansion_name=expansion_name,
                product_name=product_name,
                snapshot_date=today,
                aggregated_prices=aggregated,
            )
            stats["snapshots_saved"] += 1
            logger.info(f"  └── {product_name} → {len(aggregated)} langue(s)")

    except Exception as exc:
        logger.error(f"  └── Erreur produit [{product_name}]: {exc}")
        stats["errors"] += 1


def run_discovery(client: CardmarketClient, repo: PriceRepository, today: date) -> dict:
    """
    MODE DÉCOUVERTE — à exécuter uniquement lors du premier cycle
    ou lorsqu'on souhaite détecter de nouvelles extensions.

    Requêtes : 1 + 527 (extensions) + N (articles des produits matchés)
    """
    stats = {
        "mode": "discovery",
        "date": str(today),
        "expansions_scanned": 0,
        "products_matched": 0,
        "snapshots_saved": 0,
        "errors": 0,
    }

    logger.info("═══ MODE DÉCOUVERTE — scan complet des extensions ═══")

    expansions = client.get_pokemon_expansions()
    stats["expansions_scanned"] = len(expansions)

    for expansion in expansions:
        exp_id = expansion["idExpansion"]
        exp_name = expansion["name"]

        try:
            products = client.get_sealed_products(exp_id)
            if not products:
                continue

            stats["products_matched"] += len(products)

            for product in products:
                # Enregistre le produit en base (pour les cycles suivants)
                repo.register_product(
                    expansion_name=exp_name,
                    product_name=product["name"],
                    cm_product_id=product["idProduct"],
                )
                _collect_articles(
                    client, repo,
                    product_id=product["idProduct"],
                    product_name=product["name"],
                    expansion_name=exp_name,
                    today=today,
                    stats=stats,
                )

        except Exception as exc:
            logger.error(f"Erreur extension [{exp_name}]: {exc}")
            stats["errors"] += 1

    logger.info(
        f"═══ Découverte terminée — "
        f"{stats['expansions_scanned']} extensions, "
        f"{stats['products_matched']} produits, "
        f"{stats['snapshots_saved']} snapshots ═══"
    )
    return stats


def run_exploitation(client: CardmarketClient, repo: PriceRepository, today: date) -> dict:
    """
    MODE EXPLOITATION — cycle quotidien normal.

    Utilise les product_id déjà connus en base.
    Requêtes : N uniquement (une par produit connu)
    Les 527 scans d'extensions sont évités entièrement.
    """
    stats = {
        "mode": "exploitation",
        "date": str(today),
        "products_processed": 0,
        "snapshots_saved": 0,
        "errors": 0,
    }

    logger.info("═══ MODE EXPLOITATION — collecte sur produits connus ═══")

    known_products = repo.get_all_known_products()
    stats["products_processed"] = len(known_products)

    logger.info(f"{len(known_products)} produits connus en base")

    for product in known_products:
        _collect_articles(
            client, repo,
            product_id=product.cm_product_id,
            product_name=product.name,
            expansion_name=product.expansion.name,
            today=today,
            stats=stats,
        )

    logger.info(
        f"═══ Exploitation terminée — "
        f"{stats['products_processed']} produits, "
        f"{stats['snapshots_saved']} snapshots, "
        f"{stats['errors']} erreur(s) ═══"
    )
    return stats


def run_collection(force_discovery: bool = False) -> dict:
    """
    Point d'entrée principal.

    - Si la base ne contient aucun produit connu → MODE DÉCOUVERTE automatique
    - Sinon → MODE EXPLOITATION (N requêtes seulement)
    - force_discovery=True → force un nouveau scan complet (ex: nouvelle saison)
    """
    client = CardmarketClient()
    repo = PriceRepository()
    today = date.today()

    if force_discovery or not repo.has_known_products():
        logger.info("Aucun produit en base — lancement du mode découverte")
        return run_discovery(client, repo, today)
    else:
        return run_exploitation(client, repo, today)

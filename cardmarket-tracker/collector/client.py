"""
collector/client.py

Gestion des appels à l'API Cardmarket avec OAuth 1.0a.
Hiérarchie ciblée :
  Jeu : Pokémon (idGame=3)
    └── Catégories : Booster Box + Elite Trainer Box
          └── Extensions : toutes celles qui matchent
                └── Articles : toutes les offres (langue, prix, quantité)

"2 fois par jour" = 2 cycles complets de collecte (pas 2 requêtes HTTP).
"""

import logging
import time
from typing import Any

import httpx
from authlib.integrations.httpx_client import OAuth1Auth

from config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.cardmarket.com/ws/v2.0/output.json"

POKEMON_GAME_ID = 3
TARGET_PRODUCT_TYPES = {"Booster Box", "Elite Trainer Box"}


class CardmarketClient:
    def __init__(self):
        self.auth = OAuth1Auth(
            client_id=settings.cm_app_token,
            client_secret=settings.cm_app_secret,
            token=settings.cm_access_token,
            token_secret=settings.cm_access_token_secret,
        )

    def _get(self, endpoint: str, params: dict = None) -> dict[str, Any]:
        """
        Requête GET authentifiée avec retry exponentiel.
        Gère les erreurs 429 (rate limit) et 503 (indisponibilité).
        """
        url = f"{BASE_URL}/{endpoint}"
        for attempt in range(settings.max_retries):
            try:
                with httpx.Client(auth=self.auth, timeout=30) as client:
                    response = client.get(url, params=params)

                logger.info(f"[{response.status_code}] GET /{endpoint}")

                if response.status_code == 200:
                    return response.json()

                if response.status_code in (429, 503):
                    wait = settings.retry_backoff ** attempt
                    logger.warning(
                        f"Rate limit {response.status_code} — "
                        f"retry dans {wait:.0f}s (tentative {attempt + 1}/{settings.max_retries})"
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()

            except httpx.HTTPError as exc:
                logger.error(f"Erreur HTTP tentative {attempt + 1}: {exc}")
                if attempt < settings.max_retries - 1:
                    time.sleep(settings.retry_backoff ** attempt)

        raise RuntimeError(
            f"Échec après {settings.max_retries} tentatives — endpoint: {endpoint}"
        )

    def get_pokemon_expansions(self) -> list[dict]:
        """
        Retourne toutes les extensions du jeu Pokémon.
        Endpoint : GET /expansions/game/{idGame}
        """
        data = self._get(f"expansions/game/{POKEMON_GAME_ID}")
        expansions = data.get("expansion", [])
        logger.info(f"{len(expansions)} extensions Pokémon récupérées")
        return expansions

    def get_sealed_products(self, expansion_id: int) -> list[dict]:
        """
        Retourne les produits scellés d'une extension,
        filtrés sur Booster Box et Elite Trainer Box.

        Endpoint : GET /expansions/{idExpansion}/products
        Les produits scellés sont distincts des singles (cartes à l'unité).
        """
        data = self._get(f"expansions/{expansion_id}/products")
        all_products = data.get("product", [])

        matched = [
            p for p in all_products
            if p.get("categoryName") in TARGET_PRODUCT_TYPES
        ]

        if matched:
            logger.debug(
                f"Extension {expansion_id} → "
                f"{len(matched)} produit(s) ciblé(s) sur {len(all_products)} total"
            )
        return matched

    def get_product_articles(self, product_id: int) -> list[dict]:
        """
        Retourne TOUTES les offres actives d'un produit scellé.
        Chaque offre contient : langue, prix, quantité disponible.

        Endpoint : GET /products/{idProduct}/articles
        C'est à ce niveau qu'on collecte les données de marché réelles.
        """
        data = self._get(f"products/{product_id}/articles")
        articles = data.get("article", [])
        logger.debug(f"Produit {product_id} → {len(articles)} offre(s)")
        return articles

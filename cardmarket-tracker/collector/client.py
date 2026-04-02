"""
collector/client.py
Gestion des appels à l'API Cardmarket avec OAuth 1.0a,
retry exponentiel et journalisation.
"""

import logging
import time
from typing import Any

import httpx
from authlib.integrations.httpx_client import OAuth1Auth

from config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.cardmarket.com/ws/v2.0/output.json"

# Produits ciblés (selon accord API)
TARGET_CATEGORIES = ["Booster Box", "Elite Trainer Box"]


class CardmarketClient:
    def __init__(self):
        self.auth = OAuth1Auth(
            client_id=settings.cm_app_token,
            client_secret=settings.cm_app_secret,
            token=settings.cm_access_token,
            token_secret=settings.cm_access_token_secret,
        )

    def _request(self, endpoint: str) -> dict[str, Any]:
        """
        Appel HTTP GET avec retry exponentiel.
        Respecte les rate limits via backoff sur 429/503.
        """
        url = f"{BASE_URL}/{endpoint}"
        for attempt in range(settings.max_retries):
            try:
                with httpx.Client(auth=self.auth, timeout=30) as client:
                    response = client.get(url)

                logger.info(f"GET {endpoint} → {response.status_code}")

                if response.status_code == 200:
                    return response.json()

                if response.status_code in (429, 503):
                    wait = settings.retry_backoff ** attempt
                    logger.warning(f"Rate limit ({response.status_code}), retry dans {wait}s")
                    time.sleep(wait)
                    continue

                response.raise_for_status()

            except httpx.HTTPError as e:
                logger.error(f"Erreur HTTP tentative {attempt + 1}: {e}")
                if attempt < settings.max_retries - 1:
                    time.sleep(settings.retry_backoff ** attempt)

        raise RuntimeError(f"Échec après {settings.max_retries} tentatives : {endpoint}")

    def get_expansions(self) -> list[dict]:
        """Récupère toutes les extensions Pokémon disponibles."""
        data = self._request("expansions/game/3")  # game 3 = Pokémon
        return data.get("expansion", [])

    def get_products(self, expansion_id: int) -> list[dict]:
        """
        Récupère les produits d'une extension.
        Filtre uniquement Booster Box et Elite Trainer Box.
        """
        data = self._request(f"expansions/{expansion_id}/singles")
        products = data.get("single", [])
        return [
            p for p in products
            if any(cat in p.get("name", "") for cat in TARGET_CATEGORIES)
        ]

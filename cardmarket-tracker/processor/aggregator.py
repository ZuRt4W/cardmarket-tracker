"""
processor/aggregator.py
Transformation des données brutes en valeurs agrégées par langue.
Calcule min, max et moyenne des prix.
"""

from collections import defaultdict
from typing import Optional


SUPPORTED_LANGUAGES = {
    1: "fr", 2: "en", 3: "de", 4: "es", 5: "it",
    6: "pt", 7: "ja", 8: "ko", 9: "zh"
}


def aggregate_prices(product: dict) -> Optional[dict[str, dict]]:
    """
    À partir d'un produit brut retourné par l'API,
    calcule min/max/moyenne des prix par langue.

    Retourne None si aucune offre exploitable.
    """
    offers = product.get("offers", [])
    if not offers:
        return None

    # Grouper les prix par langue
    prices_by_lang: dict[str, list[float]] = defaultdict(list)

    for offer in offers:
        lang_id = offer.get("language", {}).get("idLanguage")
        price = offer.get("price")

        if lang_id and price is not None:
            lang_code = SUPPORTED_LANGUAGES.get(lang_id, f"lang_{lang_id}")
            try:
                prices_by_lang[lang_code].append(float(price))
            except (ValueError, TypeError):
                continue

    if not prices_by_lang:
        return None

    # Agrégation : min / max / moyenne
    result = {}
    for lang, prices in prices_by_lang.items():
        result[lang] = {
            "min": round(min(prices), 2),
            "max": round(max(prices), 2),
            "avg": round(sum(prices) / len(prices), 2),
            "count": len(prices),
        }

    return result

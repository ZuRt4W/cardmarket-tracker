"""
processor/aggregator.py

Transformation des articles bruts (offres Cardmarket) en valeurs agrégées.
Reçoit la liste brute des articles d'un produit et calcule,
par langue : prix minimum, maximum, moyenne et nombre d'offres.

Les articles bruts ne sont jamais stockés — seul ce résultat agrégé est conservé.
"""

from collections import defaultdict
from typing import Optional


SUPPORTED_LANGUAGES = {
    1: "fr", 2: "en", 3: "de", 4: "es", 5: "it",
    6: "pt", 7: "ja", 8: "ko", 9: "zh"
}


def aggregate_articles(articles: list[dict]) -> Optional[dict[str, dict]]:
    """
    Agrège une liste d'articles (offres) retournés par
    GET /products/{idProduct}/articles.

    Structure d'un article Cardmarket :
    {
        "idArticle": 123,
        "language": { "idLanguage": 1, "languageName": "French" },
        "price": 89.99,
        "count": 2,        # quantité disponible chez ce vendeur
        ...
    }

    Retourne un dict par langue avec min/max/avg/count,
    ou None si aucun article exploitable.
    """
    if not articles:
        return None

    # Regrouper les prix par langue
    prices_by_lang: dict[str, list[float]] = defaultdict(list)

    for article in articles:
        lang_id = article.get("language", {}).get("idLanguage")
        price = article.get("price")

        if lang_id is None or price is None:
            continue

        lang_code = SUPPORTED_LANGUAGES.get(lang_id, f"lang_{lang_id}")
        try:
            prices_by_lang[lang_code].append(float(price))
        except (ValueError, TypeError):
            continue

    if not prices_by_lang:
        return None

    # Calcul des agrégats par langue
    result = {}
    for lang, prices in prices_by_lang.items():
        result[lang] = {
            "min": round(min(prices), 2),
            "max": round(max(prices), 2),
            "avg": round(sum(prices) / len(prices), 2),
            "count": len(prices),  # nombre d'offres distinctes
        }

    return result

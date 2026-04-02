"""
tests/test_aggregator.py
Tests unitaires du module d'agrégation des articles.
"""

import pytest
from processor.aggregator import aggregate_articles


def make_articles(offers):
    """
    Construit une liste d'articles au format retourné par
    GET /products/{idProduct}/articles
    """
    return [
        {"language": {"idLanguage": lang_id}, "price": price}
        for lang_id, price in offers
    ]


def test_aggregate_single_language():
    articles = make_articles([(1, "10.00"), (1, "15.00"), (1, "20.00")])
    result = aggregate_articles(articles)
    assert result is not None
    assert "fr" in result
    assert result["fr"]["min"] == 10.0
    assert result["fr"]["max"] == 20.0
    assert result["fr"]["avg"] == 15.0
    assert result["fr"]["count"] == 3


def test_aggregate_multiple_languages():
    articles = make_articles([(1, "10.00"), (2, "12.00"), (3, "14.00")])
    result = aggregate_articles(articles)
    assert "fr" in result
    assert "en" in result
    assert "de" in result


def test_aggregate_empty_list():
    result = aggregate_articles([])
    assert result is None


def test_aggregate_invalid_price():
    articles = make_articles([(1, "N/A"), (1, "10.00")])
    result = aggregate_articles(articles)
    assert result["fr"]["count"] == 1


def test_aggregate_missing_language():
    articles = [{"price": "10.00"}]  # pas de champ language
    result = aggregate_articles(articles)
    assert result is None


def test_aggregate_unknown_language_id():
    articles = make_articles([(99, "50.00")])
    result = aggregate_articles(articles)
    assert "lang_99" in result  # langue inconnue conservée avec code générique

"""
tests/test_aggregator.py
Tests unitaires du module d'agrégation des prix.
"""

import pytest
from processor.aggregator import aggregate_prices


def make_product(offers):
    return {"name": "Test Box", "offers": offers}


def test_aggregate_single_language():
    product = make_product([
        {"language": {"idLanguage": 1}, "price": "10.00"},
        {"language": {"idLanguage": 1}, "price": "15.00"},
        {"language": {"idLanguage": 1}, "price": "20.00"},
    ])
    result = aggregate_prices(product)
    assert result is not None
    assert "fr" in result
    assert result["fr"]["min"] == 10.0
    assert result["fr"]["max"] == 20.0
    assert result["fr"]["avg"] == 15.0
    assert result["fr"]["count"] == 3


def test_aggregate_multiple_languages():
    product = make_product([
        {"language": {"idLanguage": 1}, "price": "10.00"},
        {"language": {"idLanguage": 2}, "price": "12.00"},
    ])
    result = aggregate_prices(product)
    assert "fr" in result
    assert "en" in result


def test_aggregate_no_offers():
    product = make_product([])
    result = aggregate_prices(product)
    assert result is None


def test_aggregate_invalid_price():
    product = make_product([
        {"language": {"idLanguage": 1}, "price": "N/A"},
        {"language": {"idLanguage": 1}, "price": "10.00"},
    ])
    result = aggregate_prices(product)
    assert result["fr"]["count"] == 1

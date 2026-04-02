"""
scripts/run_discovery.py
Force un cycle de découverte complet (scan des 527 extensions).
À utiliser : premier lancement, ou début d'une nouvelle saison.
Usage : python scripts/run_discovery.py
"""

import logging
from collector.pipeline import run_collection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    stats = run_collection(force_discovery=True)
    print(f"\nDécouverte terminée :")
    print(f"  Extensions scannées : {stats['expansions_scanned']}")
    print(f"  Produits enregistrés : {stats['products_matched']}")
    print(f"  Snapshots sauvegardés : {stats['snapshots_saved']}")
    print(f"  Erreurs : {stats['errors']}")

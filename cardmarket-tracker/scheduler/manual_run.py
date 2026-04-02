"""
scheduler/manual_run.py
Déclenchement manuel d'une collecte — utile pour les tests.
Usage : python -m scheduler.manual_run
"""

import logging
from collector.pipeline import run_collection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    count = run_collection()
    print(f"Collecte terminée : {count} snapshots enregistrés.")

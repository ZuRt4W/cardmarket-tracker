"""
scheduler/job.py
Planification quotidienne de la collecte via APScheduler.
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from collector.pipeline import run_collection
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler()


@scheduler.scheduled_job(
    "cron",
    hour=settings.collect_hour,
    minute=settings.collect_minute,
    id="daily_collection",
)
def daily_collection():
    logger.info("Démarrage de la collecte planifiée")
    try:
        count = run_collection()
        logger.info(f"Collecte réussie — {count} snapshots")
    except Exception as e:
        logger.error(f"Erreur lors de la collecte : {e}")


if __name__ == "__main__":
    logger.info(
        f"Scheduler démarré — collecte quotidienne à {settings.collect_hour:02d}:{settings.collect_minute:02d}"
    )
    scheduler.start()

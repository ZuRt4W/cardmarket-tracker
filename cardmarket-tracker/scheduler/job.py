"""
scheduler/job.py
Planification quotidienne — mode exploitation uniquement.
Le mode découverte se déclenche automatiquement si la base est vide,
ou manuellement via scripts/run_discovery.py.
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from collector.pipeline import run_collection
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler()


@scheduler.scheduled_job("cron", hour=settings.collect_hour,     minute=settings.collect_minute, id="morning_run")
def morning_run():
    logger.info("Cycle matin")
    run_collection()


@scheduler.scheduled_job("cron", hour=settings.collect_hour + 12, minute=settings.collect_minute, id="evening_run")
def evening_run():
    logger.info("Cycle soir")
    run_collection()


if __name__ == "__main__":
    logger.info("Scheduler démarré — 2 cycles quotidiens (matin + soir)")
    scheduler.start()

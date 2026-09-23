"""APScheduler monthly job + shared run state (prevents overlapping runs)."""
import logging
import threading
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

import mailer

logger = logging.getLogger(__name__)

JOB_ID = "monthly_email_job"

scheduler = BackgroundScheduler()
run_state = {"running": False, "last_run": None}
run_lock = threading.Lock()


def record_run(kind, result):
    run_state["last_run"] = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kind": kind,
        "result": result if isinstance(result, dict) else {"ok": True},
    }


def acquire_run_slot() -> bool:
    """Reserve the single run slot; False if another run is in progress."""
    with run_lock:
        if run_state["running"]:
            return False
        run_state["running"] = True
    return True


def release_run_slot():
    with run_lock:
        run_state["running"] = False


def scheduled_job():
    logger.info("Scheduled monthly email job starting.")
    if not acquire_run_slot():
        logger.info("Scheduled job skipped: a manual run is in progress.")
        record_run("scheduled", {"skipped": True, "reason": "a manual run is in progress"})
        return
    try:
        result = mailer.run_with_lock(mailer.send_all)
    except Exception as e:
        logger.exception("Scheduled job crashed")
        report = mailer.build_report(
            "scheduled",
            f"Scheduled job crashed: {type(e).__name__}: {e}",
            exc=e,
        )
        mailer.alert(f"Scheduled job crashed: {type(e).__name__}", report)
        result = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        release_run_slot()
    record_run("scheduled", result)


def ensure_job():
    cfg = mailer.load_config()
    scheduler.add_job(
        scheduled_job,
        trigger="cron",
        day=cfg["send_day"],
        hour=cfg["send_hour"],
        minute=cfg["send_minute"],
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info(
        f"Scheduled job set: day {cfg['send_day']} at "
        f"{cfg['send_hour']:02d}:{cfg['send_minute']:02d} monthly."
    )


def next_run_iso():
    try:
        job = scheduler.get_job(JOB_ID)
        if job and job.next_run_time:
            return job.next_run_time.isoformat(timespec="seconds")
    except Exception:
        pass
    return None


def start_manual(kind, address=None):
    """Start a manual send (test or full) in a background thread."""
    if not acquire_run_slot():
        return False

    def worker():
        try:
            if kind == "test":
                result = mailer.send_test(address)
            else:
                result = mailer.run_with_lock(mailer.send_all)
            record_run(kind, result)
        except Exception as e:
            logger.exception("Manual run crashed")
            report = mailer.build_report(
                "manual",
                f"Manual {kind} run crashed: {type(e).__name__}: {e}",
                exc=e,
            )
            mailer.alert(f"Manual {kind} run crashed: {type(e).__name__}", report)
            record_run(kind, {"ok": False, "error": f"{type(e).__name__}: {e}"})
        finally:
            release_run_slot()

    threading.Thread(target=worker, daemon=True).start()
    return True

"""
Email Automation - entry point.

One process that:
  * serves the settings/control web UI (http://127.0.0.1:8321)
  * runs the monthly scheduled send (APScheduler)
  * exposes manual actions: test email, send now, clear history, test alert

Modules:
  paths.py      shared filesystem paths
  app_logger.py rotating file + console logging setup
  mailer.py     SMTP sending, sent-history, locking, alert emails
  validator.py  email format + whitelist/blacklist rules
  env_store.py  .env / recipients.json persistence + validation
  jobs.py       scheduler + run state
  http_api.py   HTTP handler (routes)
  ui.py         the HTML page
"""
import argparse
import logging
from http.server import ThreadingHTTPServer

from dotenv import load_dotenv

import app_logger
import http_api
import jobs

load_dotenv()
app_logger.setup_logging()
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Email Automation server (UI + scheduler)")
    parser.add_argument("--port", type=int, default=8321)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-schedule", action="store_true",
                        help="Serve the UI only; do not start the scheduled job.")
    args = parser.parse_args()

    if not args.no_schedule:
        try:
            jobs.ensure_job()
            jobs.scheduler.start()
        except Exception as e:
            logger.error(f"Could not start scheduler: {e}")
            print(f"WARNING: scheduler not started: {e}")

    server = ThreadingHTTPServer((args.host, args.port), http_api.Handler)
    print(f"Email Automation running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if not args.no_schedule:
            try:
                jobs.scheduler.shutdown(wait=False)
            except Exception:
                pass
        server.server_close()


if __name__ == "__main__":
    main()

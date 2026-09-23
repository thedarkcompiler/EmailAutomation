"""HTTP handler: serves the UI and the /api/* endpoints."""
import json
import logging
from http.server import BaseHTTPRequestHandler

import env_store
import jobs
import mailer
import ui

logger = logging.getLogger(__name__)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        logger.info(fmt, *args)

    def _send(self, code, body, ctype):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), "application/json")

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _fail(self, code, message):
        """Respond with an error and email the alert address about it."""
        self._json(code, {"error": message})
        try:
            mailer.alert(f"Web server error ({self.path})", message)
        except Exception:
            logger.exception("Failed to send server-error alert")

    def do_GET(self):
        if self.path == "/":
            self._send(200, ui.PAGE, "text/html; charset=utf-8")
        elif self.path == "/api/state":
            try:
                self._json(200, env_store.state_payload(jobs.next_run_iso, jobs.run_state))
            except Exception as e:
                logger.exception("state failed")
                self._fail(500, f"Failed to build state: {e}")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        try:
            payload = self._read_json()
        except (ValueError, UnicodeDecodeError):
            self._fail(400, "Invalid JSON body.")
            return

        if not isinstance(payload, dict):
            self._fail(400, "Request body must be a JSON object.")
            return

        if self.path == "/api/settings":
            errors = env_store.validate_settings(payload)
            if errors:
                self._json(400, {"error": "\n".join(errors)})
                return
            try:
                env_store.save_env(payload)
            except OSError as e:
                self._fail(500, f"Could not write .env: {e}")
                return
            # apply to the live process
            env_store.apply_to_environ(payload)
            try:
                jobs.ensure_job()
            except Exception as e:
                logger.error(f"Failed to reschedule after save: {e}")
                self._fail(400, f"Saved, but scheduling failed: {e}")
                return
            self._json(200, {"ok": True})

        elif self.path == "/api/recipients":
            errors = env_store.validate_recipients(payload)
            if errors:
                self._json(400, {"error": "\n".join(errors)})
                return
            try:
                env_store.save_recipients(payload)
            except OSError as e:
                self._fail(500, f"Could not write recipients.json: {e}")
                return
            self._json(200, {"ok": True})

        elif self.path == "/api/test":
            address = str(payload.get("address") or "").strip()
            if not env_store.EMAIL_RE.match(address):
                self._json(400, {"error": f"Invalid test address: {address}"})
                return
            if not jobs.start_manual("test", address):
                self._json(409, {"error": "A send is already in progress."})
                return
            self._json(200, {"ok": True})

        elif self.path == "/api/send-now":
            if not jobs.start_manual("manual"):
                self._json(409, {"error": "A send is already in progress."})
                return
            self._json(200, {"ok": True})

        elif self.path == "/api/clear-history":
            mailer.clear_sent_history()
            self._json(200, {"ok": True})

        elif self.path == "/api/test-alert":
            if not (mailer.load_config().get("notify_email") or "").strip():
                self._json(400, {
                    "error": "Error alerts to (NOTIFY_EMAIL) is empty. "
                              "Set it in the SMTP & email section and save first."
                })
                return
            ok = mailer.test_alert()
            if ok:
                self._json(200, {"ok": True, "note": "Test alert sent."})
            else:
                self._fail(500, "The test alert itself could not be sent "
                                 "(SMTP unavailable or the address was rejected). "
                                 "Check mailer.log for the report.")

        else:
            self._send(404, "not found", "text/plain")

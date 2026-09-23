# Email Automation

Monthly email automation with a local web control panel. One Python process
serves the UI, runs the scheduled job, and can send manually.

## Quick start

```bash
pip install -r requirements.txt
python server.py            # http://127.0.0.1:8321
```

Open http://127.0.0.1:8321 in a browser. Everything is configurable there —
no need to edit files by hand.

Options:
- `python server.py --port 9000` — different port
- `python server.py --no-schedule` — UI only, no cron job (for testing)

## What the UI controls

| Section       | What it does |
|---------------|--------------|
| Overview      | Next scheduled run, job status, last run result, delivery progress |
| Actions       | Send test email, Send now (all unsent), Clear sent history, Test alert |
| SMTP & email  | Host, port, user, password, error-alert address, subject, max recipients, skip-already-sent toggle |
| Schedule      | Monthly cron: day (1–28), hour, minute |
| Recipients    | Add/remove/edit the recipient list (saved to `recipients.json`) |
| Domain rules  | Whitelist (allowed domains) and blacklist (blocked domains), each with an on/off toggle |

Changes are saved to `.env` (or `recipients.json`) and applied to the running
process immediately — the schedule is re-registered on save, no restart needed.

## Failure alerts

If you set **Error alerts to** in the SMTP & email section, any failure
emails you a detailed report: what failed, the exact error, likely causes,
suggested fixes, and a redacted snapshot of the active settings.

Alerts are sent when:
- a run has any failed recipients (each failure is listed with its reason)
- the SMTP connection/login fails
- a job crashes (includes the full traceback)
- the web server hits an error (e.g. `.env` can't be written)

Use **Actions → Test alert** to verify your alert address works.
If `NOTIFY_EMAIL` is empty, alerts are only written to `mailer.log`.

## Files

| File             | Purpose |
|------------------|---------|
| `server.py`      | Web UI + HTTP API + APScheduler cron job |
| `mailer.py`      | SMTP sending, sent-history, locking, alert emails |
| `validator.py`   | Email format + whitelist/blacklist rules |
| `email.html`     | Email template (`{{name}}` is replaced per recipient) |
| `.env`           | All settings (managed by the UI; keep it private) |
| `recipients.json`| Recipient list, format: `{"key": {"name": ..., "email": ...}}` |
| `sent.json`      | Which addresses were already sent (auto-managed) |
| `mailer.log`     | Log, rotates daily, keeps 7 days |

## Security notes

- `.env`, `recipients.json`, `sent.json` are in `.gitignore` — they are never
  committed.
- The server binds to `127.0.0.1` only. Do not expose it to a network without
  adding authentication.
- On Linux you can tighten permissions:

```bash
chmod 600 .env recipients.json sent.json
chmod 700 .
```

## Sending behavior

- **Scheduled run** — monthly at the configured day/hour/minute; sends only to
  recipients not in `sent.json` (when *Skip already-sent* is on).
- **Send now** — same as the scheduled run, on demand.
- **Test email** — single address, bypasses domain rules, not recorded in
  `sent.json`, subject prefixed with `[TEST]`.
- A file lock prevents two runs from overlapping; if the scheduled fire lands
  during a manual run, it is skipped and noted in the UI/log.
- If *Skip already-sent* is off, everyone in `recipients.json` is mailed on
  every run (sent history still updates with the latest time).

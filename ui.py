"""Web UI: the single HTML page served at / (markup, CSS, JS)."""

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Email Automation</title>
<style>
  :root {
    --bg: #0b1020;
    --card: #121a30;
    --card-2: #0e1526;
    --input: #0d1426;
    --border: rgba(148, 163, 184, .16);
    --border-strong: rgba(148, 163, 184, .3);
    --text: #e8edf8;
    --muted: #93a0ba;
    --faint: #64708a;
    --accent: #6366f1;
    --accent-2: #8b5cf6;
    --accent-soft: rgba(99, 102, 241, .16);
    --ok: #34d399;
    --ok-soft: rgba(52, 211, 153, .14);
    --err: #f87171;
    --err-soft: rgba(248, 113, 113, .14);
    --warn: #fbbf24;
    --warn-soft: rgba(251, 191, 36, .14);
    --radius: 14px;
    --shadow: 0 8px 24px rgba(2, 6, 23, .35);
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; color: var(--text); font-size: 15px;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    background:
      radial-gradient(1200px 500px at 80% -10%, rgba(99, 102, 241, .14), transparent 60%),
      radial-gradient(900px 420px at -10% 0%, rgba(139, 92, 246, .10), transparent 55%),
      var(--bg);
    background-attachment: fixed;
    min-height: 100vh;
  }
  ::selection { background: var(--accent-soft); }

  /* ---------- layout ---------- */
  .layout { display: flex; gap: 28px; max-width: 1120px; margin: 0 auto; padding: 24px 20px 110px; }
  aside { width: 210px; flex-shrink: 0; position: sticky; top: 24px; align-self: flex-start; }
  main { flex: 1; min-width: 0; }

  .brand { display: flex; align-items: center; gap: 10px; padding: 4px 10px 20px; }
  .brand .logo {
    width: 38px; height: 38px; border-radius: 11px; display: grid; place-items: center;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    box-shadow: 0 6px 18px rgba(99, 102, 241, .4); color: white;
  }
  .brand b { font-size: 15px; letter-spacing: .01em; display: block; }
  .brand span { font-size: 12px; color: var(--faint); }

  nav { display: flex; flex-direction: column; gap: 2px; }
  nav a {
    display: flex; align-items: center; gap: 10px; text-decoration: none;
    color: var(--muted); font-size: 13.5px; font-weight: 500;
    padding: 9px 12px; border-radius: 9px; transition: background .15s, color .15s;
  }
  nav a:hover { background: rgba(148, 163, 184, .08); color: var(--text); }
  nav a.active { background: var(--accent-soft); color: #c7d2fe; }
  nav a svg { flex-shrink: 0; opacity: .8; }

  /* ---------- cards / sections ---------- */
  section {
    background: linear-gradient(180deg, rgba(148, 163, 184, .045), rgba(148, 163, 184, .015)), var(--card);
    border: 1px solid var(--border); border-radius: var(--radius);
    margin-bottom: 18px; box-shadow: var(--shadow); overflow: hidden;
  }
  .sec-head {
    display: flex; align-items: center; gap: 10px;
    padding: 15px 20px; border-bottom: 1px solid var(--border);
  }
  .sec-head .ico {
    width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center;
    background: var(--accent-soft); color: #a5b4fc; flex-shrink: 0;
  }
  .sec-head h2 { margin: 0; font-size: 14.5px; font-weight: 600; letter-spacing: .01em; }
  .sec-head .sub { margin-left: auto; font-size: 12px; color: var(--faint); }
  .sec-body { padding: 4px 20px 16px; }

  .hint { color: var(--faint); font-size: 12.5px; padding: 2px 0 10px; line-height: 1.5; }

  /* ---------- rows & inputs ---------- */
  .row {
    display: flex; align-items: center; gap: 14px;
    padding: 11px 0; border-bottom: 1px solid rgba(148, 163, 184, .08);
  }
  .row:last-child { border-bottom: none; }
  .row > label { width: 190px; flex-shrink: 0; color: var(--muted); font-size: 13.5px; }
  input[type=text], input[type=password], input[type=number], select {
    flex: 1; min-width: 0; background: var(--input); color: var(--text);
    border: 1px solid var(--border-strong); border-radius: 9px;
    padding: 9px 12px; font-size: 14px; outline: none; font-family: inherit;
    transition: border-color .15s, box-shadow .15s;
  }
  input::placeholder { color: var(--faint); }
  input:focus, select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }
  select {
    appearance: none; -webkit-appearance: none; cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2393a0ba' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 12px center;
    padding-right: 34px;
  }
  select option { background: var(--card); color: var(--text); }
  input[type=number] { max-width: 130px; flex: 0 1 130px; }

  /* ---------- toggle ---------- */
  .toggle-row { display: flex; align-items: center; gap: 12px; padding: 10px 0 4px; }
  .toggle-row .lbl { font-weight: 600; font-size: 14px; }
  .toggle-row .state { font-size: 12px; color: var(--faint); }
  .switch { position: relative; width: 44px; height: 25px; flex-shrink: 0; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .slider {
    position: absolute; inset: 0; background: #33415e; border-radius: 25px;
    cursor: pointer; transition: .2s;
  }
  .slider:before {
    content: ""; position: absolute; width: 19px; height: 19px; left: 3px; top: 3px;
    background: #cbd5e1; border-radius: 50%; transition: .2s;
  }
  .switch input:checked + .slider { background: linear-gradient(135deg, var(--accent), var(--accent-2)); }
  .switch input:checked + .slider:before { transform: translateX(19px); background: #fff; }

  /* ---------- domain chips ---------- */
  .chips { display: flex; flex-wrap: wrap; gap: 8px; padding: 10px 0 4px; }
  .chip {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--card-2); border: 1px solid var(--border-strong);
    border-radius: 999px; padding: 6px 8px 6px 13px; font-size: 13px;
    animation: pop .18s ease;
  }
  .chip.allow { border-color: rgba(52, 211, 153, .35); background: var(--ok-soft); }
  .chip.block { border-color: rgba(248, 113, 113, .35); background: var(--err-soft); }
  .chip button {
    width: 19px; height: 19px; border-radius: 50%; border: none; cursor: pointer;
    background: rgba(148, 163, 184, .18); color: var(--muted);
    display: grid; place-items: center; font-size: 11px; line-height: 1;
    transition: background .15s, color .15s;
  }
  .chip button:hover { background: rgba(248, 113, 113, .25); color: var(--err); }
  .empty { color: var(--faint); font-size: 13px; font-style: italic; padding: 8px 0; }
  .add-row { display: flex; gap: 8px; padding: 8px 0 4px; }
  .add-row input { flex: 1; min-width: 0; }

  @keyframes pop { from { transform: scale(.92); opacity: 0; } to { transform: scale(1); opacity: 1; } }

  /* ---------- buttons ---------- */
  button.btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #fff;
    font-weight: 600; font-size: 13.5px; font-family: inherit;
    border: none; border-radius: 9px; padding: 9px 16px; cursor: pointer;
    transition: filter .15s, transform .05s, box-shadow .15s;
    box-shadow: 0 4px 14px rgba(99, 102, 241, .25);
  }
  button.btn:hover { filter: brightness(1.12); }
  button.btn:active { transform: translateY(1px); }
  button.btn:disabled { opacity: .45; cursor: not-allowed; filter: none; box-shadow: none; }
  button.btn.ghost {
    background: transparent; color: var(--muted);
    border: 1px solid var(--border-strong); box-shadow: none;
  }
  button.btn.ghost:hover { color: var(--text); border-color: var(--muted); filter: none; }
  button.btn.danger {
    background: transparent; color: var(--err);
    border: 1px solid rgba(248, 113, 113, .4); box-shadow: none;
  }
  button.btn.danger:hover { background: var(--err-soft); filter: none; }

  /* ---------- overview ---------- */
  .hero { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 14px; padding: 18px 20px; }
  .hero .cell {
    background: var(--card-2); border: 1px solid var(--border);
    border-radius: 11px; padding: 14px 16px; min-width: 0;
  }
  .hero .k {
    display: flex; align-items: center; gap: 7px;
    color: var(--faint); font-size: 11.5px; font-weight: 600;
    text-transform: uppercase; letter-spacing: .07em;
  }
  .hero .v { font-size: 19px; font-weight: 650; margin-top: 7px; word-break: break-word; }
  .hero .v small { font-size: 12.5px; font-weight: 500; color: var(--muted); display: block; margin-top: 3px; word-break: break-word; }
  .hero .v.ok { color: var(--ok); } .hero .v.err { color: var(--err); }

  .pulse {
    width: 8px; height: 8px; border-radius: 50%; background: var(--ok);
    animation: none; flex-shrink: 0;
  }
  .pulse.on { background: var(--warn); animation: pulse 1.2s ease-in-out infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }

  .progress-track {
    height: 8px; border-radius: 99px; background: rgba(148, 163, 184, .15);
    overflow: hidden; margin-top: 10px;
  }
  .progress-fill {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    transition: width .5s ease;
  }

  /* ---------- actions ---------- */
  .actions { display: flex; flex-wrap: wrap; gap: 10px; padding: 14px 0 4px; align-items: center; }
  .actions input { flex: 1; min-width: 240px; }

  /* ---------- recipients ---------- */
  .recip-head, .recip-row {
    display: grid; grid-template-columns: 1fr 1fr 34px; gap: 10px; align-items: center;
  }
  .recip-head {
    color: var(--faint); font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .08em; padding: 10px 0 6px;
  }
  .recip-row { padding: 5px 0; }
  .recip-row input { flex: 1; min-width: 0; }
  .icon-btn {
    width: 30px; height: 30px; border-radius: 8px; border: none; cursor: pointer;
    background: transparent; color: var(--faint); font-size: 17px; line-height: 1;
    display: grid; place-items: center; transition: background .15s, color .15s;
  }
  .icon-btn:hover { background: var(--err-soft); color: var(--err); }
  .section-foot { display: flex; gap: 10px; padding: 12px 0 2px; align-items: center; }
  .section-foot .note { color: var(--faint); font-size: 12.5px; flex: 1; }

  /* ---------- save bar ---------- */
  #savebar {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 30;
    display: flex; align-items: center; gap: 14px; padding: 13px 24px;
    background: rgba(11, 16, 32, .82); backdrop-filter: blur(12px);
    border-top: 1px solid var(--border);
  }
  #savebar .inner {
    width: 100%; max-width: 1120px; margin: 0 auto;
    display: flex; align-items: center; gap: 14px;
  }
  #dirty-pill {
    display: none; align-items: center; gap: 7px;
    font-size: 12.5px; font-weight: 600; color: var(--warn);
    background: var(--warn-soft); border: 1px solid rgba(251, 191, 36, .35);
    padding: 5px 12px; border-radius: 999px;
  }
  #dirty-pill.show { display: inline-flex; }
  #savebar .spacer { flex: 1; }
  kbd {
    font-family: inherit; font-size: 11px; color: var(--faint);
    border: 1px solid var(--border-strong); border-radius: 5px; padding: 1px 6px;
    background: var(--card-2);
  }

  /* ---------- toasts ---------- */
  #toasts { position: fixed; top: 18px; right: 18px; z-index: 50; display: flex; flex-direction: column; gap: 10px; }
  .toast {
    display: flex; align-items: flex-start; gap: 10px;
    background: var(--card); border: 1px solid var(--border-strong);
    border-left: 3px solid var(--accent);
    border-radius: 11px; padding: 12px 16px; max-width: 360px;
    box-shadow: var(--shadow); font-size: 13.5px; line-height: 1.45; white-space: pre-line;
    animation: slidein .25s ease;
  }
  .toast.ok { border-left-color: var(--ok); }
  .toast.err { border-left-color: var(--err); }
  .toast .t-ico { flex-shrink: 0; margin-top: 1px; }
  .toast.ok .t-ico { color: var(--ok); }
  .toast.err .t-ico { color: var(--err); }
  @keyframes slidein { from { transform: translateX(24px); opacity: 0; } to { transform: none; opacity: 1; } }
  .toast.hide { transition: opacity .3s, transform .3s; opacity: 0; transform: translateX(24px); }

  /* ---------- responsive ---------- */
  @media (max-width: 900px) {
    .layout { flex-direction: column; gap: 14px; padding-bottom: 120px; }
    aside { width: 100%; position: static; }
    .brand { padding-bottom: 10px; }
    nav { flex-direction: row; overflow-x: auto; padding-bottom: 4px; }
    nav a { white-space: nowrap; }
    .hero { grid-template-columns: 1fr; }
    .row { flex-direction: column; align-items: stretch; gap: 6px; }
    .row > label { width: auto; }
    .recip-head { display: none; }
    .recip-row { grid-template-columns: 1fr 1fr 34px; }
  }
</style>
</head>
<body>
<div class="layout">
  <aside>
    <div class="brand">
      <div class="logo">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
      </div>
      <div><b>Email Automation</b><span>control panel</span></div>
    </div>
    <nav id="nav">
      <a href="#overview" class="active"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h4l3-9 4 18 3-9h4"/></svg>Overview</a>
      <a href="#actions"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Actions</a>
      <a href="#smtp"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>SMTP &amp; email</a>
      <a href="#schedule"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>Schedule</a>
      <a href="#recipients"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>Recipients</a>
      <a href="#domains"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>Domain rules</a>
    </nav>
  </aside>
  <main id="main"></main>
</div>

<div id="savebar">
  <div class="inner">
    <span id="dirty-pill"><span>&#9679;</span>Unsaved changes</span>
    <span class="spacer"></span>
    <span style="color:var(--faint);font-size:12.5px"><kbd>Ctrl</kbd>+<kbd>S</kbd> saves settings</span>
    <button class="btn ghost" onclick="reloadAll()">Reload</button>
    <button class="btn" id="save-btn" onclick="saveSettings()">Save settings</button>
  </div>
</div>

<div id="toasts"></div>

<script>
let state = { settings: {}, recipients: [], sent_count: 0, total_recipients: 0,
              running: false, last_run: null, next_run: null };
let draft = { settings: {}, allowed: [], blocked: [], recipients: [] };
let dirty = false;

function $(s) { return document.querySelector(s); }
function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function markDirty() {
  if (!dirty) {
    dirty = true;
    $('#dirty-pill').classList.add('show');
  }
}
function clearDirty() {
  dirty = false;
  $('#dirty-pill').classList.remove('show');
}
function fmtTime(iso) {
  if (!iso) return 'not scheduled';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
       + ' · ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
const ICONS = {
  check: '<svg class="t-ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  x: '<svg class="t-ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
  info: '<svg class="t-ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
};

function toast(msg, kind = 'ok') {
  const el = document.createElement('div');
  el.className = 'toast ' + kind;
  el.innerHTML = (kind === 'err' ? ICONS.x : kind === 'info' ? ICONS.info : ICONS.check) + '<span>' + esc(msg) + '</span>';
  $('#toasts').appendChild(el);
  setTimeout(() => {
    el.classList.add('hide');
    setTimeout(() => el.remove(), 350);
  }, 4200);
}
const flash = (msg, isErr) => toast(msg, isErr ? 'err' : 'ok');

function render() {
  const s = draft.settings;
  $('#main').innerHTML = `
  <section id="overview">
    <div class="hero" id="hero"></div>
  </section>

  <section id="actions">
    <div class="sec-head">
      <div class="ico"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div>
      <h2>Actions</h2>
    </div>
    <div class="sec-body">
      <div class="actions">
        <input type="text" id="test-addr" placeholder="Test recipient address" value="${esc(s.SMTP_USER)}">
        <button class="btn" onclick="sendTest()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
          Send test email
        </button>
        <button class="btn" onclick="sendNow()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          Send now
        </button>
        <button class="btn danger" onclick="clearHistory()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          Clear history
        </button>
        <button class="btn ghost" onclick="sendTestAlert()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          Test alert
        </button>
      </div>
      <div class="hint">"Send now" mails every recipient not yet in the sent history. Test emails bypass domain rules and are not recorded in the history. "Test alert" emails your Error-alerts address to verify notifications work.</div>
    </div>
  </section>

  <section id="smtp">
    <div class="sec-head">
      <div class="ico"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></div>
      <h2>SMTP &amp; email</h2>
      <span class="sub">used by every send</span>
    </div>
    <div class="sec-body">
      <div class="row"><label>SMTP host</label><input type="text" data-k="SMTP_HOST" value="${esc(s.SMTP_HOST)}" placeholder="smtp.example.com"></div>
      <div class="row"><label>SMTP port</label><input type="number" data-k="SMTP_PORT" value="${esc(s.SMTP_PORT)}" min="1" max="65535"></div>
      <div class="row"><label>SMTP user (from)</label><input type="text" data-k="SMTP_USER" value="${esc(s.SMTP_USER)}" placeholder="mailer@example.com"></div>
      <div class="row"><label>Password / app password</label><input type="password" data-k="SMTP_PASSWORD" value="${esc(s.SMTP_PASSWORD)}"></div>
      <div class="row"><label>Error alerts to</label><input type="text" data-k="NOTIFY_EMAIL" value="${esc(s.NOTIFY_EMAIL)}" placeholder="you@example.com"></div>
      <div class="row"><label>Subject</label><input type="text" data-k="SUBJECT" value="${esc(s.SUBJECT)}"></div>
      <div class="row"><label>Max recipients</label><input type="number" data-k="MAX_RECIPIENTS" value="${esc(s.MAX_RECIPIENTS)}" min="1" max="1000000"></div>
      <div class="toggle-row" style="border-top:1px solid rgba(148,163,184,.08)">
        <label class="switch"><input type="checkbox" data-b="SKIP_SENT" ${s.SKIP_SENT !== false ? 'checked' : ''}><span class="slider"></span></label>
        <div><div class="lbl">Skip already-sent recipients</div><div class="state">when off, previously sent recipients are emailed again on every run</div></div>
      </div>
    </div>
  </section>

  <section id="schedule">
    <div class="sec-head">
      <div class="ico"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
      <h2>Schedule</h2>
      <span class="sub">monthly cron job</span>
    </div>
    <div class="sec-body">
      <div class="row"><label>Day of month</label><select data-k="SEND_DAY">${opts(1,28,s.SEND_DAY)}</select></div>
      <div class="row"><label>Hour</label><select data-k="SEND_HOUR">${opts(0,23,s.SEND_HOUR)}</select></div>
      <div class="row"><label>Minute</label><select data-k="SEND_MINUTE">${opts(0,59,s.SEND_MINUTE)}</select></div>
      <div class="hint" id="sched-preview"></div>
    </div>
  </section>

  <section id="recipients">
    <div class="sec-head">
      <div class="ico"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>
      <h2>Recipients</h2>
      <span class="sub" id="recip-count"></span>
    </div>
    <div class="sec-body">
      <div class="recip-head"><span>Name</span><span>Email</span><span></span></div>
      <div id="recip-list"></div>
      <div class="section-foot">
        <button class="btn ghost" onclick="addRecipient()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Add recipient
        </button>
        <span class="note"></span>
        <button class="btn" onclick="saveRecipients()">Save recipients</button>
      </div>
    </div>
  </section>

  <section id="domains">
    <div class="sec-head">
      <div class="ico"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
      <h2>Domain rules</h2>
      <span class="sub">applied at send time</span>
    </div>
    <div class="sec-body">
      <div class="toggle-row">
        <label class="switch"><input type="checkbox" data-b="ALLOWED_DOMAINS_ENABLED" ${s.ALLOWED_DOMAINS_ENABLED ? 'checked' : ''}><span class="slider"></span></label>
        <div><div class="lbl">Whitelist</div><div class="state">only send to addresses with an allowed domain</div></div>
      </div>
      <div class="chips" id="chips-allowed"></div>
      <div class="add-row">
        <input type="text" id="add-allowed" placeholder="e.g. example.com — press Enter">
        <button class="btn ghost" onclick="addDomain('allowed')">Add</button>
      </div>
      <hr style="border:none;border-top:1px solid rgba(148,163,184,.1);margin:16px 0">
      <div class="toggle-row">
        <label class="switch"><input type="checkbox" data-b="BLOCKED_DOMAINS_ENABLED" ${s.BLOCKED_DOMAINS_ENABLED ? 'checked' : ''}><span class="slider"></span></label>
        <div><div class="lbl">Blacklist</div><div class="state">never send to these domains</div></div>
      </div>
      <div class="chips" id="chips-blocked"></div>
      <div class="add-row">
        <input type="text" id="add-blocked" placeholder="e.g. spam.example.com — press Enter">
        <button class="btn ghost" onclick="addDomain('blocked')">Add</button>
      </div>
    </div>
  </section>`;

  document.querySelectorAll('[data-k]').forEach(el => {
    el.addEventListener('input', () => {
      draft.settings[el.dataset.k] = el.value;
      markDirty();
      if (el.dataset.k === 'SMTP_USER') $('#test-addr').value = el.value;
      if (el.dataset.k.startsWith('SEND_')) schedPreview();
      if (el.dataset.k === 'MAX_RECIPIENTS') recipCount();
    });
  });
  document.querySelectorAll('[data-b]').forEach(el =>
    el.addEventListener('change', () => { draft.settings[el.dataset.b] = el.checked; markDirty(); }));
  ['add-allowed','add-blocked'].forEach(id =>
    $('#' + id).addEventListener('keydown', e => {
      if (e.key === 'Enter') addDomain(id === 'add-allowed' ? 'allowed' : 'blocked');
    }));
  renderChips();
  renderRecipients();
  schedPreview();
  renderStatus();
}

function opts(lo, hi, sel) {
  let out = '';
  for (let i = lo; i <= hi; i++)
    out += `<option value="${i}" ${i === Number(sel) ? 'selected' : ''}>${i}</option>`;
  return out;
}

function renderChips() {
  for (const kind of ['allowed', 'blocked']) {
    const el = $(kind === 'allowed' ? '#chips-allowed' : '#chips-blocked');
    const items = draft[kind];
    el.innerHTML = items.length
      ? items.map((d, i) =>
          `<span class="chip ${kind === 'allowed' ? 'allow' : 'block'}">${esc(d)}<button title="Remove ${esc(d)}" onclick="removeDomain('${kind}', ${i})">&times;</button></span>`
        ).join('')
      : '<span class="empty">No domains — every domain passes this rule.</span>';
  }
}

function addDomain(kind) {
  const input = $(kind === 'allowed' ? '#add-allowed' : '#add-blocked');
  const v = input.value.trim().toLowerCase().replace(/\.+$/, '');
  if (!v) return;
  if (!/^[a-z0-9.-]+\.[a-z]{2,}$/.test(v)) { toast(`"${v}" is not a valid domain name.`, 'err'); return; }
  if (draft[kind].includes(v)) { toast(`"${v}" is already in the list.`, 'info'); return; }
  draft[kind].push(v);
  markDirty();
  renderChips();
  input.value = '';
  input.focus();
}
function removeDomain(kind, i) { draft[kind].splice(i, 1); markDirty(); renderChips(); }

function renderRecipients() {
  const el = $('#recip-list');
  el.innerHTML = draft.recipients.map((r, i) => `
    <div class="recip-row">
      <input type="text" value="${esc(r.name)}" placeholder="John Doe" data-ri="${i}" data-f="name">
      <input type="text" value="${esc(r.email)}" placeholder="john.doe@example.com" data-ri="${i}" data-f="email">
      <button class="icon-btn" title="Remove" onclick="removeRecipient(${i})">&times;</button>
    </div>`).join('') || '<div class="empty">No recipients yet — use "Add recipient" below.</div>';
  el.querySelectorAll('input').forEach(inp =>
    inp.addEventListener('input', () => { draft.recipients[+inp.dataset.ri][inp.dataset.f] = inp.value; markDirty(); }));
  recipCount();
}
function recipCount() {
  const max = Number(draft.settings.MAX_RECIPIENTS) || 0;
  const el = $('#recip-count');
  if (el) el.textContent = draft.recipients.length + (max ? ' / ' + max + ' max' : '');
}
function addRecipient() {
  draft.recipients.push({ name: '', email: '' });
  markDirty();
  renderRecipients();
  const inputs = document.querySelectorAll('#recip-list input');
  if (inputs.length) inputs[inputs.length - 2].focus();
}
function removeRecipient(i) { draft.recipients.splice(i, 1); markDirty(); renderRecipients(); }

function schedPreview() {
  const d = Number(draft.settings.SEND_DAY), h = Number(draft.settings.SEND_HOUR), m = Number(draft.settings.SEND_MINUTE);
  const ok = d >= 1 && d <= 28 && h >= 0 && h <= 23 && m >= 0 && m <= 59;
  const el = $('#sched-preview');
  if (el) el.textContent = ok
    ? `Runs every month on day ${d} at ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')} (local time). The schedule is applied immediately when you save.`
    : '';
}

function renderStatus() {
  const el = $('#hero');
  if (!el) return;
  const lr = state.last_run;
  let lastHtml = '<span style="color:var(--faint)">never</span>';
  if (lr) {
    const r = lr.result || {};
    let detail = '', cls = 'ok';
    if (lr.kind === 'test') { detail = r.ok ? 'delivered' : (r.error || 'failed'); if (!r.ok) cls = 'err'; }
    else if (r.skipped) { detail = 'skipped — another run was active'; cls = ''; }
    else {
      detail = `${r.success ?? 0} sent · ${r.failed ?? 0} failed · ${r.skipped ?? 0} already sent`;
      if ((r.failed ?? 0) > 0) cls = 'err';
    }
    if (r.error) { detail = r.error; cls = 'err'; }
    lastHtml = `<span class="${cls}">${esc(lr.kind)}</span><small>${esc(lr.time)} — ${esc(detail)}</small>`;
  }
  const unsent = Math.max(0, state.total_recipients - state.sent_count);
  const pct = state.total_recipients ? Math.round((state.sent_count / state.total_recipients) * 100) : 0;
  el.innerHTML = `
    <div class="cell">
      <div class="k">Next scheduled run</div>
      <div class="v">${esc(fmtTime(state.next_run))}</div>
    </div>
    <div class="cell">
      <div class="k"><span class="pulse ${state.running ? 'on' : ''}"></span>Job status</div>
      <div class="v ${state.running ? '' : 'ok'}">${state.running ? 'Running…' : 'Idle'}<small>${state.running ? 'emails are being sent' : 'scheduler active'}</small></div>
    </div>
    <div class="cell">
      <div class="k">Last run</div>
      <div class="v" style="font-size:15px;font-weight:600">${lastHtml}</div>
    </div>
    <div class="cell" style="grid-column:1 / -1">
      <div class="k">Delivery progress</div>
      <div class="v" style="font-size:14px;font-weight:600">${state.sent_count} of ${state.total_recipients} recipients sent${unsent ? ' · ' + unsent + ' waiting' : ' · all caught up'}</div>
      <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
    </div>`;
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, data };
}

function pollStatus() {
  api('/api/state').then(({ ok, data }) => {
    if (!ok) return;
    state = data;
    renderStatus();
  });
}

async function reloadAll() {
  const { ok, data } = await api('/api/state');
  if (!ok) { toast('Failed to load state.', 'err'); return; }
  state = data;
  draft.settings = { ...data.settings };
  draft.allowed = [...data.settings.ALLOWED_DOMAINS];
  draft.blocked = [...data.settings.BLOCKED_DOMAINS];
  draft.recipients = data.recipients.map(r => ({ name: r.name, email: r.email }));
  clearDirty();
  render();
}

async function saveSettings() {
  const payload = {
    SMTP_HOST: draft.settings.SMTP_HOST,
    SMTP_PORT: Number(draft.settings.SMTP_PORT),
    SMTP_USER: draft.settings.SMTP_USER,
    SMTP_PASSWORD: draft.settings.SMTP_PASSWORD,
    NOTIFY_EMAIL: draft.settings.NOTIFY_EMAIL,
    SUBJECT: draft.settings.SUBJECT,
    MAX_RECIPIENTS: Number(draft.settings.MAX_RECIPIENTS),
    SKIP_SENT: draft.settings.SKIP_SENT !== false,
    SEND_DAY: Number(draft.settings.SEND_DAY),
    SEND_HOUR: Number(draft.settings.SEND_HOUR),
    SEND_MINUTE: Number(draft.settings.SEND_MINUTE),
    ALLOWED_DOMAINS_ENABLED: !!draft.settings.ALLOWED_DOMAINS_ENABLED,
    BLOCKED_DOMAINS_ENABLED: !!draft.settings.BLOCKED_DOMAINS_ENABLED,
    ALLOWED_DOMAINS: draft.allowed,
    BLOCKED_DOMAINS: draft.blocked,
  };
  const btn = $('#save-btn');
  btn.disabled = true;
  const { ok, data } = await api('/api/settings', payload);
  btn.disabled = false;
  if (ok) { toast('Settings saved — schedule updated.'); await reloadAll(); }
  else toast(data.error || 'Save failed.', 'err');
}

async function saveRecipients() {
  const payload = {};
  for (const r of draft.recipients) {
    const key = (r.name || r.email || '').trim();
    if (!key) { toast('Every recipient needs a name or email.', 'err'); return; }
    if (key in payload) { toast('Duplicate entry: ' + key, 'err'); return; }
    payload[key] = { name: r.name.trim(), email: r.email.trim() };
  }
  const { ok, data } = await api('/api/recipients', payload);
  if (ok) { toast('Recipients saved.'); await reloadAll(); }
  else toast(data.error || 'Save failed.', 'err');
}

async function sendTest() {
  const address = $('#test-addr').value.trim();
  const { ok, data } = await api('/api/test', { address });
  if (ok) { toast('Test email queued to ' + address); pollStatus(); }
  else toast(data.error || 'Failed.', 'err');
}

async function sendNow() {
  const unsent = Math.max(0, state.total_recipients - state.sent_count);
  if (!confirm(`Send now to ${unsent} unsent recipient(s)?`)) return;
  const { ok, data } = await api('/api/send-now', {});
  if (ok) { toast('Send started — watch the job status.'); pollStatus(); }
  else toast(data.error || 'Failed.', 'err');
}

async function clearHistory() {
  if (!confirm('Clear the sent history? The next run will re-send to ALL recipients.')) return;
  const { ok, data } = await api('/api/clear-history', {});
  if (ok) { toast('Sent history cleared.'); reloadAll(); }
  else toast(data.error || 'Failed.', 'err');
}

async function sendTestAlert() {
  const { ok, data } = await api('/api/test-alert', {});
  if (ok) { toast(data.note || 'Test alert sent — check your inbox (and spam).'); }
  else toast(data.error || 'Failed to send the test alert.', 'err');
}

/* scrollspy for the sidebar */
function initSpy() {
  const links = [...document.querySelectorAll('#nav a')];
  const secs = links.map(a => $(a.getAttribute('href'))).filter(Boolean);
  const onScroll = () => {
    let current = secs[0];
    for (const s of secs) if (s.getBoundingClientRect().top <= 120) current = s;
    links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + current.id));
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault();
    saveSettings();
  }
});

reloadAll();
initSpy();
setInterval(pollStatus, 8000);
</script>
</body>
</html>
"""

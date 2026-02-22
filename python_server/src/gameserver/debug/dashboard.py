"""Tiny async HTTP server for the debug dashboard.

Serves a single auto-refreshing HTML page on a configurable port.
No external dependencies — uses only asyncio and stdlib.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Callable, Any

if TYPE_CHECKING:
    from gameserver.main import Services

from gameserver.debug.monitor import collect_snapshot
from gameserver.debug.signals import SIGNAL_CATALOG, get_signals_by_category

log = logging.getLogger(__name__)

# -------------------------------------------------------------------
# HTML template — self-contained, auto-refreshes every second
# -------------------------------------------------------------------

_DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>GameServer Debug</title>
<style>
  :root {
    --bg: #0d1117; --fg: #c9d1d9; --accent: #58a6ff;
    --green: #3fb950; --yellow: #d29922; --red: #f85149;
    --card-bg: #161b22; --border: #30363d;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    background: var(--bg); color: var(--fg);
    padding: 16px; font-size: 13px; line-height: 1.5;
  }
  h1 { color: var(--accent); font-size: 18px; margin-bottom: 12px; }
  h2 {
    color: var(--accent); font-size: 14px; margin-bottom: 6px;
    border-bottom: 1px solid var(--border); padding-bottom: 3px;
  }
  .grid {
    display: grid; gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  }
  .card {
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 6px; padding: 12px;
  }
  table { width: 100%; border-collapse: collapse; }
  td { padding: 2px 8px 2px 0; vertical-align: top; }
  td:first-child { color: #8b949e; white-space: nowrap; width: 45%; }
  .status-on { color: var(--green); }
  .status-off { color: var(--red); }
  .val-zero { color: #484f58; }
  .bar-outer {
    background: var(--border); border-radius: 3px; height: 8px;
    width: 120px; display: inline-block; vertical-align: middle;
  }
  .bar-inner {
    background: var(--green); height: 100%; border-radius: 3px;
    transition: width 0.3s;
  }
  #age { color: #484f58; font-size: 11px; }
  #error-banner {
    display: none; background: var(--red); color: #fff;
    padding: 6px 12px; border-radius: 4px; margin-bottom: 12px;
  }
  .event-list { max-height: 120px; overflow-y: auto; font-size: 12px; }
  .event-list div { padding: 1px 0; }
  .badge {
    display: inline-block; background: var(--border); color: var(--fg);
    border-radius: 3px; padding: 0 6px; font-size: 11px; margin-left: 4px;
  }
</style>
</head>
<body>
<div style="display:flex;align-items:center;gap:24px;margin-bottom:12px">
<h1 style="margin:0">&#x1f3ae; GameServer Debug Dashboard</h1>
<nav><a href="/" style="color:var(--accent);margin-right:12px">Status</a><a href="/signals" style="color:var(--accent)">&#x1f4e1; Signale senden</a></nav>
</div>
<div id="error-banner"></div>
<div id="age">loading …</div>
<div class="grid" id="panels"></div>

<script>
const API = '/api/state';
let lastOk = Date.now();

function val(v) {
  if (v === 0 || v === '0') return `<span class="val-zero">${v}</span>`;
  return v;
}

function tickBar(ms) {
  // 0 ms = 0%, 1000 ms = 100%  (shows how much of the tick budget is used)
  const pct = Math.min(ms, 1000) / 10;
  const color = pct < 30 ? 'var(--green)' : pct < 70 ? 'var(--yellow)' : 'var(--red)';
  return `<span class="bar-outer"><span class="bar-inner" style="width:${pct}%;background:${color}"></span></span> ${ms.toFixed(2)} ms`;
}

function renderCard(title, rows) {
  let html = `<div class="card"><h2>${title}</h2><table>`;
  for (const [k, v] of rows) {
    html += `<tr><td>${k}</td><td>${v}</td></tr>`;
  }
  html += '</table></div>';
  return html;
}

function renderEventBus(data) {
  let html = '<div class="card"><h2>&#x1f4e1; Event Bus</h2><table>';
  html += `<tr><td>Event types</td><td>${val(data.registered_events)}</td></tr>`;
  html += `<tr><td>Total handlers</td><td>${val(data.total_handlers)}</td></tr>`;
  html += '</table>';
  if (data.events && Object.keys(data.events).length > 0) {
    html += '<div class="event-list">';
    for (const [name, count] of Object.entries(data.events)) {
      html += `<div>${name} <span class="badge">${count}</span></div>`;
    }
    html += '</div>';
  }
  html += '</div>';
  return html;
}

function render(snap) {
  const gl = snap.game_loop || {};
  const srv = snap.server || {};
  const emp = snap.empires || {};
  const bat = snap.battles || {};
  const att = snap.attacks || {};
  const up = snap.upgrade_provider || {};
  const proc = snap.process || {};
  const bus = snap.event_bus || {};

  let html = '';

  // Game Loop
  const running = gl.running
    ? '<span class="status-on">&#x25cf; running</span>'
    : '<span class="status-off">&#x25cf; stopped</span>';
  html += renderCard('&#x1f504; Game Loop', [
    ['Status', running],
    ['Uptime', gl.uptime_fmt || '–'],
    ['Ticks', val(gl.tick_count || 0)],
    ['Last tick Δt', `${(gl.last_tick_dt_ms || 0).toFixed(1)} ms`],
    ['Last tick work', tickBar(gl.last_tick_work_ms || 0)],
    ['Avg tick work', tickBar(gl.avg_tick_work_ms || 0)],
  ]);

  // Server
  html += renderCard('&#x1f310; Network', [
    ['Listen', `${srv.host || '?'}:${srv.port || '?'}`],
    ['Connections', val(srv.connections || 0)],
    ['Connected UIDs', (srv.connected_uids || []).join(', ') || '–'],
  ]);

  // Empires
  const empDetails = emp.details || {};
  const empIds = Object.keys(empDetails);
  if (empIds.length === 0) {
    html += renderCard('&#x1f3f0; Empires', [['Count', val(0)]]);
  } else {
    for (const uid of empIds) {
      const e = empDetails[uid];
      const res = e.resources || {};
      const buildList = Object.entries(e.buildings || {})
        .map(([id, r]) => r > 0 ? `${id} (${r}s)` : `${id} &#x2705;`).join(', ') || '–';
      const knowList = Object.entries(e.knowledge || {})
        .map(([id, r]) => r > 0 ? `${id} (${r}s)` : `${id} &#x2705;`).join(', ') || '–';
      const cit = e.citizens || {};
      const citStr = Object.entries(cit).map(([t, n]) => `${t}: ${n}`).join(', ') || '–';
      const lifeBar = e.max_life > 0
        ? `<span class="bar-outer" style="width:80px"><span class="bar-inner" style="width:${(e.life/e.max_life*100).toFixed(0)}%;background:var(--red)"></span></span> ${e.life}/${e.max_life}`
        : `${e.life}`;
      html += renderCard(`&#x1f3f0; ${e.name || 'Empire'} (uid ${uid})`, [
        ['🪙 Gold', val(res.gold || 0)],
        ['🎭 Culture', val(res.culture || 0)],
        ['❤️ Life', lifeBar],
        ['Citizens', citStr],
        ['Buildings', buildList],
        ['Research', knowList],
        ['Structures', val(e.structures || 0)],
        ['Armies', val(e.armies || 0)],
        ['Artefacts', val(e.artefacts || 0)],
      ]);
    }
  }

  // Battles
  html += renderCard('&#x2694;&#xfe0f; Battles', [
    ['Active', val(bat.active || 0)],
  ]);

  // Attacks
  html += renderAttacks(att);

  // Upgrade Provider
  const byType = up.by_type || {};
  const typeRows = Object.entries(byType).map(([t, c]) => `${t}: ${c}`).join(', ') || '–';
  html += renderCard('&#x1f4e6; Items / Upgrades', [
    ['Items loaded', val(up.items_loaded || 0)],
    ['By type', typeRows],
  ]);

  // Event Bus
  html += renderEventBus(bus);

  // Process
  html += renderCard('&#x1f5a5;&#xfe0f; Process', [
    ['PID', proc.pid || '?'],
    ['Memory', `${proc.memory_mb || '?'} MB`],
    ['Server time', proc.time || '?'],
  ]);

  // Accounts
  const accts = snap.accounts || [];
  html += renderAccounts(accts);

  document.getElementById('panels').innerHTML = html;
}

function renderAccounts(accounts) {
  let html = '<div class="card" style="grid-column:1/-1;overflow-x:auto"><h2>&#x1f464; Accounts (' + accounts.length + ')</h2>';
  if (accounts.length === 0) {
    html += '<table><tr><td style="color:#484f58">No accounts</td></tr></table>';
  } else {
    html += '<table><tr style="color:var(--accent)"><td>UID</td><td>Username</td><td>Empire</td><td>Email</td><td>Created</td><td></td></tr>';
    for (const a of accounts) {
      html += `<tr><td>${a.uid}</td><td>${a.username}</td><td>${a.empire_name}</td><td>${a.email || '\u2013'}</td><td>${a.created_at || '\u2013'}</td>`;
      html += `<td><button onclick="deleteAccount('${a.username}')" style="background:var(--red);color:#fff;border:none;border-radius:3px;padding:2px 8px;cursor:pointer;font-size:11px">&#x1f5d1; Delete</button></td></tr>`;
    }
    html += '</table>';
  }
  html += '</div>';
  return html;
}

function renderAttacks(attacks) {
  let html = '<div class="card" style="grid-column:1/-1;overflow-x:auto"><h2>&#x1f6e1;&#xfe0f; Attacks (' + (attacks.total || 0) + ')</h2>';
  const list = attacks.attacks || [];
  if (list.length === 0) {
    html += '<table><tr><td style="color:#484f58">No active attacks</td></tr></table>';
  } else {
    html += '<table><tr style="color:var(--accent)"><td>ID</td><td>Attacker</td><td>Defender</td><td>Army ID</td><td>Phase</td><td>ETA (s)</td><td>Total ETA</td><td>Siege (s)</td><td>Total Siege</td></tr>';
    for (const a of list) {
      html += `<tr>`;
      html += `<td><code style="font-size:11px">${a.id}</code></td>`;
      html += `<td>${a.attacker}</td>`;
      html += `<td>${a.defender}</td>`;
      html += `<td>${a.army_aid}</td>`;
      html += `<td>${a.phase}</td>`;
      html += `<td style="text-align:right">${a.eta_seconds}</td>`;
      html += `<td style="text-align:right">${a.total_eta_seconds}</td>`;
      html += `<td style="text-align:right">${a.siege_remaining_seconds || 0}</td>`;
      html += `<td style="text-align:right">${a.total_siege_seconds || 30}</td>`;
      html += `</tr>`;
    }
    html += '</table>';
  }
  html += '</div>';
  return html;
}

async function deleteAccount(username) {
  if (!confirm('Account "' + username + '" wirklich löschen?')) return;
  try {
    const r = await fetch('/api/accounts/delete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username}),
    });
    const result = await r.json();
    if (result.ok) {
      poll();
    } else {
      alert('Delete failed: ' + (result.error || 'unknown'));
    }
  } catch (e) {
    alert('Delete error: ' + e.message);
  }
}

async function poll() {
  try {
    const r = await fetch(API);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const snap = await r.json();
    render(snap);
    lastOk = Date.now();
    document.getElementById('error-banner').style.display = 'none';
    document.getElementById('age').textContent =
      `Last update: ${new Date().toLocaleTimeString()}`;
  } catch (e) {
    const age = ((Date.now() - lastOk) / 1000).toFixed(0);
    const banner = document.getElementById('error-banner');
    banner.textContent = `Connection lost (${age}s ago): ${e.message}`;
    banner.style.display = 'block';
    document.getElementById('age').textContent = `Last successful update: ${age}s ago`;
  }
}

setInterval(poll, 1000);
poll();
</script>
</body>
</html>
"""


# -------------------------------------------------------------------
# Signals page — interactive forms to send messages to the router
# -------------------------------------------------------------------

_SIGNALS_HTML = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>GameServer Signals</title>
<style>
  :root {
    --bg: #0d1117; --fg: #c9d1d9; --accent: #58a6ff;
    --green: #3fb950; --yellow: #d29922; --red: #f85149;
    --card-bg: #161b22; --border: #30363d;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    background: var(--bg); color: var(--fg);
    padding: 16px; font-size: 13px; line-height: 1.5;
  }
  h1 { color: var(--accent); font-size: 18px; }
  h2 {
    color: var(--accent); font-size: 14px; margin: 16px 0 8px;
    border-bottom: 1px solid var(--border); padding-bottom: 3px;
    cursor: pointer; user-select: none;
  }
  h2:hover { color: var(--green); }
  h2::before { content: '\25B6  '; font-size: 10px; }
  h2.open::before { content: '\25BC  '; }
  .category { display: none; }
  .category.open { display: block; }
  .signal-card {
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;
  }
  .signal-title {
    color: var(--green); font-weight: bold; font-size: 13px;
    margin-bottom: 4px;
  }
  .signal-desc { color: #8b949e; font-size: 12px; margin-bottom: 8px; }
  .param-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
  .param-row label { color: #8b949e; width: 140px; font-size: 12px; }
  .param-row input, .param-row textarea {
    background: var(--bg); color: var(--fg); border: 1px solid var(--border);
    border-radius: 4px; padding: 3px 6px; font-family: inherit; font-size: 12px;
    flex: 1;
  }
  .param-row input:focus, .param-row textarea:focus {
    outline: none; border-color: var(--accent);
  }
  .param-hint { color: #484f58; font-size: 11px; margin-left: 4px; }
  button.send-btn {
    background: var(--accent); color: #fff; border: none;
    border-radius: 4px; padding: 4px 14px; cursor: pointer;
    font-family: inherit; font-size: 12px; margin-top: 6px;
  }
  button.send-btn:hover { background: #1f6feb; }
  button.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .result {
    font-size: 12px; margin-top: 4px; padding: 3px 8px;
    border-radius: 3px; display: none;
  }
  .result.ok { display: block; background: #0d2818; color: var(--green); max-height: 300px; overflow-y: auto; }
  .result.err { display: block; background: #2d0f0f; color: var(--red); }
  .result.noop { display: block; background: #1c1c00; color: var(--yellow); }
  #log-panel {
    margin-top: 20px; background: var(--card-bg);
    border: 1px solid var(--border); border-radius: 6px;
    padding: 10px 14px; max-height: 200px; overflow-y: auto;
  }
  #log-panel h3 { color: var(--accent); font-size: 13px; margin-bottom: 6px; }
  .log-entry { font-size: 11px; padding: 1px 0; border-bottom: 1px solid var(--border); }
  .log-time { color: #484f58; }
  .log-type { color: var(--accent); }
  .log-ok { color: var(--green); }
  .log-noop { color: var(--yellow); }
  .log-err { color: var(--red); }
  nav a { text-decoration: none; }
  nav a:hover { text-decoration: underline; }
</style>
</head>
<body>

<div style="display:flex;align-items:center;gap:24px;margin-bottom:12px">
<h1>&#x1f4e1; Signal Sender</h1>
<nav><a href="/" style="color:var(--accent);margin-right:12px">&#x1f3ae; Status</a><a href="/signals" style="color:var(--accent)">Signale senden</a></nav>
</div>

<p style="color:#8b949e;margin-bottom:16px;font-size:12px">
Sende Nachrichten an den Server-Router. Wenn kein Handler registriert ist, passiert nichts.
</p>

<div id="signals-container">Lade Signalkatalog…</div>

<div id="log-panel">
<h3>&#x1f4cb; Sende-Log</h3>
<div id="log-entries"></div>
</div>

<script>
let catalog = [];
const logEntries = [];

async function loadCatalog() {
  try {
    const resp = await fetch('/api/signals');
    const data = await resp.json();
    catalog = data.catalog;
    renderCatalog();
  } catch (e) {
    document.getElementById('signals-container').textContent = 'Fehler beim Laden: ' + e;
  }
}

function renderCatalog() {
  const container = document.getElementById('signals-container');
  container.innerHTML = '';

  // Group by category
  const cats = {};
  catalog.forEach(sig => {
    if (!cats[sig.category]) cats[sig.category] = [];
    cats[sig.category].push(sig);
  });

  Object.keys(cats).forEach(cat => {
    const h2 = document.createElement('h2');
    h2.textContent = cat;
    h2.onclick = () => {
      h2.classList.toggle('open');
      div.classList.toggle('open');
    };
    container.appendChild(h2);

    const div = document.createElement('div');
    div.className = 'category';
    cats[cat].forEach(sig => {
      div.appendChild(createSignalCard(sig));
    });
    container.appendChild(div);
  });

  // Open first category by default
  const firstH2 = container.querySelector('h2');
  const firstDiv = container.querySelector('.category');
  if (firstH2 && firstDiv) {
    firstH2.classList.add('open');
    firstDiv.classList.add('open');
  }
}

function createSignalCard(sig) {
  const card = document.createElement('div');
  card.className = 'signal-card';

  const title = document.createElement('div');
  title.className = 'signal-title';
  title.textContent = sig.type;
  card.appendChild(title);

  const desc = document.createElement('div');
  desc.className = 'signal-desc';
  desc.textContent = sig.description;
  card.appendChild(desc);

  const inputs = {};

  (sig.params || []).forEach(p => {
    const row = document.createElement('div');
    row.className = 'param-row';

    const label = document.createElement('label');
    label.textContent = p.name;
    row.appendChild(label);

    let input;
    if (p.type === 'JSON') {
      input = document.createElement('textarea');
      input.rows = 2;
      input.value = p.default !== undefined ? (typeof p.default === 'string' ? p.default : JSON.stringify(p.default)) : '';
    } else {
      input = document.createElement('input');
      if (p.type === 'INT' || p.type === 'FLOAT') {
        input.type = 'number';
        if (p.type === 'FLOAT') input.step = '0.1';
      } else {
        input.type = 'text';
      }
      input.value = p.default !== undefined ? String(p.default) : '';
    }
    input.placeholder = p.description || '';
    row.appendChild(input);
    inputs[p.name] = { el: input, type: p.type };

    card.appendChild(row);
  });

  const btn = document.createElement('button');
  btn.className = 'send-btn';
  btn.textContent = 'Senden';
  card.appendChild(btn);

  const result = document.createElement('div');
  result.className = 'result';
  card.appendChild(result);

  btn.onclick = async () => {
    btn.disabled = true;
    result.className = 'result';
    result.style.removeProperty('display');
    try {
      const payload = { type: sig.type };
      Object.keys(inputs).forEach(name => {
        const { el, type } = inputs[name];
        let val = el.value;
        if (type === 'INT') val = parseInt(val, 10) || 0;
        else if (type === 'FLOAT') val = parseFloat(val) || 0;
        else if (type === 'JSON') {
          try { val = JSON.parse(val); } catch (e) { /* keep string */ }
        }
        payload[name] = val;
      });

      const resp = await fetch('/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();

      if (data.ok && data.handled) {
        result.className = 'result ok';
        let txt = '\u2713 ' + data.message;
        if (data.response) {
          txt += '\n' + JSON.stringify(data.response, null, 2);
        }
        result.textContent = txt;
        result.style.whiteSpace = 'pre-wrap';
      } else if (data.ok && !data.handled) {
        result.className = 'result noop';
        result.textContent = '\u26A0 ' + data.message;
      } else {
        result.className = 'result err';
        result.textContent = '\u2717 ' + (data.error || 'Unbekannter Fehler');
      }

      addLogEntry(sig.type, data);
    } catch (e) {
      result.className = 'result err';
      result.textContent = '\u2717 Netzwerkfehler: ' + e;
      addLogEntry(sig.type, { ok: false, error: String(e) });
    } finally {
      btn.disabled = false;
    }
  };

  return card;
}

function addLogEntry(type, data) {
  const now = new Date().toLocaleTimeString('de');
  const el = document.createElement('div');
  el.className = 'log-entry';
  let cls = 'log-err';
  let status = 'ERROR';
  if (data.ok && data.handled) { cls = 'log-ok'; status = 'OK'; }
  else if (data.ok && !data.handled) { cls = 'log-noop'; status = 'NO-OP'; }
  const respHint = (data.response && data.response.type) ? ` \u2192 ${data.response.type}` : '';
  el.innerHTML = `<span class="log-time">${now}</span> <span class="log-type">${type}</span> <span class="${cls}">${status}${respHint}</span>`;
  const container = document.getElementById('log-entries');
  container.prepend(el);
  // Keep max 50 entries
  while (container.children.length > 50) container.removeChild(container.lastChild);
}

loadCatalog();
</script>
</body>
</html>
"""


class DebugDashboard:
    """Minimal async HTTP server that serves the debug dashboard.

    Routes:
    - ``GET /``              → HTML status dashboard
    - ``GET /signals``       → HTML signal sender page
    - ``GET /api/state``     → JSON snapshot of engine state (incl. accounts)
    - ``GET /api/signals``   → JSON signal catalog
    - ``POST /api/send``     → Send a signal to the router
    - ``POST /api/accounts/delete`` → Delete a user account

    Args:
        services: The Services container from main.py.
        host: Bind address (default ``"0.0.0.0"``).
        port: Bind port (default ``9000``).
    """

    def __init__(self, services: Services, host: str = "0.0.0.0", port: int = 9000) -> None:
        self._services = services
        self._host = host
        self._port = port
        self._server: asyncio.AbstractServer | None = None
        self._send_log: list[dict[str, Any]] = []  # last N sent signals

    async def start(self) -> None:
        """Start listening for HTTP connections."""
        self._server = await asyncio.start_server(
            self._handle_connection, self._host, self._port,
        )
        log.info("Debug dashboard running at http://%s:%d/", self._host, self._port)

    async def stop(self) -> None:
        """Stop the HTTP server."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    # -------------------------------------------------------------------
    # Internal HTTP handling
    # -------------------------------------------------------------------

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
    ) -> None:
        """Handle one HTTP connection (one request, then close)."""
        try:
            # Read headers
            raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=5.0)
            request_line = raw.split(b"\r\n")[0].decode("utf-8", errors="replace")
            headers_str = raw.decode("utf-8", errors="replace")
            parts = request_line.split()
            method = parts[0] if parts else "GET"
            path = parts[1] if len(parts) > 1 else "/"

            # Read body for POST
            body_data = b""
            if method == "POST":
                cl = 0
                for line in headers_str.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        cl = int(line.split(":", 1)[1].strip())
                        break
                if cl > 0:
                    body_data = await asyncio.wait_for(reader.readexactly(cl), timeout=5.0)

            # Route
            if method == "GET":
                await self._handle_get(writer, path)
            elif method == "POST":
                await self._handle_post(writer, path, body_data)
            else:
                await self._send_response(writer, 405, "text/plain", b"Method Not Allowed")

        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
            pass
        except asyncio.IncompleteReadError:
            pass
        except Exception as exc:
            log.debug("Debug dashboard request error: %s", exc)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _handle_get(self, writer: asyncio.StreamWriter, path: str) -> None:
        if path == "/api/state":
            snap = collect_snapshot(self._services)
            # Add accounts from DB (async)
            db = self._services.database
            snap["accounts"] = await db.list_users() if db else []
            body = json.dumps(snap, ensure_ascii=False, default=str).encode("utf-8")
            await self._send_response(writer, 200, "application/json", body)
        elif path == "/api/signals":
            payload = {
                "catalog": SIGNAL_CATALOG,
                "categories": list(get_signals_by_category().keys()),
                "log": self._send_log[-50:],
            }
            body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            await self._send_response(writer, 200, "application/json", body)
        elif path == "/" or path == "/index.html":
            body = _DASHBOARD_HTML.encode("utf-8")
            await self._send_response(writer, 200, "text/html; charset=utf-8", body)
        elif path == "/signals":
            body = _SIGNALS_HTML.encode("utf-8")
            await self._send_response(writer, 200, "text/html; charset=utf-8", body)
        else:
            await self._send_response(writer, 404, "text/plain", b"Not Found")

    async def _handle_post(self, writer: asyncio.StreamWriter, path: str, body_data: bytes) -> None:
        if path == "/api/accounts/delete":
            await self._handle_delete_account(writer, body_data)
            return
        if path != "/api/send":
            await self._send_response(writer, 404, "text/plain", b"Not Found")
            return

        try:
            payload = json.loads(body_data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            resp = json.dumps({"ok": False, "error": f"Invalid JSON: {e}"}).encode()
            await self._send_response(writer, 400, "application/json", resp)
            return

        msg_type = payload.get("type", "")
        sender_uid = payload.get("sender", 0)

        import time
        log_entry = {
            "time": time.strftime("%H:%M:%S"),
            "type": msg_type,
            "sender": sender_uid,
            "payload": payload,
            "result": "pending",
        }

        router = self._services.router
        if router is None:
            log_entry["result"] = "no_router"
            self._send_log.append(log_entry)
            resp = json.dumps({"ok": False, "error": "Router not available"}).encode()
            await self._send_response(writer, 503, "application/json", resp)
            return

        handler = router._handlers.get(msg_type)
        if handler is None:
            log_entry["result"] = "no_handler"
            self._send_log.append(log_entry)
            log.info("Signal sent (no handler): type=%s sender=%d", msg_type, sender_uid)
            resp = json.dumps({
                "ok": True,
                "handled": False,
                "message": f"Signal '{msg_type}' accepted — no handler registered yet",
            }).encode()
            await self._send_response(writer, 200, "application/json", resp)
            return

        try:
            result = await router.route(payload, sender_uid)
            log_entry["result"] = "handled"
            log_entry["response"] = result
            self._send_log.append(log_entry)
            log.info("Signal sent (handled): type=%s sender=%d", msg_type, sender_uid)
            resp_body: dict = {
                "ok": True,
                "handled": True,
                "message": f"Signal '{msg_type}' routed to handler",
            }
            if result is not None:
                resp_body["response"] = result
            resp = json.dumps(resp_body, ensure_ascii=False, default=str).encode()
            await self._send_response(writer, 200, "application/json", resp)
        except Exception as exc:
            log_entry["result"] = f"error: {exc}"
            self._send_log.append(log_entry)
            log.warning("Signal error: type=%s error=%s", msg_type, exc)
            resp = json.dumps({"ok": False, "error": str(exc)}).encode()
            await self._send_response(writer, 500, "application/json", resp)

    @staticmethod
    async def _send_response(
        writer: asyncio.StreamWriter,
        status: int,
        content_type: str,
        body: bytes,
    ) -> None:
        """Write a minimal HTTP/1.1 response."""
        reason = {200: "OK", 400: "Bad Request", 404: "Not Found",
                  405: "Method Not Allowed", 500: "Internal Server Error",
                  503: "Service Unavailable"}.get(status, "OK")
        header = (
            f"HTTP/1.1 {status} {reason}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n"
            f"Cache-Control: no-cache\r\n"
            f"\r\n"
        )
        writer.write(header.encode("utf-8"))
        writer.write(body)
        await writer.drain()

    async def _handle_delete_account(
        self, writer: asyncio.StreamWriter, body_data: bytes
    ) -> None:
        """Handle POST /api/accounts/delete — remove a user account."""
        try:
            payload = json.loads(body_data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            resp = json.dumps({"ok": False, "error": f"Invalid JSON: {e}"}).encode()
            await self._send_response(writer, 400, "application/json", resp)
            return

        username = payload.get("username", "")
        if not username:
            resp = json.dumps({"ok": False, "error": "Missing username"}).encode()
            await self._send_response(writer, 400, "application/json", resp)
            return

        db = self._services.database
        if db is None:
            resp = json.dumps({"ok": False, "error": "Database not available"}).encode()
            await self._send_response(writer, 503, "application/json", resp)
            return

        # Look up UID before deleting (to also remove the empire)
        user = await db.get_user(username)
        deleted = await db.delete_user(username)

        # Also remove the empire from the empire service if it exists
        if user and self._services.empire_service:
            self._services.empire_service.unregister(user["uid"])

        if deleted:
            log.info("Account deleted via debug dashboard: %s", username)
            resp = json.dumps({"ok": True, "message": f"Account '{username}' deleted"}).encode()
        else:
            resp = json.dumps({"ok": False, "error": f"User '{username}' not found"}).encode()
        await self._send_response(writer, 200, "application/json", resp)

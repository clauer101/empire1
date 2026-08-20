/**
 * Shared spy report overlay — renders the latest spy report for a target
 * empire. Used by the live spy_report WS event (army.js) and by the
 * "spy report" button in the known-empires lists (status.js, globalempires.js).
 */

import { escHtml } from './html.js';
import { _buildEraStatsHTML } from '../views/defense/era_data.js';
import { state } from '../state.js';

const OVERLAY_ID = 'shared-spy-report-overlay';
const BODY_ID = 'shared-spy-report-body';
const CLOSE_ID = 'shared-spy-report-close';

function _ensureOverlay() {
  let overlay = document.getElementById(OVERLAY_ID);
  if (overlay) return overlay;

  overlay = document.createElement('div');
  overlay.id = OVERLAY_ID;
  overlay.style.cssText = 'display:none;position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.65);align-items:center;justify-content:center;';
  overlay.innerHTML = `
    <div style="background:var(--panel-bg,#1e1e2e);border:1px solid rgba(150,100,220,0.5);border-radius:var(--radius,8px);padding:20px;min-width:280px;max-width:min(520px,92vw);max-height:80vh;overflow-y:auto;position:relative;">
      <button id="${CLOSE_ID}" style="position:absolute;top:8px;right:12px;background:none;border:none;cursor:pointer;color:#888;font-size:18px;line-height:1;">✕</button>
      <div id="${BODY_ID}"></div>
    </div>
  `;
  document.body.appendChild(overlay);

  document.getElementById(CLOSE_ID).addEventListener('click', hideSpyReportOverlay);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) hideSpyReportOverlay();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.style.display !== 'none') hideSpyReportOverlay();
  });

  return overlay;
}

/** Hide the shared spy-report overlay if visible. */
export function hideSpyReportOverlay() {
  const overlay = document.getElementById(OVERLAY_ID);
  if (overlay) overlay.style.display = 'none';
}

/**
 * Build the inner HTML body for a spy report payload. Shared by the overlay
 * (below) and by the standalone empire-details page.
 * @param {object} msg - shape: {defender_uid, defender_name, era, era_idx,
 *   placed_towers, path_length, artifacts?, ruler?, queues?, structures?, critters?, created_at?}
 */
export function buildSpyReportBodyHtml(msg) {
  const era = msg.era || '?';
  const defName = msg.defender_name || `Player ${msg.defender_uid}`;

  const structHtml = (msg.structures || [])
    .map((s) => {
      const upg = Object.entries(s.upgrades || {})
        .filter(([, v]) => v > 0)
        .map(([k, v]) => {
          const abbr = {
            damage: 'dmg',
            range: 'rng',
            reload: 'rld',
            effect_duration: 'eff_dur',
            effect_value: 'eff_val',
          };
          return `<span style="background:rgba(255,255,255,0.08);border-radius:3px;padding:1px 4px;font-size:11px;">${abbr[k] || k}+${v}</span>`;
        })
        .join(' ');
      return `<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
      <span>🗼 ${escHtml(s.name)}</span>
      <span>${upg || '<span style="opacity:0.4;font-size:11px;">no upgrades</span>'}</span>
    </div>`;
    })
    .join('');

  const critterHtml = (msg.critters || [])
    .map((c) => {
      const upg = Object.entries(c.upgrades || {})
        .filter(([, v]) => v > 0)
        .map(([k, v]) => {
          const abbr = { health: 'hp', speed: 'spd', armour: 'arm' };
          return `<span style="background:rgba(255,255,255,0.08);border-radius:3px;padding:1px 4px;font-size:11px;">${abbr[k] || k}+${v}</span>`;
        })
        .join(' ');
      return `<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
      <span>⚔ ${escHtml(c.name)}</span>
      <span>${upg || '<span style="opacity:0.4;font-size:11px;">no upgrades</span>'}</span>
    </div>`;
    })
    .join('');

  const eraDistHTML = _buildEraStatsHTML(msg.placed_towers || [], null, state.items?.catalog);

  const pathLenHtml = msg.path_length != null
    ? `<span style="background:rgba(255,255,255,0.08);border-radius:3px;padding:1px 6px;font-size:12px;font-family:monospace;">${msg.path_length} tiles</span>`
    : '<span style="opacity:0.4;font-size:12px;">unknown</span>';
  const towerCountHtml = `<span style="background:rgba(255,255,255,0.08);border-radius:3px;padding:1px 6px;font-size:12px;font-family:monospace;">${(msg.placed_towers || []).length}</span>`;

  const reportTimeHtml = msg.created_at
    ? `<div style="font-size:11px;color:var(--text-dim);margin-bottom:10px;">🕓 ${escHtml(new Date(msg.created_at).toLocaleString('de-DE'))}</div>`
    : '';

  return `
    <h3 style="margin:0 0 4px;font-size:15px;">🕵 Spy Report</h3>
    <div style="font-size:12px;color:var(--text-dim);margin-bottom:2px;">${escHtml(defName)}</div>
    ${reportTimeHtml}

    <div style="font-size:13px;font-weight:600;margin-bottom:6px;color:var(--accent,#4fc3f7);">🛡 Defense Intelligence</div>
    <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;margin-bottom:6px;">
      <div style="font-size:12px;margin-bottom:3px;">🛤 Path length: ${pathLenHtml}</div>
      <div style="font-size:12px;margin-bottom:8px;">🏰 Towers placed: ${towerCountHtml}</div>
      ${eraDistHTML}
    </div>

    <div style="font-size:13px;font-weight:600;margin-bottom:6px;margin-top:10px;color:var(--accent,#4fc3f7);">⚜ Artifacts</div>
    <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;margin-bottom:10px;">
      ${(msg.artifacts || []).length > 0
        ? (msg.artifacts).map((a) => {
            const name = typeof a === 'string' ? a : a.name;
            const prot = typeof a === 'object' && a.protected;
            const glow = prot ? 'box-shadow:0 0 8px 2px #4fc3f7,0 0 2px #4fc3f7;border:1px solid #4fc3f7;border-radius:4px;padding:0 4px;' : '';
            const tag = prot ? ' <span style="font-size:0.75em;color:#4fc3f7;">🔒 protected</span>' : '';
            return `<div style="padding:2px 0;font-size:12px;${glow}">⚜ ${escHtml(name)}${tag}</div>`;
          }).join('')
        : '<div style="opacity:0.4;font-size:12px;">none</div>'}
    </div>

    <div style="font-size:13px;font-weight:600;margin-bottom:6px;margin-top:10px;color:var(--accent,#4fc3f7);">👑 Ruler</div>
    <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;margin-bottom:10px;">
      ${msg.ruler
        ? `<div style="font-size:12px;">👑 ${escHtml(msg.ruler.name)} &mdash; <span style="color:#aaa">Lv ${msg.ruler.level}</span></div>`
        : '<div style="opacity:0.4;font-size:12px;">none</div>'}
    </div>

    <div style="font-size:13px;font-weight:600;margin-bottom:6px;margin-top:10px;color:var(--accent,#4fc3f7);">🔬 Workshop Intelligence &mdash; ${escHtml(era)}</div>
    <div style="border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;">
      <div style="font-size:12px;color:var(--text-dim);margin-bottom:4px;">Towers</div>
      <div style="margin-bottom:10px;">${structHtml || '<div style="opacity:0.4;font-size:12px;">none</div>'}</div>
      <div style="font-size:12px;color:var(--text-dim);margin-bottom:4px;">Units</div>
      <div>${critterHtml || '<div style="opacity:0.4;font-size:12px;">none</div>'}</div>
    </div>
  `;
}

/**
 * Build and show the shared spy-report overlay for a given report payload.
 * @param {object} msg - see {@link buildSpyReportBodyHtml}
 */
export function showSpyReportOverlay(msg) {
  const overlay = _ensureOverlay();
  const body = document.getElementById(BODY_ID);
  body.innerHTML = buildSpyReportBodyHtml(msg);
  overlay.style.display = 'flex';
}

/**
 * Ruler detail view — standalone, independent of status.js.
 */

import { rest } from '../rest.js';
import { pageTitle } from '../lib/page_title.js';
import { formatEffect } from '../i18n.js';
import { fmtEffectValue } from '../lib/format.js';
import { showChooseRulerOverlay } from './status.js';

/** @type {HTMLElement} */
let container;
/** @type {import('../state.js').StateStore} */
let st;

// ── Init ─────────────────────────────────────────────────────────────

function init(el, _api, state) {
  container = el;
  st = state;
  container.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow-y:auto;overflow-x:hidden;';
}

async function enter() {
  pageTitle.set('👑 Ruler');
  _renderLoading();
  await _load();
  if (window.innerWidth <= 600) {
    document.getElementById('app')?.style.setProperty('overflow', 'hidden', 'important');
  }
}

function leave() {
  document.getElementById('app')?.style.removeProperty('overflow');
  const bg = document.getElementById('ruler-mobile-bg');
  bg?._cleanup?.();
  bg?.remove();
}

// ── Data ─────────────────────────────────────────────────────────────

async function _load() {
  try {
    const [summary] = await Promise.all([rest.getSummary(), rest.getItems()]);
    _render(summary, st?.items?.rulers);
  } catch (e) {
    container.innerHTML = `<div style="padding:16px"><div class="error-msg">${e.message}</div></div>`;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────

function _skillUpState(ruler, skill) {
  const level = ruler.level || 1;
  const totalPoints = (ruler.q || 0) + (ruler.w || 0) + (ruler.e || 0) + (ruler.r || 0);
  const hasPoint = totalPoints < level;
  const current = ruler[skill] || 0;
  if (skill === 'q' || skill === 'w' || skill === 'e') {
    if (current >= 5) return { can: false, muted: false, hint: null };
    if (current + 1 === 5 && hasPoint && level < 9) return { can: false, muted: true, hint: 'Requires ruler level 9' };
    return { can: hasPoint, muted: false, hint: null };
  }
  const unlockLevels = [6, 11, 16];
  if (current >= unlockLevels.length) return { can: false, muted: false, hint: null };
  if (!hasPoint) return { can: false, muted: false, hint: null };
  if (level < unlockLevels[current]) return { can: false, muted: true, hint: `Requires ruler level ${unlockLevels[current]}` };
  return { can: true, muted: false, hint: null };
}

// ── Render ────────────────────────────────────────────────────────────

function _renderLoading() {
  container.innerHTML = `<div style="padding:16px"><div class="panel-row"><span class="value" style="color:#666">Loading…</span></div></div>`;
}


function _panelOverlayHtml(rulerDisplayName, ruler, pct, atMax, xpTarget, skillCards, withBgImg, splash, combatStats, canChange) {
  return `
    <div style="position:relative;overflow:hidden;padding:0;${withBgImg ? 'background:var(--surface);border:1px solid var(--border-color,#333);border-radius:var(--radius,6px);' : ''}" id="ruler-panel-wrap${withBgImg ? '' : '-mobile'}">
      ${withBgImg && splash ? `<img src="${splash}" style="width:100%;display:block;opacity:0.5;object-fit:cover;object-position:top;" alt="">` : ''}

      <!-- XP + progress bar pinned to top -->
      <div style="position:absolute;top:0;left:0;right:0;z-index:2;padding:10px 14px;background:linear-gradient(to bottom,rgba(14,14,22,0.75) 0%,rgba(14,14,22,0) 100%);">
        <div style="display:flex;justify-content:space-between;font-size:0.82em;color:#ccc;padding-bottom:4px">
          <span style="font-weight:700;font-size:1.1em">${rulerDisplayName} <span style="font-weight:400;color:#aaa;font-size:0.85em">Lv ${ruler.level}</span></span>
          <span style="color:#aaa">${atMax ? 'max level' : `${Math.floor(ruler.xp)} / ${Math.ceil(xpTarget)} XP`}</span>
        </div>
        <div class="atk-progress-wrap">
          <div class="atk-progress-bar" style="width:${pct}%;background:#66bb6a"></div>
        </div>
        ${combatStats ? `<div style="display:flex;gap:10px;margin-top:6px;font-size:0.78em;color:#ccc;flex-wrap:wrap;">
          <span>❤ ${Math.round(combatStats.health)}</span>
          <span>🛡 ${combatStats.armour.toFixed(1)}</span>
          <span>⚡ ${combatStats.speed.toFixed(2)}</span>
          <span>⚔ ${combatStats.damage.toFixed(1)}</span>
        </div>
        <div style="color:#888;font-size:0.72em;margin-top:3px;">Earn XP by sending this ruler on attacks.</div>` : ''}
      </div>

      <!-- Skills pinned to bottom -->
      <div style="position:absolute;bottom:32px;left:0;right:0;z-index:2;padding:6px 0 0;display:flex;flex-direction:column;gap:4px;">
        ${skillCards}
        <div style="text-align:center;padding:6px 0 2px">
          ${canChange
            ? `<a id="change-ruler-link" href="#" style="font-size:0.78em;color:#888;text-decoration:underline;cursor:pointer">change ruler</a>`
            : `<span style="font-size:0.72em;color:#555">locked — R skill upgraded</span>`}
        </div>
      </div>
    </div>`;
}

function _render(summary, rulersCatalog) {
  const ruler = summary.ruler;
  const empireEffects = summary.effects || {};
  const rulerUnlocked = (empireEffects?.ruler_unlock ?? 0) > 0;

  if (!rulerUnlocked && (!ruler || !ruler.type)) {
    container.innerHTML = `<div style="padding:16px"><div class="panel-row"><span class="value" style="color:#666">Ruler system not unlocked yet.</span></div></div>`;
    return;
  }

  if (!ruler || !ruler.type) {
    container.innerHTML = `
      <div style="padding:16px;max-width:600px;box-sizing:border-box;">
        <div class="panel">
          <div class="panel-header">👑 Ruler</div>
          <div style="color:#aaa;font-size:0.9em;line-height:1.6;padding:6px 0">
            <p style="margin:0 0 8px">Your empire has unlocked the ruler system.</p>
            <p style="margin:0 0 12px">Rulers are powerful heroes that can lead your armies into battle, granting unique combat bonuses scaled with their level.</p>
            <button id="choose-ruler-btn" style="background:#ffa726;color:#111;border:none;border-radius:4px;padding:6px 18px;font-weight:700;cursor:pointer;font-size:0.95em">Select a ruler</button>
          </div>
        </div>
      </div>`;
    container.querySelector('#choose-ruler-btn')?.addEventListener('click', () => showChooseRulerOverlay(rulersCatalog, _load));
    return;
  }

  const def = rulersCatalog?.[ruler.type];
  const rulerDisplayName = def?.name || ruler.name || ruler.type;
  const splash = def?.splash || '';

  const xpStart = ruler.level_xp_start || 0;
  const stepCost = ruler.next_level_xp || 1;
  const xpTarget = xpStart + stepCost;
  const xpInLevel = ruler.xp - xpStart;
  const pct = Math.min(100, (xpInLevel / stepCost) * 100).toFixed(1);
  const atMax = ruler.level >= 18;

  const SKILLS = [
    { key: 'q', label: 'Q' },
    { key: 'w', label: 'W' },
    { key: 'e', label: 'E' },
    { key: 'r', label: 'R' },
  ];
  const _LUMP_SUM_KEYS = new Set(['gold_lump_sum_on_skill_up', 'culture_lump_sum_on_skill_up']);

  const skillCards = SKILLS.map(({ key, label }) => {
    const level = ruler[key] || 0;
    const skillDef = def?.skills?.[key];
    const name = skillDef?.name || label;
    const upState = _skillUpState(ruler, key);
    const upBtn = (upState.can || upState.muted)
      ? `<button class="ruler-skill-up-btn" data-skill="${key}" style="padding:1px 8px;font-size:0.78em;border-radius:3px;font-weight:700;border:none;line-height:1.4;${upState.can ? 'cursor:pointer;background:#ffa726;color:#111' : 'cursor:default;background:#444;color:#666'}" ${upState.can ? '' : 'disabled'} title="${upState.hint || 'Spend skill point'}">${upState.muted ? '🔒' : '+'}</button>`
      : '';
    const currentEffects = level > 0 ? (skillDef?.levels?.[level - 1] || {}) : {};
    const nextLevelEffects = skillDef?.levels?.[level] || null;
    const effectLines = Object.entries(skillDef?.levels?.[0] || {}).map(([k]) => {
      try {
        const isLumpSum = _LUMP_SUM_KEYS.has(k);
        const curVal = level > 0 ? currentEffects[k] : null;
        const nxtVal = nextLevelEffects?.[k];
        const desc = formatEffect(k, curVal ?? (nxtVal ?? 0)).replace(/ \(.*\)$/, '');
        const curStr = isLumpSum && level > 0
          ? `<span style="color:#81c784">${fmtEffectValue(k, curVal)} ✓</span>`
          : curVal != null
            ? `<span style="color:#81c784">${fmtEffectValue(k, curVal)}</span>`
            : `<span style="color:#555">not learned</span>`;
        const nxtStr = nxtVal != null && nextLevelEffects
          ? `<span style="color:#555;font-size:0.82em"> (next: ${fmtEffectValue(k, nxtVal)})</span>`
          : '';
        return `<div style="font-size:0.82em;color:#ccc;margin-top:2px">${desc}: ${curStr}${nxtStr}</div>`;
      } catch (_) { return ''; }
    }).join('');
    const maxLvl = key === 'r' ? 3 : 5;
    const dots = Array.from({length: maxLvl}, (_, i) =>
      `<span style="display:inline-block;width:9px;height:9px;border-radius:50%;border:1.5px solid #66bb6a;background:${i < level ? '#66bb6a' : 'transparent'}"></span>`
    ).join('');
    return `<div style="padding:2px 14px;background:rgba(0,0,0,0.35);">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;">
        <div style="min-width:0;">
          <div style="font-weight:600;font-size:0.82em;color:#ddd;line-height:1.2;">${name}</div>
          ${effectLines}
          <div style="display:flex;gap:3px;margin-top:2px;">${dots}</div>
        </div>
        <div style="display:flex;align-items:center;gap:4px;flex-shrink:0;">
          ${upState.muted && upState.hint ? `<span style="font-size:0.7em;color:#555">${upState.hint}</span>` : ''}
          ${upBtn}
        </div>
      </div>
    </div>`;
  }).join('');

  const combatStats = ruler.combat_stats || null;
  const canChange = (ruler.r || 0) === 0;
  const sharedOverlay = (withBg) => _panelOverlayHtml(rulerDisplayName, ruler, pct, atMax, xpTarget, skillCards, withBg, splash, combatStats, canChange);

  container.innerHTML = `
    <!-- Desktop: image inside panel, max 500px -->
    <div id="ruler-desktop-wrap" style="padding:16px;width:100%;box-sizing:border-box;max-width:500px;">
      ${sharedOverlay(true)}
    </div>

    <!-- Mobile: image fixed as page background, panel transparent, full width -->
    <div id="ruler-mobile-wrap" style="display:none;width:100%;position:relative;z-index:1;padding:0;margin:0;overflow:hidden;">
      ${sharedOverlay(false)}
    </div>

    ${splash ? `<div id="ruler-mobile-bg" style="display:none;position:fixed;z-index:0;left:0;right:0;bottom:-1px;pointer-events:none;">
      <img src="${splash}" style="width:100%;height:100%;object-fit:cover;object-position:top;opacity:0.4;" alt="">
    </div>` : ''}

    <style>
      @media (max-width:600px) {
        #ruler-desktop-wrap { display:none !important; }
        #ruler-mobile-wrap  { display:block !important; }
        #ruler-mobile-bg    { display:block !important; }
        #app { padding:0 !important; }
      }
    </style>`;

  // On mobile: position the fixed bg below #page-header, and size the mobile panel to fill available space
  if (splash) {
    const bg = container.querySelector('#ruler-mobile-bg');
    const mobilePanel = container.querySelector('#ruler-panel-wrap-mobile');
    const header = document.getElementById('page-header');
    const update = () => {
      const top = header ? header.getBoundingClientRect().bottom : 0;
      if (bg) bg.style.top = `${top}px`;
      if (mobilePanel) {
        mobilePanel.style.height = `${window.innerHeight - top}px`;
        mobilePanel.style.minHeight = 'unset';
      }
    };
    update();
    window.addEventListener('resize', update);
    if (bg) bg._cleanup = () => window.removeEventListener('resize', update);
  }

  _bindEvents(rulersCatalog);
}

function _showChangeRulerOverlay(rulersCatalog) {
  document.querySelector('.change-ruler-confirm-overlay')?.remove();
  const overlay = document.createElement('div');
  overlay.className = 'change-ruler-confirm-overlay tt-overlay visible';
  overlay.innerHTML = `
    <div class="tt-panel" style="max-width:340px">
      <button class="tt-close">&times;</button>
      <div class="tt-dp-name" style="color:#ffa726">👑 Change Ruler</div>
      <div class="tt-dp-desc" style="margin-top:10px;font-style:normal;line-height:1.7;font-size:0.92em">
        <p style="margin-bottom:10px">Changing your ruler will permanently remove your current ruler and <strong style="color:#ef5350">reset all XP, levels, and skill points</strong>.</p>
        <p>You can then select a new ruler from the available options.</p>
      </div>
      <div style="display:flex;gap:10px;margin-top:16px">
        <button id="change-ruler-cancel" style="flex:1;background:#4fc3f7;color:#111;border:none;border-radius:4px;padding:8px 0;font-weight:700;cursor:pointer">Cancel</button>
        <button id="change-ruler-confirm" style="flex:1;background:#333;color:#ccc;border:1px solid #555;border-radius:4px;padding:8px 0;cursor:pointer">Change Ruler</button>
      </div>
      <div id="change-ruler-error" style="color:#ef9a9a;font-size:0.85em;margin-top:8px;min-height:1em;text-align:center"></div>
    </div>
  `;
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.classList.contains('tt-close')) overlay.remove();
  });
  overlay.querySelector('#change-ruler-cancel').addEventListener('click', () => overlay.remove());
  overlay.querySelector('#change-ruler-confirm').addEventListener('click', async () => {
    const btn = overlay.querySelector('#change-ruler-confirm');
    const errEl = overlay.querySelector('#change-ruler-error');
    btn.disabled = true;
    errEl.textContent = '';
    try {
      const resp = await rest.dismissRuler();
      if (resp?.success) {
        overlay.remove();
        showChooseRulerOverlay(rulersCatalog, _load);
      } else {
        errEl.textContent = resp?.error || 'Could not change ruler';
        btn.disabled = false;
      }
    } catch (e) {
      errEl.textContent = e.message;
      btn.disabled = false;
    }
  });
  document.body.appendChild(overlay);
}

function _bindEvents(rulersCatalog) {
  container.querySelector('#choose-ruler-btn')?.addEventListener('click', () =>
    showChooseRulerOverlay(rulersCatalog, _load)
  );
  container.querySelectorAll('.ruler-skill-up-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        const resp = await rest.rulerSkillUp(btn.dataset.skill);
        if (resp?.success) await _load();
        else btn.disabled = false;
      } catch (_) { btn.disabled = false; }
    });
  });
  container.querySelectorAll('#change-ruler-link').forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      _showChangeRulerOverlay(rulersCatalog);
    });
  });
}

export default {
  id: 'ruler',
  title: 'Ruler',
  init,
  enter,
  leave,
};

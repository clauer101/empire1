/**
 * Trophies — persistent achievements that survive season resets.
 *
 * Shows earned trophies (highlighted) and unearned trophies (dimmed)
 * with their conditions and passive effects.
 */

import { rest } from '../rest.js';
import { pageTitle } from '../lib/page_title.js';
import { fmtEffectsInline, fmtTrophyCondition, fmtTrophyProgress } from '../lib/format.js';
import { eventBus } from '../events.js';

let _container = null;
let _trophies = [];
let _unsubTrophy = null;

function _render() {
  if (!_container) return;

  const earned = _trophies.filter(t => t.earned);
  const unearned = _trophies.filter(t => !t.earned);

  _container.innerHTML = `
    <div class="trophies-page">
      <h2>Trophies</h2>
      <p class="trophies-subtitle">Trophies persist across season resets and grant permanent bonuses.</p>

      ${earned.length > 0 ? `
        <h3 class="trophies-section-title">Earned (${earned.length})</h3>
        <div class="trophies-grid">
          ${earned.map(_cardHtml).join('')}
        </div>
      ` : ''}

      ${unearned.length > 0 ? `
        <h3 class="trophies-section-title trophies-section-locked">Locked (${unearned.length})</h3>
        <div class="trophies-grid trophies-grid--locked">
          ${unearned.map(_cardHtml).join('')}
        </div>
      ` : ''}

      ${_trophies.length === 0 ? '<p class="trophies-empty">No trophies defined yet.</p>' : ''}
    </div>
  `;
}

function _cardHtml(t) {
  const effects = Object.keys(t.effects || {}).length > 0
    ? `<div class="trophy-effects">${fmtEffectsInline(t.effects)}</div>`
    : '';
  const progressText = fmtTrophyProgress(t.progress_current, t.progress_target);
  const condition = t.earned
    ? `<div class="trophy-condition trophy-condition--earned">✓ ${fmtTrophyCondition(t.condition)}</div>`
    : `<div class="trophy-condition">${fmtTrophyCondition(t.condition)}${progressText ? ` (${progressText})` : ''}</div>`;
  const progressBar = (!t.earned && t.progress_target)
    ? `<div class="trophy-progress-bar"><div class="trophy-progress-bar-fill" style="width:${Math.min(100, 100 * (t.progress_current ?? 0) / t.progress_target)}%"></div></div>`
    : '';
  const earnedDate = t.earned && t.earned_at
    ? `<div class="trophy-date">${new Date(t.earned_at * 1000).toLocaleDateString()}</div>`
    : '';

  return `
    <div class="trophy-card${t.earned ? ' trophy-card--earned' : ''}">
      <div class="trophy-icon">${t.image ? `<img src="${t.image}" alt="${t.name}" style="width:48px;height:48px;object-fit:contain">` : '🏆'}</div>
      <div class="trophy-body">
        <div class="trophy-name">${t.name}</div>
        <div class="trophy-desc">${t.description}</div>
        ${condition}
        ${progressBar}
        ${effects}
        ${earnedDate}
      </div>
    </div>
  `;
}

async function _load() {
  try {
    const resp = await rest.getTrophies();
    _trophies = resp?.trophies ?? [];
    _render();
  } catch (e) {
    if (_container) _container.innerHTML = '<p class="error">Failed to load trophies.</p>';
  }
}

function init(el) {
  _container = el;
}

async function enter() {
  pageTitle.set('🏆 Trophies');
  await _load();
  _unsubTrophy = eventBus.on('trophy_awarded', () => _load());
}

function leave() {
  if (_unsubTrophy) {
    _unsubTrophy();
    _unsubTrophy = null;
  }
}

export default { id: 'trophies', title: 'Trophies', init, enter, leave };

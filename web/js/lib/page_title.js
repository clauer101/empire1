/**
 * Shell-level page title + resource bar manager.
 * Owns #page-header in index.html — all views call pageTitle.set() in enter().
 */

import { eventBus } from '../events.js';
import { isGameFrozen } from './game_state.js';
import { fmtRes } from './format.js';

let _tickTimer = null;
let _summary = null;
let _tickTs = null;

function _calcRate(type, s) {
  const fx = s.effects || {};
  const citizens = s.citizens || {};
  const effCe = s.citizen_effect || 0;
  if (type === 'life') return (s.base_life ?? 0) + (fx.life_regen_modifier || 0);
  if (type === 'gold') {
    const offset = (s.base_gold ?? 0) + (fx.gold_offset || 0);
    const mod = (citizens.merchant || 0) * effCe
      + ((citizens.artist || 0) + (citizens.scientist || 0)) * (fx.other_citizen_gold_modifier || 0)
      + (fx.gold_modifier || 0);
    return offset * (1 + mod);
  }
  const offset = (s.base_culture ?? 0) + (fx.culture_offset || 0);
  const mod = (citizens.artist || 0) * effCe + (fx.culture_modifier || 0);
  return offset * (1 + mod);
}


function _tick() {
  if (!_summary || !_tickTs) return;
  const elapsedS = isGameFrozen() ? 0 : (Date.now() - _tickTs) / 1000;
  const res = _summary.resources || {};
  const gold = (res.gold || 0) + _calcRate('gold', _summary) * elapsedS;
  const culture = (res.culture || 0) + _calcRate('culture', _summary) * elapsedS;
  const life = Math.min((res.life || 0) + _calcRate('life', _summary) * elapsedS, _summary.max_life ?? Infinity);
  const g = document.querySelector('#page-header .title-gold');
  const c = document.querySelector('#page-header .title-culture');
  const l = document.querySelector('#page-header .title-life');
  if (g) g.textContent = '💰 ' + fmtRes(gold);
  if (c) c.textContent = '🎭 ' + fmtRes(culture);
  if (l) l.innerHTML = '<span style="color:#e05c5c">❤</span> ' + fmtRes(life);
}

function _onSummary(summary) {
  _summary = summary;
  _tickTs = Date.now();
  _tick();
  if (!_tickTimer) _tickTimer = setInterval(_tick, 1000);
}

export const pageTitle = {
  /** Call once at app startup */
  init() {
    eventBus.on('state:summary', _onSummary);
  },

  /**
   * @param {string} text - title text incl. emoji
   * @param {{ id?: string, title?: string, onClick: Function }|null} [btn]
   */
  set(text, btn) {
    const textEl = document.getElementById('page-header-text');
    // Button may have had its id changed by a previous view — find it by class
    const btnEl = document.querySelector('#main-col .prod-info-btn');
    if (textEl) textEl.textContent = text;
    if (btnEl) {
      btnEl.id = 'page-header-btn';
      if (btn) {
        btnEl.style.display = '';
        if (btn.id) btnEl.id = btn.id;
        btnEl.title = btn.title || '';
        btnEl.onclick = btn.onClick;
      } else {
        btnEl.style.display = 'none';
        btnEl.onclick = null;
      }
    }
  },
};

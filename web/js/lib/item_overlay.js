/**
 * Shared item detail overlay — used by techtree, buildings, research views.
 *
 * Usage:
 *   import { ItemOverlay } from '../lib/item_overlay.js';
 *   const overlay = new ItemOverlay(stateStore);
 *   overlay.mount(containerElement);     // creates overlay DOM
 *   await overlay.ensureEraMap();        // load era data once
 *   overlay.show('HUNTING', 'knowledge');
 *   overlay.bindBadgeClicks(someEl);     // make .tt-link badges clickable
 *   overlay.destroy();                   // cleanup
 */

import { fmtEffort, fmtEffectRow, fmtEffectsInline, fmtTowerEffects } from './format.js';
import { ERA_YAML_TO_KEY, ERA_LABEL_EN } from './eras.js';

export class ItemOverlay {
  constructor(state) {
    this._st = state;
    this._eraMap = null;
    this._history = [];
    this._el = null;
    this._panel = null;
    this.onHide = null; // callback when overlay is closed
  }

  /** Create overlay DOM inside container. */
  mount(container) {
    this._el = document.createElement('div');
    this._el.className = 'tt-overlay';
    this._panel = document.createElement('div');
    this._panel.className = 'tt-panel';
    this._el.appendChild(this._panel);
    container.appendChild(this._el);

    this._el.addEventListener('click', (e) => {
      if (e.target === this._el) this.hide();
    });

    this._keyHandler = (e) => {
      if (e.key === 'Escape' && this._el.classList.contains('visible')) this.hide();
    };
    document.addEventListener('keydown', this._keyHandler);
  }

  /** No-op: era data now comes from item catalog. Kept for call-site compatibility. */
  async ensureEraMap() {}

  /** Build reverse-requirement map from catalog. */
  _unlocksMap() {
    const map = {};
    const catalog = this._st.items?.catalog || {};
    for (const [iid, info] of Object.entries(catalog)) {
      for (const req of info.requirements || []) {
        if (!map[req]) map[req] = [];
        map[req].push({ iid, name: info.name || iid, category: info.item_type || 'knowledge' });
      }
    }
    return map;
  }

  /** Create clickable badge HTML. */
  linkBadge(iid, name, category) {
    return `<span class="tt-ubadge tt-link tt-cat-${category}" data-iid="${iid}" data-cat="${category}">${name}</span>`;
  }

  /** Bind click handlers on all .tt-link badges inside el. */
  bindBadgeClicks(el) {
    el.querySelectorAll('.tt-link').forEach((badge) => {
      badge.addEventListener('click', (e) => {
        e.stopPropagation();
        this.show(badge.dataset.iid, badge.dataset.cat);
      });
    });
  }

  /** Show overlay for an item. */
  show(iid, category) {
    const catalog = this._st.items?.catalog || {};
    const knowledge = this._st.items?.knowledge || {};
    const buildings = this._st.items?.buildings || {};
    const structures = this._st.items?.structures || {};
    const critters = this._st.items?.critters || {};
    const unlocks = this._unlocksMap();

    if (!category) {
      const info = catalog[iid];
      category = info?.item_type || 'knowledge';
    }

    this._history.push({ iid, category });

    const catInfo = catalog[iid] || {};
    let spriteUrl = null;
    let html = `<button class="tt-close">&times;</button>`;
    if (this._history.length > 1) {
      html += `<button class="tt-back">← Back</button>`;
    }

    if (category === 'knowledge') {
      const avail = knowledge[iid];
      const name = avail?.name || catInfo.name || iid;
      const desc = avail?.description || catInfo.description;
      const effort = avail?.effort ?? catInfo.effort;
      const effectsStr = this._fmtEffects(avail?.effects || catInfo.effects);
      const reqs = this._reqLinks(avail?.requirements || catInfo.requirements);
      const eraLabel = this._getEraLabel(iid);
      const itemUnlocks = unlocks[iid] || [];

      html += `
        <div class="tt-dp-name">🔬 ${name}</div>
        <div class="tt-dp-iid">${iid}</div>
        ${desc ? `<div class="tt-dp-desc">${desc}</div>` : ''}
        <div class="tt-dp-props">
          ${eraLabel ? `<span class="tt-dp-label">Era:</span><span>${eraLabel}</span>` : ''}
          ${effort != null ? `<span class="tt-dp-label">Effort:</span><span>${this._fmtEffort(effort)}</span>` : ''}
        </div>
        ${effectsStr ? `<div class="tt-dp-row tt-dp-effects">✦ ${effectsStr}</div>` : ''}
        ${reqs ? `<div class="tt-dp-section"><div class="tt-dp-section-title">Requirements</div><div class="tt-dp-unlocks">${reqs}</div></div>` : ''}
        ${
          itemUnlocks.length > 0
            ? `<div class="tt-dp-section"><div class="tt-dp-section-title">Unlocks</div><div class="tt-dp-unlocks">${itemUnlocks
                .map((u) => this.linkBadge(u.iid, u.name, u.category))
                .join('')}</div></div>`
            : ''
        }
      `;
    } else if (category === 'building') {
      const b = buildings[iid] || catInfo;
      const name = b?.name || catInfo.name || iid;
      const desc = b?.description || catInfo.description;
      const effort = b?.effort ?? catInfo.effort;
      const effectsStr = this._fmtItemEffects(b?.effects || catInfo.effects);
      const reqs = this._reqLinks(b?.requirements || catInfo.requirements);
      const costsStr = this._fmtCosts(b?.costs || catInfo.costs);
      const eraLabel = this._getEraLabel(iid);

      html += `
        <div class="tt-dp-name">🏗 ${name}</div>
        <div class="tt-dp-iid">${iid}</div>
        ${desc ? `<div class="tt-dp-desc">${desc}</div>` : ''}
        <div class="tt-dp-props">
          ${eraLabel ? `<span class="tt-dp-label">Era:</span><span>${eraLabel}</span>` : ''}
          ${effort != null ? `<span class="tt-dp-label">Effort:</span><span>${this._fmtEffort(effort)}</span>` : ''}
          ${costsStr ? `<span class="tt-dp-label">Costs:</span><span>${costsStr}</span>` : ''}
        </div>
        ${effectsStr ? `<div class="tt-dp-row tt-dp-effects">✦ ${effectsStr}</div>` : ''}
        ${reqs ? `<div class="tt-dp-section"><div class="tt-dp-section-title">Requirements</div><div class="tt-dp-unlocks">${reqs}</div></div>` : ''}
      `;
    } else if (category === 'structure') {
      const s = structures[iid] || catInfo;
      const name = s?.name || catInfo.name || iid;
      const effectsStr = this._fmtItemEffects(s?.effects || catInfo.effects);
      const reqs = this._reqLinks(s?.requirements || catInfo.requirements);
      const costsStr = this._fmtCosts(s?.costs || catInfo.costs);
      const eraLabel = this._getEraLabel(iid);

      html += `
        <div class="tt-dp-name">🗼 ${name}</div>
        <div class="tt-dp-iid">${iid}</div>
        ${s?.description || catInfo.description ? `<div class="tt-dp-desc">${s?.description || catInfo.description}</div>` : ''}
        <div class="tt-dp-props">
          ${eraLabel ? `<span class="tt-dp-label">Era:</span><span>${eraLabel}</span>` : ''}
          ${s?.damage != null ? `<span class="tt-dp-label">Damage:</span><span>⚔️ ${s.damage}</span>` : ''}
          ${s?.range != null ? `<span class="tt-dp-label">Range:</span><span>🎯 ${s.range} hex</span>` : ''}
          ${s?.reload_time_ms != null ? `<span class="tt-dp-label">Reload:</span><span>⏱️ ${(s.reload_time_ms / 1000).toFixed(1)}s</span>` : ''}
          ${costsStr ? `<span class="tt-dp-label">Costs:</span><span>${costsStr}</span>` : ''}
        </div>
        ${effectsStr ? `<div class="tt-dp-row tt-dp-effects">✦ ${effectsStr}</div>` : ''}
        ${reqs ? `<div class="tt-dp-section"><div class="tt-dp-section-title">Requirements</div><div class="tt-dp-unlocks">${reqs}</div></div>` : ''}
      `;
    } else if (category === 'artifact') {
      const a = catInfo;
      const name = a?.name || iid;
      const desc = a?.description || '';
      const type = a?.type || 'normal';
      const effectRows = this._fmtEffectRows(a?.effects);
      const reqs = this._reqLinks(a?.requirements);
      const eraLabel = this._getEraLabel(iid);
      const typeColor = type === 'legendary' ? '#ab47bc' : '#c9a84c';
      spriteUrl = a?.sprite ? '/' + a.sprite : null;

      html += `
        <div class="tt-dp-name" style="color:${typeColor}">⚜ ${name}</div>
        <div class="tt-dp-iid">${iid}</div>
        ${eraLabel ? `<div class="tt-dp-props"><span class="tt-dp-label">Era:</span><span>${eraLabel}</span></div>` : ''}
        ${desc ? `<div class="tt-dp-desc">${desc}</div>` : ''}
        ${effectRows ? `<div class="tt-dp-section"><div class="tt-dp-section-title">Effects</div><div class="tt-dp-props">${effectRows}</div></div>` : ''}
        ${reqs ? `<div class="tt-dp-section"><div class="tt-dp-section-title">Requirements</div><div class="tt-dp-unlocks">${reqs}</div></div>` : ''}
      `;
    } else if (category === 'critter') {
      const c = critters[iid] || catInfo;
      const name = c?.name || catInfo.name || iid;
      const reqs = this._reqLinks(c?.requirements || catInfo.requirements);
      const eraLabel = this._getEraLabel(iid);

      html += `
        <div class="tt-dp-name">${c?.is_boss || catInfo.is_boss ? '👑 ' : '🗡 '}${name}</div>
        <div class="tt-dp-iid">${iid}</div>
        <div class="tt-dp-props">
          ${eraLabel ? `<span class="tt-dp-label">Era:</span><span>${eraLabel}</span>` : ''}
          ${c?.health != null ? `<span class="tt-dp-label">Health:</span><span>❤ ${c.health}</span>` : ''}
          ${c?.speed != null ? `<span class="tt-dp-label">Speed:</span><span>⚡ ${c.speed.toFixed(2)}</span>` : ''}
          ${c?.armour ? `<span class="tt-dp-label">Armour:</span><span>🛡 ${c.armour}</span>` : ''}
          ${c?.damage != null ? `<span class="tt-dp-label">Damage:</span><span>${c.damage}</span>` : ''}
          ${c?.slots != null ? `<span class="tt-dp-label">Slots:</span><span>${c.slots}</span>` : ''}
        </div>
        ${reqs ? `<div class="tt-dp-section"><div class="tt-dp-section-title">Requirements</div><div class="tt-dp-unlocks">${reqs}</div></div>` : ''}
      `;
    }

    this._panel.innerHTML = html;

    // Artifact sprite as panel background with fade-to-dark gradient
    if (category === 'artifact' && spriteUrl) {
      this._panel.style.backgroundImage =
        `linear-gradient(to bottom, rgba(14,14,22,0.35) 0%, rgba(14,14,22,0.97) 55%), url('${spriteUrl}')`;
      this._panel.style.backgroundSize = 'cover, cover';
      this._panel.style.backgroundPosition = 'center top, center top';
      this._panel.style.backgroundRepeat = 'no-repeat, no-repeat';
    } else {
      this._panel.style.backgroundImage = '';
      this._panel.style.backgroundSize = '';
      this._panel.style.backgroundPosition = '';
      this._panel.style.backgroundRepeat = '';
    }

    // Bind close
    this._panel.querySelector('.tt-close').addEventListener('click', () => this.hide());

    // Bind back
    const backBtn = this._panel.querySelector('.tt-back');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        this._history.pop();
        const prev = this._history.pop();
        if (prev) this.show(prev.iid, prev.category);
      });
    }

    // Bind clickable badges inside panel
    this.bindBadgeClicks(this._panel);

    this._el.classList.add('visible');
  }

  hide() {
    if (this._el) this._el.classList.remove('visible');
    this._history = [];
    if (this.onHide) this.onHide();
  }

  destroy() {
    if (this._keyHandler) document.removeEventListener('keydown', this._keyHandler);
    if (this._el) {
      this._el.remove();
      this._el = null;
      this._panel = null;
    }
    this._history = [];
  }

  // ── Format helpers ────────────────────────────────────────

  _fmtEffort(n) {
    return fmtEffort(n);
  }

  _fmtEffectRows(effects) {
    if (!effects || Object.keys(effects).length === 0) return '';
    return Object.entries(effects).map(([k, v]) => fmtEffectRow(k, v)).join('');
  }

  _fmtEffects(effects) {
    return fmtEffectsInline(effects);
  }

  _fmtItemEffects(effects) {
    return fmtTowerEffects(effects);
  }

  _fmtCosts(costs) {
    if (!costs || Object.keys(costs).length === 0) return '';
    return Object.entries(costs)
      .map(([r, v]) => {
        const icon = r === 'gold' ? '💰' : r === 'culture' ? '📚' : r === 'life' ? '❤️' : '';
        return `${icon} ${Math.round(v)} ${r.charAt(0).toUpperCase() + r.slice(1)}`;
      })
      .join(', ');
  }

  _reqLinks(requirements) {
    const catalog = this._st.items?.catalog || {};
    return (requirements || [])
      .map((r) => {
        const info = catalog[r];
        if (info) return this.linkBadge(r, info.name || r, info.item_type || 'knowledge');
        return `<span class="tt-ubadge">${r}</span>`;
      })
      .join(' ');
  }

  _getEraLabel(iid) {
    const catalog = this._st?.items?.catalog || {};
    const era = catalog[iid]?.era || '';
    if (!era) return '';
    return ERA_LABEL_EN[ERA_YAML_TO_KEY[era]] || era;
  }
}

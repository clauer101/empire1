/**
 * Tile placement menu and map editor functions.
 *
 * All functions are factories that close over a shared context object:
 *   ctx = {
 *     getGrid()           → HexGrid | null
 *     getContainer()      → HTMLElement
 *     getSt()             → StateStore
 *     getBattleState()    → _battleState
 *     getSpectateUid()    → number | null
 *     getStructureEraRoman() → { [iidUpper]: romanStr }
 *     applyStructUpgrades(s, iid) → upgraded stats
 *     showMapError(msg)
 *     showPersistentError(msg)
 *     clearMapError()
 *     getTileType(id)     → tile type descriptor (from hex_grid.js)
 *     rest                → rest client
 *   }
 */

export function createPlacement(ctx) {
  let _isDirtyPath = false;
  let _autoSaveTimer = null;

  function clearExistingCastle(excludeQ, excludeR) {
    const grid = ctx.getGrid();
    if (!grid) return;
    for (const [key, data] of grid.tiles) {
      if (data.type === 'castle') {
        const [sq, sr] = key.split(',').map(Number);
        if (sq === excludeQ && sr === excludeR) continue;
        grid.setTile(sq, sr, 'empty');
      }
    }
  }

  function clearExistingSpawnpoint(excludeQ, excludeR) {
    const grid = ctx.getGrid();
    if (!grid) return;
    for (const [key, data] of grid.tiles) {
      if (data.type === 'spawnpoint') {
        const [sq, sr] = key.split(',').map(Number);
        if (sq === excludeQ && sr === excludeR) continue;
        grid.setTile(sq, sr, 'empty');
      }
    }
  }

  function openPlacementMenu(q, r) {
    const grid = ctx.getGrid();
    const container = ctx.getContainer();
    if (!grid || grid.getTile(q, r)?.type !== 'empty') return;

    const menu = container.querySelector('#tile-place-menu');
    const itemsEl = container.querySelector('#tpm-items');
    if (!menu || !itemsEl) return;

    itemsEl.innerHTML = '';

    const inBattle = ctx.getBattleState().phase === 'in_battle';

    let hasCastle = false;
    let hasSpawnpoint = false;
    for (const [, tileData] of grid.tiles) {
      if (tileData.type === 'castle') hasCastle = true;
      if (tileData.type === 'spawnpoint') hasSpawnpoint = true;
    }

    if (!inBattle) {
      const label = document.createElement('div');
      label.className = 'tpm-section-label';
      label.textContent = 'Waypoints';
      itemsEl.appendChild(label);

      const setupRow = document.createElement('div');
      setupRow.className = 'tpm-row';
      for (const typeId of ['castle', 'spawnpoint']) {
        const item = createTpmItem(typeId, q, r, menu);
        if (typeId === 'castle' && hasCastle) item.title += ' (move)';
        else if (typeId === 'spawnpoint' && hasSpawnpoint) item.title += ' (move)';
        setupRow.appendChild(item);
      }
      itemsEl.appendChild(setupRow);
    }

    const structureIds = Object.keys((ctx.getSt().items || {}).structures || {}).reverse();
    if (structureIds.length > 0) {
      const towerLabel = document.createElement('div');
      towerLabel.className = 'tpm-section-label';
      towerLabel.textContent = 'Towers';
      itemsEl.appendChild(towerLabel);

      const towerGrid = document.createElement('div');
      towerGrid.className = 'tpm-grid';
      for (const iid of structureIds) {
        towerGrid.appendChild(createTpmItem(iid, q, r, menu));
      }
      itemsEl.appendChild(towerGrid);
    }

    menu.style.display = 'flex';
  }

  function createTpmItem(typeId, q, r, menu) {
    const t = ctx.getTileType(typeId);
    const s = t.serverData ? ctx.applyStructUpgrades(t.serverData, typeId) : t.serverData;
    const currentGold = ctx.getSt().summary?.resources?.gold || 0;
    const goldCost = s?.costs?.gold;
    const canAfford = !goldCost || currentGold >= goldCost;

    const card = document.createElement('div');
    card.className = 'tpm-item' + (canAfford ? '' : ' tpm-item--disabled');
    card.title = t.label + (goldCost ? ' (💰 ' + Math.round(goldCost).toLocaleString() + ')' : '');

    const sprite = document.createElement('div');
    sprite.className = 'tpm-sprite';
    sprite.style.backgroundColor = t.color;
    sprite.style.border = '2px solid ' + t.stroke;
    if (t.spriteUrl) {
      sprite.style.backgroundImage = 'url(' + t.spriteUrl + ')';
      if (typeId === 'path') sprite.style.backgroundSize = '50%';
    }
    card.appendChild(sprite);

    const name = document.createElement('div');
    name.className = 'tpm-name';
    name.style.cssText = 'display:flex;align-items:baseline;gap:3px;overflow:hidden;';
    const eraRoman = ctx.getStructureEraRoman()[typeId.toUpperCase()];
    const labelSpan = document.createElement('span');
    labelSpan.style.cssText = 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
    labelSpan.textContent = t.label;
    name.appendChild(labelSpan);
    if (eraRoman) {
      const era = document.createElement('span');
      era.className = 'era-roman-badge';
      era.style.cssText = 'font-size:9px;flex-shrink:0;';
      era.textContent = eraRoman;
      name.appendChild(era);
    }
    card.appendChild(name);

    if (goldCost) {
      const cost = document.createElement('div');
      cost.className = 'tpm-cost' + (canAfford ? '' : ' unaffordable');
      cost.textContent = '💰 ' + Math.round(goldCost).toLocaleString();
      card.appendChild(cost);
    }

    if (s && (s.damage || s.range || s.reload_time_ms)) {
      const stats = document.createElement('div');
      stats.className = 'tpm-stats';
      const statItems = [];
      if (s.damage) statItems.push({ text: '⚔️ ' + s.damage, tip: 'Damage: ' + s.damage });
      if (s.range) statItems.push({ text: '🎯 ' + s.range, tip: 'Range: ' + s.range });
      if (s.reload_time_ms) statItems.push({ text: '⏱️ ' + (s.reload_time_ms / 1000).toFixed(1) + 's', tip: 'Reload Time: ' + (s.reload_time_ms / 1000).toFixed(1) + 's' });
      statItems.forEach((item) => {
        const span = document.createElement('span');
        span.title = item.tip;
        span.textContent = item.text;
        stats.appendChild(span);
      });
      card.appendChild(stats);
    }

    if (s?.effects && Object.keys(s.effects).length > 0) {
      const efx = document.createElement('div');
      efx.className = 'tpm-effects';
      const ef = s.effects;
      const efxItems = [];
      if (ef.burn_duration || ef.burn_dps) {
        const txt = '🔥 ' + ((ef.burn_duration || 0) / 1000).toFixed(1) + 's @ ' + (ef.burn_dps || 0) + ' dps';
        efxItems.push({ text: txt, tip: 'Burn Damage: ' + (ef.burn_dps || 0) + ' dps for ' + ((ef.burn_duration || 0) / 1000).toFixed(1) + 's' });
      }
      if (ef.slow_duration || ef.slow_ratio != null) {
        const txt = '❄ ' + ((ef.slow_duration || 0) / 1000).toFixed(1) + 's @ ' + Math.round((ef.slow_ratio || 0) * 100) + '%';
        efxItems.push({ text: txt, tip: 'Slow Effect: ' + Math.round((ef.slow_ratio || 0) * 100) + '% speed for ' + ((ef.slow_duration || 0) / 1000).toFixed(1) + 's' });
      }
      if (ef.splash_radius) {
        efxItems.push({ text: '💥 ' + ef.splash_radius, tip: 'Splash Radius: ' + ef.splash_radius + ' tiles' });
      }
      efxItems.forEach((item) => {
        const span = document.createElement('span');
        span.title = item.tip;
        span.textContent = item.text;
        efx.appendChild(span);
      });
      card.appendChild(efx);
    }

    if (canAfford) {
      card.addEventListener('click', () => {
        placeTile(q, r, typeId);
        menu.style.display = 'none';
      });
    }

    return card;
  }

  function placeTile(q, r, typeId) {
    const grid = ctx.getGrid();
    const existingType = grid.getTile(q, r)?.type;
    if (!existingType || existingType === 'void') return;
    if (existingType !== 'empty') {
      ctx.showMapError('Tile bereits belegt.');
      return;
    }
    if (typeId === 'spawnpoint') clearExistingSpawnpoint(q, r);
    if (typeId === 'castle') clearExistingCastle(q, r);
    grid.setTile(q, r, typeId);
    const cost = ctx.getTileType(typeId)?.serverData?.costs?.gold || 0;
    if (cost && ctx.getSt().summary?.resources) {
      ctx.getSt().summary.resources.gold = Math.max(0, (ctx.getSt().summary.resources.gold || 0) - cost);
    }
    checkPathAndSave();
  }

  function markPathDirty() {
    _isDirtyPath = true;
    if (ctx.getSpectateUid() != null) return;
    const btn = ctx.getContainer().querySelector('#map-save');
    if (btn) btn.style.display = '';
  }

  function clearPathDirty() {
    _isDirtyPath = false;
    const btn = ctx.getContainer().querySelector('#map-save');
    if (btn) btn.style.display = 'none';
  }

  function checkPathAndSave() {
    if (ctx.getSpectateUid() != null) return;
    const grid = ctx.getGrid();
    let hasSpawnpoint = false, hasCastle = false;
    for (const [, data] of grid.tiles) {
      if (data.type === 'spawnpoint') hasSpawnpoint = true;
      if (data.type === 'castle') hasCastle = true;
    }
    if (!hasCastle) {
      ctx.showPersistentError('⚠️ Kein Castle platziert');
      grid.setDisplayPath(null);
      return;
    }
    if (!hasSpawnpoint) {
      ctx.showPersistentError('⚠️ Kein Spawnpoint platziert');
      grid.setDisplayPath(null);
      return;
    }
    autoSave();
  }

  async function saveMap() {
    if (ctx.getSpectateUid() != null) {
      console.warn('[Battle] _saveMap blocked: spectating uid', ctx.getSpectateUid());
      return;
    }
    const myUid = ctx.getSt()?.auth?.uid;
    const battleState = ctx.getBattleState();
    if (myUid == null || (battleState.defender_uid != null && battleState.defender_uid !== myUid)) {
      console.error('[Battle] _saveMap blocked: displayed map belongs to uid', battleState.defender_uid, '(mine:', myUid, ')');
      const errBanner = ctx.getContainer().querySelector('#map-error-banner');
      if (errBanner) { errBanner.textContent = '❌ Cannot save: wrong map loaded'; errBanner.style.display = 'block'; }
      return;
    }
    const grid = ctx.getGrid();
    const btn = ctx.getContainer().querySelector('#map-save');
    const errBanner = ctx.getContainer().querySelector('#map-error-banner');
    if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }
    if (errBanner) errBanner.style.display = 'none';
    try {
      const data = grid.toJSON();
      const resp = await ctx.rest.saveMap(data.tiles || {});
      if (resp && resp.success === false) {
        const msg = resp.error || 'Save failed';
        console.error('[Battle] Map save failed:', msg);
        if (errBanner) { errBanner.textContent = '❌ ' + msg; errBanner.style.display = 'block'; }
        if (btn) { btn.textContent = '✗ Error'; btn.style.color = 'var(--danger)'; setTimeout(() => { btn.textContent = '💾 Save'; btn.style.color = ''; btn.disabled = false; }, 2000); }
      } else {
        clearPathDirty();
        if (resp?.tiles && grid) { grid.fromJSON({ tiles: resp.tiles }); grid.addVoidNeighbors(); }
        const path = resp?.path ? resp.path.map(([q, r]) => ({ q, r })) : null;
        grid.setDisplayPath(path);
        if (path) ctx.clearMapError();
        if (errBanner) errBanner.style.display = 'none';
        if (btn) { btn.textContent = '✓ Saved'; btn.style.color = 'var(--success)'; setTimeout(() => { btn.textContent = '💾 Save'; btn.style.color = ''; btn.disabled = false; }, 1200); }
      }
    } catch (err) {
      const msg = err.message || 'Network error';
      console.error('[Battle] _saveMap error:', err);
      if (errBanner) { errBanner.textContent = '❌ ' + msg; errBanner.style.display = 'block'; }
      if (btn) { btn.textContent = '✗ Error'; btn.style.color = 'var(--danger)'; setTimeout(() => { btn.textContent = '💾 Save'; btn.style.color = ''; btn.disabled = false; }, 2000); }
    }
  }

  function autoSave() {
    if (ctx.getSpectateUid() != null) return;
    clearTimeout(_autoSaveTimer);
    _autoSaveTimer = setTimeout(async () => {
      const grid = ctx.getGrid();
      if (!grid) { console.warn('[Battle] Auto-save skipped: grid destroyed (view left)'); return; }
      try {
        const data = grid.toJSON();
        const resp = await ctx.rest.saveMap(data.tiles || {});
        if (resp && resp.success === false) {
          markPathDirty();
          ctx.showPersistentError('⚠️ ' + (resp.error || 'No valid path'));
          grid.setDisplayPath(null);
        } else {
          clearPathDirty();
          if (resp?.tiles && grid) { grid.fromJSON({ tiles: resp.tiles }); grid.addVoidNeighbors(); }
          const path = resp?.path ? resp.path.map(([q, r]) => ({ q, r })) : null;
          grid.setDisplayPath(path);
          if (path) ctx.clearMapError();
        }
      } catch (err) {
        console.error('[Battle] Auto-save error:', err);
      }
    }, 800);
  }

  function cancelAutoSave() {
    clearTimeout(_autoSaveTimer);
    _autoSaveTimer = null;
  }

  function isDirtyPath() { return _isDirtyPath; }
  function hasAutoSaveTimer() { return _autoSaveTimer != null; }

  return {
    openPlacementMenu,
    createTpmItem,
    placeTile,
    markPathDirty,
    clearPathDirty,
    checkPathAndSave,
    saveMap,
    autoSave,
    cancelAutoSave,
    isDirtyPath,
    hasAutoSaveTimer,
  };
}

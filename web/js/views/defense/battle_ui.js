/**
 * Battle UI: message handlers, status panel, summary overlay, flying HUD icons.
 *
 * ctx = {
 *   getGrid()           → HexGrid | null
 *   getContainer()      → HTMLElement
 *   getSt()             → StateStore
 *   getBattleState()    → mutable _battleState object (will be mutated)
 *   setBattleState(obj) → replace _battleState reference
 *   getPendingAttackId() → number | null
 *   getSpectateUid()    → number | null
 *   addDebugLog(msg)
 *   acquireWakeLock()
 *   releaseWakeLock()
 *   showPersistentError(msg)
 *   clearMapError()
 *   setBattleTitle(label)
 *   updateCastleSprite(eraKey)
 *   rest                → rest client
 *   hexKey(q, r)        → string key
 * }
 */

export function createBattleUi(ctx) {
  let _statusLoopId = null;
  // Snapshot of the last wave_info received from the server + the wall-clock time it arrived.
  // Used to compute a smooth client-side countdown independent of broadcast interval.
  let _waveInfoSnapshot = null;   // { wave_info, receivedAt: DOMHighResTimeStamp }


  function spawnFlyingIcon(imgSrc, cx, cy, label, labelColor) {
    const wrap = ctx.getContainer().querySelector('#canvas-wrap');
    if (!wrap) return;
    const div = document.createElement('div');
    div.className = 'fly-wrap';
    div.style.left = cx + 'px';
    div.style.top = cy + 'px';
    const img = document.createElement('img');
    img.src = imgSrc;
    img.className = 'fly-icon';
    div.appendChild(img);
    if (label != null) {
      const span = document.createElement('span');
      span.className = 'fly-label';
      if (labelColor) span.style.color = labelColor;
      span.textContent = typeof label === 'string' && label.startsWith('-') ? label : '+' + label;
      div.appendChild(span);
    }
    wrap.appendChild(div);
    div.addEventListener('animationend', () => div.remove());
  }

  function onBattleStatus(msg) {
    if (!msg) return;
    const bs = ctx.getBattleState();
    if (bs.phase !== (msg.phase || 'waiting')) {
      ctx.addDebugLog(`Phase: ${bs.phase} → ${msg.phase || 'waiting'}`);
    }
    bs.phase = msg.phase || 'waiting';
    bs.defender_uid = msg.defender_uid;
    bs.defender_name = msg.defender_name || 'Unknown';
    bs.attacker_uid = msg.attacker_uid;
    bs.attacker_name = msg.attacker_name || 'Unknown';
    bs.attacker_army_name = msg.attacker_army_name || '';
    bs.attacker_username = msg.attacker_username || '';
    bs.time_since_start_s = msg.time_since_start_s || 0;
    if (msg.time_since_start_s != null) bs.elapsed_ms = msg.time_since_start_s * 1000;
    if ('wave_info' in msg) {
      bs.wave_info = msg.wave_info;
      _waveInfoSnapshot = msg.wave_info ? { wave_info: msg.wave_info, receivedAt: performance.now() } : null;
    }

    const grid = ctx.getGrid();
    if (msg.phase === 'in_battle' && grid && !grid.battleActive) {
      grid.battleActive = true;
    }

    if (ctx.getSpectateUid() != null && msg.defender_era) {
      ctx.updateCastleSprite(msg.defender_era);
    }

    updateStatusFromBattleMsg();
  }

  function onBattleSetup(msg) {
    console.log('[Battle] Battle setup:', msg);
    ctx.addDebugLog(`🎮 Battle Setup: ${msg.defender_name} vs ${msg.attacker_name}`);
    ctx.acquireWakeLock();

    // If a battle is already active on this client, ignore re-initialization triggered
    // by a second observer connecting (e.g. same user on another device).
    if (ctx.getGrid().battleActive) {
      ctx.addDebugLog('⚡ Battle setup ignored — battle already active on this client');
      return;
    }

    _waveInfoSnapshot = null;

    // Check if a battle is already in progress from the summary (user opened defense mid-battle)
    const _st = ctx.getSt();
    const _pendingId = ctx.getPendingAttackId();
    const _existingAtk =
      ((_st?.summary?.attacks_incoming || []).find((a) => a.attack_id === _pendingId)) ||
      ((_st?.summary?.attacks_outgoing || []).find((a) => a.attack_id === _pendingId));
    const _resumePhase = _existingAtk?.phase === 'in_battle' ? 'in_battle'
      : _existingAtk?.phase === 'in_siege' ? 'in_siege'
      : 'waiting';
    const _resumeElapsed = _existingAtk?.battle_elapsed_seconds ?? 0;

    ctx.setBattleState({
      active: true,
      bid: msg.bid || null,
      defender_uid: msg.defender_uid || null,
      defender_name: msg.defender_name || '',
      attacker_uids: msg.attacker_uids || [],
      attacker_name: msg.attacker_name || '',
      attacker_army_name: msg.attacker_army_name || '',
      attacker_username: '',
      elapsed_ms: _resumeElapsed * 1000,
      is_finished: false,
      defender_won: null,
      phase: _resumePhase,
      time_since_start_s: _resumeElapsed,
      wave_info: null,
    });

    const grid = ctx.getGrid();
    grid.clearBattle();

    if (msg.tiles) {
      const isDirty = ctx.getSpectateUid() == null && ctx.placement?.isDirtyPath();
      const hasTimer = ctx.getSpectateUid() == null && ctx.placement?.hasAutoSaveTimer();
      if (!isDirty && !hasTimer) {
        grid.fromJSON({ tiles: msg.tiles });
        grid.addVoidNeighbors();
        grid._centerGrid();
      }
    }

    if (msg.path) {
      if (ctx.getBattleState().phase === 'in_battle') {
        grid.setBattlePath(msg.path);
      } else {
        const path = msg.path.map((p) => (Array.isArray(p) ? { q: p[0], r: p[1] } : p));
        grid.setDisplayPath(path);
      }
    }

    if (msg.structures) {
      for (const s of msg.structures) {
        const key = ctx.hexKey(s.q, s.r);
        const _meta = s.select && s.select !== 'first' ? { select: s.select } : {};
        grid.setTile(s.q, s.r, s.iid, _meta);
        const tile = grid.tiles.get(key);
        if (tile) {
          tile.sid = s.sid;
          tile.structure_data = s;
        }
      }
    }

    if (ctx.getBattleState().phase === 'in_battle') grid.battleActive = true;
    grid._dirty = true;

    if (ctx.getSpectateUid() != null && msg.defender_name) {
      ctx.setBattleTitle(`👁 ${msg.defender_name}`);
    }

    updateStatusFromBattleMsg();
  }

  function onStructureUpdate(msg) {
    const grid = ctx.getGrid();
    if (!msg || !Array.isArray(msg.structures) || !grid) return;
    ctx.addDebugLog(`🏗 Structure update: ${msg.structures.length} towers`);

    const NON_STRUCTURE = new Set(['path', 'castle', 'spawnpoint', 'empty', 'void', 'blocked']);

    for (const [key, tile] of grid.tiles) {
      if (!NON_STRUCTURE.has(tile.type)) {
        const [q, r] = key.split(',').map(Number);
        grid.setTile(q, r, 'empty');
      }
    }

    for (const s of msg.structures) {
      const _meta = s.select && s.select !== 'first' ? { select: s.select } : {};
      grid.setTile(s.q, s.r, s.iid, _meta);
      const key = ctx.hexKey(s.q, s.r);
      const tile = grid.tiles.get(key);
      if (tile) {
        tile.sid = s.sid;
        tile.structure_data = s;
      }
    }

    grid._invalidateBase();
    grid._dirty = true;
  }

  function onBattleUpdate(msg) {
    if (!msg) return;
    const grid = ctx.getGrid();

    if (grid && !grid.battleActive) grid.battleActive = true;

    if (msg.critters && Array.isArray(msg.critters)) {
      const activeCids = new Set();
      for (const c of msg.critters) {
        grid.updateBattleCritter(c);
        activeCids.add(c.cid);
      }
      for (const cid of grid.battleCritters.keys()) {
        if (!activeCids.has(cid)) grid.removeBattleCritter(cid);
      }

      if (msg.removed_critters && Array.isArray(msg.removed_critters)) {
        for (const rc of msg.removed_critters) {
          if (rc.reason === 'died') {
            const raw = grid._getCritterPixelPos(rc.path_progress, grid.hexSize);
            const cx = raw.x * grid.zoom + grid.offsetX;
            const cy = raw.y * grid.zoom + grid.offsetY;
            spawnFlyingIcon(
              '/assets/sprites/hud/flying_coin.webp',
              cx,
              cy,
              rc.value != null ? Math.round(rc.value) : null
            );
          } else if (rc.reason === 'reached') {
            const raw = grid._getCritterPixelPos(1.0, grid.hexSize);
            const cx = raw.x * grid.zoom + grid.offsetX;
            const cy = raw.y * grid.zoom + grid.offsetY;
            spawnFlyingIcon(
              '/assets/sprites/hud/flying_hearth.webp',
              cx,
              cy,
              rc.damage != null ? `-${Math.round(rc.damage)}` : null,
              '#ef5350'
            );
          }
        }
      }
      grid._dirty = true;
    }

    if (msg.shots && Array.isArray(msg.shots)) {
      const activeShotIds = new Set();
      for (const shot of msg.shots) {
        grid.updateBattleShot(shot);
        activeShotIds.add(`${shot.source_sid}_${shot.target_cid}`);
      }
      for (const shot_id of grid.battleShots.keys()) {
        if (!activeShotIds.has(shot_id)) grid.battleShots.delete(shot_id);
      }
    }

    if (msg.defender_life != null) grid.setDefenderLives(msg.defender_life, msg.defender_max_life);
    if ('wave_info' in msg) {
      ctx.getBattleState().wave_info = msg.wave_info;
      _waveInfoSnapshot = msg.wave_info ? { wave_info: msg.wave_info, receivedAt: performance.now() } : null;
      _updateNextWaveDisplay();
    }
    grid._dirty = true;
  }

  function onBattleSummary(msg) {
    console.log('[Battle] Battle summary:', msg);
    const result = msg.defender_won ? '🎉 Victory' : '💀 Defeat';
    ctx.addDebugLog(`⚔ Battle Finished: ${result}`);

    const bs = ctx.getBattleState();
    bs.is_finished = true;
    bs.defender_won = msg.defender_won || false;
    bs.active = false;
    ctx.releaseWakeLock();
    bs.phase = 'finished';

    const grid = ctx.getGrid();
    setTimeout(() => {
      grid.clearBattle();
      const path = msg.path ? msg.path.map(([q, r]) => ({ q, r })) : null;
      grid.setDisplayPath(path);
      if (!path)
        ctx.showPersistentError('⚠️ No path from spawn to castle — please remove obstacles.');
      else ctx.clearMapError();
    }, 1500);

    showSummary(msg);
    updateStatus('Battle complete!');
  }

  // ── Status panel ──────────────────────────────────────────

  function startStatusLoop() {
    _statusLoopId = setInterval(() => {
      if (ctx.getBattleState().active) ctx.getBattleState().elapsed_ms += 100;
      updateStatusPanel();
      _updateNextWaveDisplay();
    }, 100);
  }

  function stopStatusLoop() {
    if (_statusLoopId) {
      clearInterval(_statusLoopId);
      _statusLoopId = null;
    }
  }

  function updateStatus(text) {
    const el = ctx.getContainer().querySelector('#battle-status-text');
    if (el) el.textContent = text;
  }

  function _formatTime(ms) {
    const totalSec = Math.floor(Math.abs(ms) / 1000);
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    const sign = ms < 0 ? '-' : '';
    return `${sign}${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  }

  function updateStatusPanel() {
    const bs = ctx.getBattleState();
    const elapsedEl = ctx.getContainer().querySelector('#battle-elapsed');
    if (elapsedEl) {
      if (bs.phase === 'travelling' && bs.eta_seconds != null) {
        bs.eta_seconds = Math.max(0, bs.eta_seconds - 0.1);
        elapsedEl.textContent = _formatTime(-bs.eta_seconds * 1000);
      } else if (bs.phase !== 'travelling') {
        elapsedEl.textContent = _formatTime(bs.elapsed_ms);
      }
    }
  }

  function updateStatusFromBattleMsg() {
    const bs = ctx.getBattleState();
    const container = ctx.getContainer();

    const defenderEl = container.querySelector('#battle-defender');
    const attackerEl = container.querySelector('#battle-attacker');
    if (defenderEl) defenderEl.textContent = bs.defender_name || '-';
    if (attackerEl) {
      const armyName = bs.attacker_army_name || bs.attacker_name || '-';
      const username = bs.attacker_username;
      attackerEl.textContent = username ? `${armyName} (${username})` : armyName;
    }

    let statusText = 'Waiting...';
    if (bs.phase === 'travelling') statusText = '🚶 Traveling';
    else if (bs.phase === 'in_siege') statusText = '🛡 Siege';
    else if (bs.phase === 'in_battle') statusText = '⚔ Battle';
    else if (bs.phase === 'finished') statusText = '✓ Complete';
    updateStatus(statusText);

    const fightNowItem = container.querySelector('#fight-now-item');
    if (fightNowItem) {
      const showFightNow =
        ctx.getPendingAttackId() !== null &&
        bs.phase === 'in_siege' &&
        ctx.getSpectateUid() == null;
      fightNowItem.style.display = showFightNow ? '' : 'none';
    }

    _updateNextWaveDisplay();
  }

  function _updateNextWaveDisplay() {
    const bs = ctx.getBattleState();
    const container = ctx.getContainer();
    const nextWaveEl = container.querySelector('#battle-next-wave');
    if (!nextWaveEl) return;

    if (bs.phase === 'travelling') {
      // Before battle: show army arrival ETA from the attack summary
      const st = ctx.getSt();
      const attackSummary =
        (st.summary?.attacks_incoming || []).find(
          (a) => a.attack_id === ctx.getPendingAttackId()
        ) ||
        (st.summary?.attacks_outgoing || []).find(
          (a) => a.attack_id === ctx.getPendingAttackId()
        );
      const etaSec = attackSummary?.eta_seconds ?? null;
      if (etaSec !== null) bs.eta_seconds = etaSec;
      const wi = bs.wave_info;
      if (wi && etaSec !== null) {
        nextWaveEl.textContent = `Next Wave (${wi.wave_index}/${wi.total_waves}): ${wi.critter_count}× ${wi.critter_name}, eta: ${Math.ceil(etaSec)}s`;
      } else if (etaSec !== null) {
        nextWaveEl.textContent = `Arriving in ${Math.ceil(etaSec)}s`;
      } else {
        nextWaveEl.textContent = '-';
      }
      return;
    }

    // Siege / in_battle: smooth client-side countdown using server eta_ms + elapsed time since receipt
    if (!_waveInfoSnapshot) {
      nextWaveEl.textContent = bs.phase === 'in_battle' ? 'All waves done' : '-';
      return;
    }

    const { wave_info: wi, receivedAt } = _waveInfoSnapshot;
    const elapsedSinceReceipt = performance.now() - receivedAt;
    const siegeRemainingMs =
      bs.phase === 'in_siege' && bs.time_since_start_s < 0 ? -bs.time_since_start_s * 1000 : 0;
    const remainingMs = siegeRemainingMs + (wi.eta_ms ?? 0) - elapsedSinceReceipt;
    const etaSec = Math.ceil(remainingMs / 1000);
    const timeStr = etaSec > 0 ? `${etaSec}s` : 'now';
    nextWaveEl.textContent = `Next Wave (${wi.wave_index}/${wi.total_waves}): ${wi.critter_count}× ${wi.critter_name}, eta: ${timeStr}`;
  }

  // ── Summary overlay ───────────────────────────────────────

  function showSummary(msg) {
    const container = ctx.getContainer();
    const overlay = container.querySelector('#battle-summary');
    const title = container.querySelector('#summary-title');
    const content = container.querySelector('#summary-content');

    const won = msg.defender_won || false;
    title.textContent = won ? '🛡 Defender Victory' : '⚔ Attacker Victory';
    title.style.color = won ? 'var(--green, #4caf50)' : 'var(--red, #d32f2f)';

    const st = ctx.getSt();
    const bs = ctx.getBattleState();
    const myUid = st?.auth?.uid;
    const isDefender = myUid != null && myUid == bs.defender_uid;

    const defenderName = bs.defender_name || 'Defender';

    // Build attacker label: list all participating empires / armies
    const attackerUids = msg.attacker_uids || (msg.attacker_uid != null ? [msg.attacker_uid] : []);
    const empireNames = msg.attacker_empire_names || {};
    const armyNamesByUid = msg.army_names || {};  // uid → [armyName, ...]
    const multiAttacker = attackerUids.length > 1;

    // Single-attacker fallback label (for title sentence)
    const firstUid = attackerUids[0];
    const firstEmpire = empireNames[firstUid] || bs.attacker_username || bs.attacker_name || 'the attacker';
    const firstArmy = (armyNamesByUid[firstUid] || [])[0] || msg.army_name || bs.attacker_army_name || '';
    const singleLabel = firstArmy ? `${firstArmy} (${firstEmpire})` : firstEmpire;
    const attackLabel = multiAttacker ? `${attackerUids.length} empires` : singleLabel;

    let html = '<div style="margin-top:8px">';

    if (won) {
      html += `<p style="text-align:center">${defenderName} successfully defeated ${attackLabel}.</p>`;
    } else {
      html += `<p style="text-align:center">${attackLabel} broke through ${defenderName}'s defenses.</p>`;
    }

    // ── Attacking armies list ──────────────────────────────────────
    {
      const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
      const liSt = `style="padding:3px 0"`;
      html += `<div ${sep}>`;
      html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">⚔ Attacking Armies</strong>`;
      html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
      if (attackerUids.length === 0) {
        html += `<li ${liSt}>${msg.army_name || 'Unknown'}</li>`;
      } else {
        for (const uid of attackerUids) {
          const eName = empireNames[uid] || `uid ${uid}`;
          const aNames = armyNamesByUid[uid] || [];
          const gains = (msg.attacker_gains || {})[uid] || {};
          const gainParts = Object.entries(gains)
            .filter(([, v]) => v > 0)
            .map(([k, v]) => `+${Math.round(v)} ${k}`)
            .join(', ');
          const armyStr = aNames.length > 0 ? aNames.join(', ') : '–';
          html += `<li ${liSt}><strong>${eName}</strong>: ${armyStr}`;
          if (gainParts) html += ` <span style="color:var(--gold,#f9a825)">${gainParts}</span>`;
          html += `</li>`;
        }
      }
      html += '</ul></div>';
    }

    // ── Battle statistics ──────────────────────────────────────────
    {
      const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
      const liSt = `style="padding:3px 0"`;
      html += `<div ${sep}>`;
      html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">📊 Battle Statistics</strong>`;
      html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
      const spawned = msg.critters_spawned ?? 0;
      const reached = msg.critters_reached ?? 0;
      const killed = msg.critters_killed ?? 0;
      const waves = msg.num_waves ?? 0;
      html += `<li ${liSt}>🐛 Critters: ${spawned} in ${waves} waves — ${reached} reached goal, ${killed} killed</li>`;
      const towers = msg.num_towers ?? 0;
      const goldEarned = Math.round(msg.defender_gold_earned ?? 0);
      html += `<li ${liSt}>🗼 Towers: ${towers} — ${goldEarned} gold earned</li>`;
      if (msg.duration_s > 0) {
        const dur = msg.duration_s;
        const dm = Math.floor(dur / 60);
        const ds = Math.floor(dur % 60);
        html += `<li ${liSt}>⏱ Duration: ${dm > 0 ? dm + 'm ' : ''}${ds}s</li>`;
      }
      html += '</ul></div>';
    }

    if (isDefender && msg.defender_gold_earned > 0) {
      const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
      html += `<div ${sep}>`;
      html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">💰 Gold Earned</strong>`;
      html += `<p style="margin:5px 0 0 0">+${Math.round(msg.defender_gold_earned).toLocaleString()} Gold from defeated attackers</p>`;
      html += `</div>`;
    }

    const loot = msg.loot || {};

    if (!won) {
      const items = st?.items || {};
      const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
      const liSt = `style="padding:3px 0"`;
      const mutedSt = `style="padding:3px 0;color:var(--muted,#888)"`;

      html += `<div ${sep}>`;
      html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">🗡 Stolen from you</strong>`;
      html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
      if (loot.culture > 0) {
        html += `<li ${liSt}>🎭 Culture: <strong>-${Math.round(loot.culture)}</strong></li>`;
      } else {
        html += `<li ${mutedSt}>🎭 Culture: –</li>`;
      }
      if (loot.artefact) {
        const artefactName = items?.artefacts?.[loot.artefact]?.name || loot.artefact;
        html += `<li ${liSt}>⚗️ Artefact: <strong>${artefactName}</strong></li>`;
      } else {
        html += `<li ${mutedSt}>⚗️ Artefact: –</li>`;
      }
      html += '</ul></div>';

      const attackersLabel = multiAttacker ? 'Attackers get' : 'The Attacker gets';
      html += `<div ${sep}>`;
      html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">🎓 ${attackersLabel}</strong>`;
      html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
      if (loot.knowledge) {
        const kn = loot.knowledge;
        const perW = kn.per_winner != null && multiAttacker ? ` (${kn.per_winner} each)` : '';
        html += `<li ${liSt}>📖 ${kn.pct}% of <strong>${kn.name}</strong> → +${kn.amount} 🧪${perW}</li>`;
      } else {
        html += `<li ${mutedSt}>📖 Knowledge: –</li>`;
      }
      html += '</ul></div>';
    }

    if (!won && loot.life_restored > 0) {
      const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
      html += `<div ${sep}>`;
      html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">❤️ Life Restored after Battle</strong>`;
      html += `<p style="margin:5px 0 0 0">+${loot.life_restored}</p>`;
      html += `</div>`;
    }

    html += '</div>';
    content.innerHTML = html;

    const feedbackRow = container.querySelector('#summary-feedback-row');
    if (feedbackRow) feedbackRow.remove();

    if (msg.attacker_uid === 0 && msg.army_name) {
      const row = document.createElement('div');
      row.id = 'summary-feedback-row';
      row.style.cssText = 'display:flex;gap:8px;margin-top:12px;justify-content:center;';
      row.innerHTML = `
        <button id="feedback-easy" style="background:var(--green,#388e3c);color:#fff;border:none;padding:6px 16px;border-radius:var(--radius);cursor:pointer;font-size:13px;">✓ Too Easy</button>
        <button id="feedback-hard" style="background:var(--red,#d32f2f);color:#fff;border:none;padding:6px 16px;border-radius:var(--radius);cursor:pointer;font-size:13px;">✗ Too Hard</button>
      `;
      content.appendChild(row);

      const sendFeedback = async (rating) => {
        row.querySelectorAll('button').forEach((b) => {
          b.disabled = true;
          b.style.opacity = '0.6';
        });
        try {
          await ctx.rest.battleFeedback(msg.army_name, rating);
        } catch (e) {
          console.warn('[feedback] failed:', e);
        }
        row.innerHTML =
          '<span style="color:var(--text-muted);font-size:12px;">✓ Feedback sent</span>';
      };

      row.querySelector('#feedback-easy').addEventListener('click', () => sendFeedback('too_easy'));
      row.querySelector('#feedback-hard').addEventListener('click', () => sendFeedback('too_hard'));
    }

    overlay.style.display = 'flex';
  }

  return {
    spawnFlyingIcon,
    onBattleStatus,
    onBattleSetup,
    onStructureUpdate,
    onBattleUpdate,
    onBattleSummary,
    startStatusLoop,
    stopStatusLoop,
    updateStatus,
    updateStatusPanel,
    updateStatusFromBattleMsg,
    showSummary,
  };
}

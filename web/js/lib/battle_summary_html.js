/**
 * Shared battle summary HTML generator.
 * Used by both the live defense view and the replay view.
 *
 * buildBattleSummaryHtml(msg, catalog, opts) → { titleText, titleColor, bodyHtml }
 *
 * @param {object} msg        - battle_summary message payload
 * @param {object} catalog    - items.catalog for artifact name resolution
 * @param {object} [opts]
 * @param {number} [opts.myUid]         - viewer's uid (used to show gold earned section)
 * @param {number} [opts.defenderUid]   - defender uid from battle state
 * @param {string} [opts.defenderName]  - defender display name
 */
function _esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function buildBattleSummaryHtml(msg, catalog = {}, opts = {}) {
  const won = msg.defender_won || false;
  const titleText = won ? '🛡 Defender Victory' : '⚔ Attacker Victory';
  const titleColor = won ? 'var(--green, #4caf50)' : 'var(--red, #d32f2f)';

  const { myUid, defenderUid, defenderName: _defName } = opts;
  const isDefender = myUid != null && defenderUid != null && myUid == defenderUid;

  const defenderName = _defName || 'Defender';
  const attackerUids = msg.attacker_uids || (msg.attacker_uid != null ? [msg.attacker_uid] : []);
  const empireNames = msg.attacker_empire_names || {};
  const armyNamesByUid = msg.army_names || {};
  const multiAttacker = attackerUids.length > 1;

  const firstUid = attackerUids[0];
  const firstEmpire = _esc(empireNames[firstUid] || msg.attacker_username || msg.attacker_name || 'the attacker');
  const firstArmy = _esc((armyNamesByUid[firstUid] || [])[0] || msg.army_name || '');
  const singleLabel = firstArmy ? `${firstArmy} (${firstEmpire})` : firstEmpire;
  const attackLabel = multiAttacker ? `${attackerUids.length} empires` : singleLabel;
  const defenderNameEsc = _esc(defenderName);

  const sep = `style="margin-top:12px;border-top:1px solid rgba(255,255,255,0.12);padding-top:8px"`;
  const liSt = `style="padding:3px 0"`;
  const mutedSt = `style="padding:3px 0;color:var(--muted,#888)"`;

  let html = '<div style="margin-top:8px">';

  if (won) {
    html += `<p style="text-align:center">${defenderNameEsc} successfully defeated ${attackLabel}.</p>`;
  } else {
    html += `<p style="text-align:center">${attackLabel} broke through ${defenderNameEsc}'s defenses.</p>`;
  }

  // ── Attacking armies ──────────────────────────────────────────────────────
  {
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">⚔ Attacking Armies</strong>`;
    html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
    if (attackerUids.length === 0) {
      html += `<li ${liSt}>${_esc(msg.army_name || 'Unknown')}</li>`;
    } else {
      for (const uid of attackerUids) {
        const eName = _esc(empireNames[uid] || `uid ${uid}`);
        const aNames = (armyNamesByUid[uid] || []).map(_esc);
        const armyStr = aNames.length > 0 ? aNames.join(', ') : '–';
        html += `<li ${liSt}>"${armyStr}" (${eName})</li>`;
      }
    }
    html += '</ul></div>';
  }

  // ── Battle statistics ─────────────────────────────────────────────────────
  {
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

  // ── Gold earned (only when viewer is the defender) ────────────────────────
  if (isDefender && msg.defender_gold_earned > 0) {
    const pvpBonus = Math.round(msg.pvp_gold_bonus ?? 0);
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">💰 Gold Earned</strong>`;
    html += `<p style="margin:5px 0 0 0">+${Math.round(msg.defender_gold_earned).toLocaleString()} Gold from defeated attackers</p>`;
    if (pvpBonus > 0) {
      html += `<p style="margin:4px 0 0 0;color:var(--gold,#ffd54f)">⚡ +${pvpBonus.toLocaleString()} PvP Bonus (×2 vs player)</p>`;
    }
    html += `</div>`;
  }

  const loot = msg.loot || {};

  if (!won) {
    const perAtk = loot.per_attacker || {};
    const totalPenaltyLost = Object.values(perAtk).reduce((s, v) => s + (v.culture_era_penalty_lost || 0), 0);

    // ── Defender loses ──────────────────────────────────────────────────────
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">🏳 Defender Loses</strong>`;
    html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
    if (loot.culture > 0) {
      const penaltyNote = totalPenaltyLost > 0.5
        ? ` <span style="color:var(--muted,#888);font-size:0.88em">(${Math.round(totalPenaltyLost)} reduced due to era penalty)</span>`
        : '';
      html += `<li ${liSt}>🎭 Culture: <strong>-${Math.round(loot.culture)}</strong>${penaltyNote}</li>`;
    } else {
      html += `<li ${mutedSt}>🎭 Culture: –</li>`;
    }
    if (loot.knowledge) {
      const kn = loot.knowledge;
      html += `<li ${liSt}>📖 ${kn.pct}% of <strong>${kn.name}</strong> → -${Math.round(kn.amount)} research effort</li>`;
    } else {
      html += `<li ${mutedSt}>📖 Knowledge: –</li>`;
    }
    const artifacts = loot.artifacts || (loot.artifact ? [{ iid: loot.artifact, winner_uid: attackerUids[0] }] : []);
    if (artifacts.length > 0) {
      for (const art of artifacts) {
        const artName = catalog[art.iid]?.name || art.iid;
        html += `<li ${liSt}>⚜ <strong>${artName}</strong> stolen</li>`;
      }
    } else {
      html += `<li ${mutedSt}>⚜ –</li>`;
    }
    html += '</ul></div>';

    // ── Attacker(s) get ─────────────────────────────────────────────────────
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">⚔ Attacker(s) Get</strong>`;
    html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;

    if (loot.culture > 0) {
      if (multiAttacker) {
        const parts = attackerUids
          .map(uid => {
            const c = perAtk[uid]?.culture ?? 0;
            const pen = perAtk[uid]?.culture_era_penalty_lost ?? 0;
            const penStr = pen > 0.5 ? ` <span style="color:var(--muted,#888);font-size:0.88em">(-${Math.round(pen)} era penalty)</span>` : '';
            return `${_esc(empireNames[uid] || `uid ${uid}`)} +${Math.round(c)}${penStr}`;
          })
          .join(', ');
        const penNote = totalPenaltyLost > 0.5
          ? ` <span style="color:var(--muted,#888);font-size:0.88em">(${Math.round(totalPenaltyLost)} lost to era penalty)</span>`
          : '';
        html += `<li ${liSt}>🎭 Culture: ${parts}${penNote}</li>`;
      } else {
        const c = perAtk[firstUid]?.culture ?? loot.culture;
        const pen = perAtk[firstUid]?.culture_era_penalty_lost ?? 0;
        const penNote = pen > 0.5
          ? ` <span style="color:var(--muted,#888);font-size:0.88em">(-${Math.round(pen)} era penalty)</span>`
          : '';
        html += `<li ${liSt}>🎭 Culture: +${Math.round(c)}${penNote}</li>`;
      }
    } else {
      html += `<li ${mutedSt}>🎭 Culture: –</li>`;
    }

    if (loot.knowledge) {
      const kn = loot.knowledge;
      const eachNote = kn.per_winner != null && multiAttacker
        ? ` <span style="color:var(--muted,#888);font-size:0.88em">(+${Math.round(kn.per_winner)} each)</span>`
        : '';
      html += `<li ${liSt}>📖 +${Math.round(kn.amount)} <strong>${kn.name}</strong> research${eachNote}</li>`;
    } else {
      html += `<li ${mutedSt}>📖 Knowledge: –</li>`;
    }

    if (artifacts.length > 0) {
      for (const art of artifacts) {
        const artName = catalog[art.iid]?.name || art.iid;
        const winnerName = _esc(empireNames[art.winner_uid] || `uid ${art.winner_uid}`);
        html += `<li ${liSt}>⚜ <strong>${artName}</strong> → ${winnerName}</li>`;
      }
    } else {
      html += `<li ${mutedSt}>⚜ –</li>`;
    }
    html += '</ul></div>';
  }

  if (!won && loot.life_restored > 0) {
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">❤️ Life Restored after Battle</strong>`;
    html += `<p style="margin:5px 0 0 0">+${loot.life_restored}</p>`;
    html += `</div>`;
  }

  // ── Ruler XP ──────────────────────────────────────────────────────────────
  const rulerXp = msg.ruler_xp || {};
  const rulerXpPvpBonus = msg.ruler_xp_pvp_bonus || {};
  const rulerXpEntries = attackerUids
    .map(uid => ({ uid, xp: rulerXp[String(uid)] ?? rulerXp[uid] ?? 0 }))
    .filter(e => e.xp > 0);
  if (rulerXpEntries.length > 0 || msg.ruler_reached_goal) {
    html += `<div ${sep}>`;
    html += `<strong style="font-size:0.9em;text-transform:uppercase;letter-spacing:.04em">👑 Ruler XP</strong>`;
    html += `<ul style="list-style:none;padding:0;margin:5px 0 0 0">`;
    for (const { uid, xp } of rulerXpEntries) {
      const label = multiAttacker ? (empireNames[uid] || `uid ${uid}`) : null;
      const bonus = Math.round(rulerXpPvpBonus[String(uid)] ?? rulerXpPvpBonus[uid] ?? 0);
      const bonusNote = bonus > 0 ? ` <span style="color:var(--gold,#ffd54f)">⚡ +${bonus} era bonus (×2)</span>` : '';
      html += `<li ${liSt}>👑 ${label ? `${label}: ` : ''}+${Math.round(xp)} XP${bonusNote}</li>`;
    }
    if (msg.ruler_reached_goal) {
      const stealBonuses = msg.ruler_artifact_steal_bonus || {};
      const firstUidBonus = typeof stealBonuses === 'object'
        ? (stealBonuses[String(firstUid)] ?? stealBonuses[firstUid] ?? 0.15)
        : (stealBonuses || 0.15);
      html += `<li ${liSt} style="color:var(--gold,#ffd54f)">⚜ Ruler reached the castle — +${Math.round(firstUidBonus * 100)}% artifact steal chance</li>`;
    }
    html += '</ul></div>';
  }

  html += '</div>';
  return { titleText, titleColor, bodyHtml: html };
}

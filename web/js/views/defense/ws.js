/**
 * Battle WebSocket module.
 *
 * Usage:
 *   import { createBattleWs } from './defense/ws.js';
 *   const ws = createBattleWs(ctx);
 *   ws.connectIfNeeded();
 *   ws.disconnect();
 *
 * ctx = {
 *   getSt()             → current state store snapshot
 *   getContainer()      → current container HTMLElement
 *   getPendingAttackId() → number | null
 *   getSpectateUid()    → number | null
 *   getBattleState()    → mutable _battleState object
 *   onMessage(msg)      → dispatch incoming WS message
 *   addDebugLog(msg)    → append to debug panel
 *   updateBattleStatusVisibility(visible) → show/hide status rows
 *   updateStatusFromBattleMsg()           → refresh status panel
 *   setBattlePhase(phase)                 → mutate _battleState.phase
 *   setPendingAttackId(id)                → capture attack id from phase event
 * }
 */

export function createBattleWs(ctx) {
  let _ws = null;
  let _wsUrl = '';
  let _wsConnected = false;
  let _wsReconnectTimer = null;
  let _wsIntentionalClose = false;
  let _wsConnectTimeout = null;

  function _updateWsIndicator(online) {
    const el = document.getElementById('ws-status-indicator');
    if (el) {
      el.classList.toggle('connected', online);
      el.classList.toggle('disconnected', !online);
      el.title = online ? 'Battle WS: connected' : 'Battle WS: disconnected';
    }
  }

  function send(msg) {
    if (_ws && _ws.readyState === WebSocket.OPEN) {
      const st = ctx.getSt();
      if (st?.auth?.uid) msg.sender = st.auth.uid;
      _ws.send(JSON.stringify(msg));
    }
  }

  function connect() {
    if (_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    _wsIntentionalClose = false;

    const { rest } = window._defenseWsRestRef || {};
    const restMod = rest || window._restModule;
    if (!restMod) {
      console.warn('[BattleWs] rest module not available');
      return;
    }

    const restBase = restMod.baseUrl || `http://${window.location.hostname}:8080`;
    const restUrl = new URL(restBase);
    const wsProto = restUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    const baseUrl = `${wsProto}//${restUrl.host}/ws`;
    _wsUrl = restMod.getAuthenticatedWsUrl(baseUrl);

    ctx.addDebugLog(`🔌 WS connecting to ${baseUrl}...`);
    let ws;
    try {
      ws = new WebSocket(_wsUrl);
    } catch (err) {
      ctx.addDebugLog(`❌ WS constructor error: ${err.message}`);
      return;
    }
    _ws = ws;

    _wsConnectTimeout = setTimeout(() => {
      if (ws.readyState === WebSocket.CONNECTING) {
        ctx.addDebugLog(`⏱ WS timeout after 8s (still CONNECTING) — closing`);
        ws.close();
      }
    }, 8000);

    ws.addEventListener('open', () => {
      clearTimeout(_wsConnectTimeout);
      _wsConnected = true;
      ctx.addDebugLog('🟢 WS connected');
      _updateWsIndicator(true);

      const st = ctx.getSt();
      const pendingId = ctx.getPendingAttackId();
      const spectateUid = ctx.getSpectateUid();
      send({
        type: 'battle_register',
        target_uid: spectateUid ?? st?.summary?.uid,
        ...(pendingId != null ? { attack_id: pendingId } : {}),
      });
    });

    ws.addEventListener('message', (ev) => {
      let msg;
      try {
        msg = JSON.parse(ev.data);
      } catch (err) {
        console.warn('[Battle.WS] invalid JSON:', ev.data);
        return;
      }
      _dispatchMessage(msg);
    });

    ws.addEventListener('close', (ev) => {
      clearTimeout(_wsConnectTimeout);
      _wsConnected = false;
      _updateWsIndicator(false);
      ctx.addDebugLog(`🔴 WS closed (code=${ev.code} reason=${ev.reason || 'none'})`);

      if (!_wsIntentionalClose) {
        _wsReconnectTimer = setTimeout(() => connectIfNeeded(), 2000);
      }
      _ws = null;
    });

    ws.addEventListener('error', () => {
      clearTimeout(_wsConnectTimeout);
      ctx.addDebugLog(`⚠ WS error (readyState=${ws.readyState}, url=${baseUrl})`);
    });
  }

  function _dispatchMessage(msg) {
    const st = ctx.getSt();
    const spectateUid = ctx.getSpectateUid();
    const relevantDefender = spectateUid ?? st?.summary?.uid;

    switch (msg.type) {
      case 'welcome':
        ctx.addDebugLog(`WS welcome: guest_uid=${msg.temp_uid}`);
        break;
      case 'battle_setup':
        if (msg.defender_uid !== relevantDefender) break;
        ctx.onMessage(msg);
        break;
      case 'battle_update':
        if (msg.defender_uid !== undefined && msg.defender_uid !== relevantDefender) break;
        ctx.onMessage(msg);
        break;
      case 'battle_summary':
        if (msg.defender_uid !== undefined && msg.defender_uid !== relevantDefender) break;
        ctx.onMessage(msg);
        break;
      case 'battle_status':
        if (msg.defender_uid !== relevantDefender) break;
        ctx.onMessage(msg);
        break;
      case 'structure_update':
        ctx.onMessage(msg);
        break;
      case 'attack_phase_changed':
        if (msg.defender_uid !== relevantDefender) break;
        ctx.addDebugLog(`Phase changed: attack_id=${msg.attack_id} → ${msg.new_phase}`);
        if (msg.new_phase === 'in_siege' && !ctx.getPendingAttackId() && msg.attack_id != null) {
          ctx.setPendingAttackId(msg.attack_id);
        }
        if (msg.new_phase) {
          ctx.setBattlePhase(msg.new_phase);
          ctx.updateStatusFromBattleMsg();
        }
        break;
      default:
        break;
    }
  }

  function disconnect() {
    _wsIntentionalClose = true;
    if (_wsConnectTimeout) {
      clearTimeout(_wsConnectTimeout);
      _wsConnectTimeout = null;
    }
    if (_wsReconnectTimer) {
      clearTimeout(_wsReconnectTimer);
      _wsReconnectTimer = null;
    }
    if (_ws) {
      const st = ctx.getSt();
      const spectateUid = ctx.getSpectateUid();
      send({ type: 'battle_unregister', target_uid: spectateUid ?? st?.summary?.uid });
      _ws.close(1000, 'leaving-battle');
      _ws = null;
      _wsConnected = false;
      ctx.addDebugLog('🔌 WS disconnected (intentional)');
      _updateWsIndicator(false);
    }
  }

  function connectIfNeeded() {
    const st = ctx.getSt();
    const ACTIVE_PHASES = ['in_siege', 'in_battle'];
    const summary = st?.summary || {};
    const allAttacks = [...(summary.attacks_incoming || []), ...(summary.attacks_outgoing || [])];
    const hasActiveAttack =
      ctx.getPendingAttackId() != null || allAttacks.some((a) => ACTIVE_PHASES.includes(a.phase));

    ctx.updateBattleStatusVisibility(hasActiveAttack);

    if (hasActiveAttack) {
      connect();
    } else {
      ctx.addDebugLog('No active attack — WS not connected');
    }
  }

  function isConnected() {
    return _wsConnected;
  }

  return { connect, disconnect, send, connectIfNeeded, isConnected };
}

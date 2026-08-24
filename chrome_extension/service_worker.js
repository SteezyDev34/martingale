// Service Worker — maintient la connexion WebSocket avec Python
// Python écoute sur ws://localhost:9999

const WS_URL = 'ws://localhost:9999';
const RECONNECT_DELAY = 2000;
const KEEPALIVE_INTERVAL = 20; // secondes (chrome.alarms, limite 1 min)

let ws = null;
let wsConnected = false;
let pending1xbetTabId = null; // onglet 1xBet actif

// ─── Keepalive via chrome.alarms (empêche le service worker de s'endormir) ───

chrome.alarms.create('keepalive', { periodInMinutes: 0.4 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'keepalive') {
    if (!wsConnected) connectWS();
  }
});

// ─── WebSocket ────────────────────────────────────────────────────────────────

function connectWS() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  try {
    ws = new WebSocket(WS_URL);
  } catch (e) {
    console.warn('[WS] Impossible de créer WebSocket:', e);
    setTimeout(connectWS, RECONNECT_DELAY);
    return;
  }

  ws.onopen = () => {
    wsConnected = true;
    console.log('[WS] Connecté à Python');
    ws.send(JSON.stringify({ action: 'extension_ready', version: '1.0.0' }));
  };

  ws.onmessage = (event) => {
    let msg;
    try { msg = JSON.parse(event.data); } catch { return; }
    handlePythonMessage(msg);
  };

  ws.onclose = () => {
    wsConnected = false;
    console.warn('[WS] Déconnecté, reconnexion dans', RECONNECT_DELAY, 'ms');
    setTimeout(connectWS, RECONNECT_DELAY);
  };

  ws.onerror = (err) => {
    console.warn('[WS] Erreur WebSocket');
    ws.close();
  };
}

// ─── Envoi vers Python ────────────────────────────────────────────────────────

function sendToPython(msg) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(msg));
  } else {
    console.warn('[WS] Message perdu (WS fermé):', msg);
  }
}

// ─── Dispatcher des messages Python → Extension ──────────────────────────────

async function handlePythonMessage(msg) {
  console.log('[Python→Ext]', msg);

  switch (msg.action) {

    // Python demande à naviguer vers une URL 1xBet
    case 'navigate': {
      const tab = await find1xbetTab();
      if (tab) {
        await chrome.tabs.update(tab.id, { url: msg.url, active: true });
        pending1xbetTabId = tab.id;
        sendToPython({ action: 'navigate_ack', req_id: msg.req_id, tab_id: tab.id });
      } else {
        const newTab = await chrome.tabs.create({ url: msg.url, active: true });
        pending1xbetTabId = newTab.id;
        sendToPython({ action: 'navigate_ack', req_id: msg.req_id, tab_id: newTab.id });
      }
      break;
    }

    // Python demande l'état actuel du DOM (score, jeu, set)
    case 'get_state': {
      const tabId = msg.tab_id || pending1xbetTabId;
      if (!tabId) { sendToPython({ action: 'error', req_id: msg.req_id, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.getState?.() || null);
      sendToPython({ action: 'state_response', req_id: msg.req_id, data: result, tab_id: tabId });
      break;
    }

    // Python demande de placer un pari
    case 'place_bet': {
      const tabId = msg.tab_id || pending1xbetTabId;
      if (!tabId) { sendToPython({ action: 'bet_result', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.placeBet?.(args), msg);
      sendToPython({ action: 'bet_result', req_id: msg.req_id, ...result, tab_id: tabId });
      break;
    }

    // Python demande de supprimer le pari dans le betslip
    case 'delete_bet': {
      const tabId = msg.tab_id || pending1xbetTabId;
      if (!tabId) { sendToPython({ action: 'delete_bet_ack', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.deleteBet?.() || {});
      sendToPython({ action: 'delete_bet_ack', req_id: msg.req_id, ...result, tab_id: tabId });
      break;
    }

    // Python demande de valider (confirmer) le pari
    case 'validate_bet': {
      const tabId = msg.tab_id || pending1xbetTabId;
      if (!tabId) { sendToPython({ action: 'validate_bet_ack', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.validateBet?.(args), msg);
      sendToPython({ action: 'validate_bet_ack', req_id: msg.req_id, ...result, tab_id: tabId });
      break;
    }

    // Python demande le résultat du dernier pari (WIN/LOSE)
    case 'get_result': {
      const tabId = msg.tab_id || pending1xbetTabId;
      if (!tabId) { sendToPython({ action: 'result_response', req_id: msg.req_id, result: null, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.getResult?.() || {});
      sendToPython({ action: 'result_response', req_id: msg.req_id, ...result, tab_id: tabId });
      break;
    }

    // Python demande les noms des joueurs
    case 'get_players': {
      const tabId = msg.tab_id || pending1xbetTabId;
      if (!tabId) { sendToPython({ action: 'players_response', req_id: msg.req_id, p1: null, p2: null, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.getPlayers?.() || {});
      sendToPython({ action: 'players_response', req_id: msg.req_id, ...result, tab_id: tabId });
      break;
    }

    default:
      console.warn('[WS] Action inconnue:', msg.action);
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function find1xbetTab() {
  const tabs = await chrome.tabs.query({});
  return tabs.find(t =>
    t.url && (t.url.includes('1xbet') || t.url.includes('1x-bet'))
  ) || null;
}

async function execInTab(tabId, fn, args = null) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: fn,
      args: args ? [args] : [],
    });
    return results?.[0]?.result ?? null;
  } catch (e) {
    console.error('[execInTab] Erreur:', e);
    return null;
  }
}

// ─── Messages depuis content scripts ─────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (!msg || !msg.action) return;

  // Enrichir avec tab_id
  const enriched = { ...msg, tab_id: sender.tab?.id };

  // Score push (MutationObserver déclenché par content script)
  if (msg.action === 'score_update' || msg.action === 'game_update' || msg.action === 'set_update') {
    sendToPython(enriched);
    return;
  }

  // Tout autre message du content script → forward à Python
  sendToPython(enriched);
});

// ─── Init ─────────────────────────────────────────────────────────────────────

connectWS();

// Service Worker — maintient la connexion WebSocket avec Python
// Python écoute sur ws://localhost:9999

const WS_URL = 'ws://localhost:9999';
const RECONNECT_DELAY = 2000;
const KEEPALIVE_INTERVAL = 20; // secondes (chrome.alarms, limite 1 min)

let ws = null;
let wsConnected = false;
let pending1xbetTabId = null; // onglet 1xBet actif

// ─── Keepalive via chrome.alarms (empêche le service worker de s'endormir) ───

chrome.alarms.get('keepalive', (a) => { if (!a) chrome.alarms.create('keepalive', { periodInMinutes: 0.4 }); });
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
    handlePythonMessage(msg).catch(e => console.error('[WS] handlePythonMessage erreur:', e));
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
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'error', req_id: msg.req_id, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.getState?.() || null);
      sendToPython({ action: 'state_response', req_id: msg.req_id, data: result, tab_id: tabId });
      break;
    }

    // Python demande de placer un pari
    case 'place_bet': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'bet_result', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.placeBet?.(args), msg);
      sendToPython({ action: 'bet_result', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de supprimer le pari dans le betslip
    case 'delete_bet': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'delete_bet_ack', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.deleteBet?.() || {});
      sendToPython({ action: 'delete_bet_ack', req_id: msg.req_id, ...(result || {}), tab_id: tabId });
      break;
    }

    // Python demande de remplir uniquement la mise (marché déjà sélectionné)
    case 'set_stake': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'set_stake_ack', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (mise) => window._martingale?.setStake?.(mise), msg.mise);
      sendToPython({ action: 'set_stake_ack', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de valider (confirmer) le pari
    case 'validate_bet': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'validate_bet_ack', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.validateBet?.(args), msg);
      sendToPython({ action: 'validate_bet_ack', req_id: msg.req_id, ...(result || { validated: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande le résultat du dernier pari (WIN/LOSE)
    case 'get_result': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'result_response', req_id: msg.req_id, result: null, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.getResult?.() || {});
      sendToPython({ action: 'result_response', req_id: msg.req_id, ...(result || { result: null }), tab_id: tabId });
      break;
    }

    // Python demande les noms des joueurs
    case 'get_players': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'players_response', req_id: msg.req_id, p1: null, p2: null, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.getPlayers?.() || {});
      sendToPython({ action: 'players_response', req_id: msg.req_id, ...(result || { p1: null, p2: null }), tab_id: tabId });
      break;
    }

    // Python demande la liste des ligues/matchs (page live tennis)
    case 'get_match_list': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'match_list_response', req_id: msg.req_id, leagues: [] }); break; }
      // getMatchList() est async — executeScript attend la Promise (Chrome 90+)
      const result = await execInTab(tabId, () => window._martingale?.getMatchList?.() ?? null);
      sendToPython({ action: 'match_list_response', req_id: msg.req_id, leagues: result || [], tab_id: tabId });
      break;
    }

    // Python demande de rechercher un match par nom d'équipes
    case 'search_match': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'search_match_response', req_id: msg.req_id, found: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.searchMatch?.(args), msg);
      sendToPython({ action: 'search_match_response', req_id: msg.req_id, ...(result || { found: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Étape 1 : clique le bouton recherche (provoque une navigation vers /search-events —
    // on ne fait QUE cliquer ici, sans rien attendre après, cf. searchOnResultsPage).
    case 'click_search_button': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'click_search_button_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.clickSearchButton?.());
      sendToPython({ action: 'click_search_button_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Étape 2 : une fois sur la page /search-events (nouveau contexte JS réinjecté),
    // tape le texte de recherche et lit les résultats.
    case 'search_on_results_page': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'search_on_results_page_response', req_id: msg.req_id, found: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.searchOnResultsPage?.(args), msg);
      sendToPython({ action: 'search_on_results_page_response', req_id: msg.req_id, ...(result || { found: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de sélectionner un marché simple
    case 'select_market': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'select_market_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.selectMarket?.(args), msg);
      sendToPython({ action: 'select_market_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de sélectionner plusieurs marchés (pari combiné / constructor bet)
    case 'select_combined_markets': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'select_combined_markets_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (legs) => window._martingale?.selectCombinedMarkets?.(legs), msg.legs);
      sendToPython({ action: 'select_combined_markets_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de charger un code coupon
    case 'load_coupon_code': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'load_coupon_code_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (code) => window._martingale?.loadCouponCode?.(code), msg.code);
      sendToPython({ action: 'load_coupon_code_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // DEBUG uniquement — liste les options du dropdown de catégorie sans en cliquer aucune
    case 'debug_list_category_options': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'debug_list_category_options_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.debugListCategoryOptions?.());
      sendToPython({ action: 'debug_list_category_options_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de cliquer une option déjà visible du dropdown de catégorie (RetourTpsRegMobile)
    case 'click_category_option': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'click_category_option_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (text) => window._martingale?.clickCategoryOption?.(text), msg.text);
      sendToPython({ action: 'click_category_option_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande la liste des ligues sur la page desktop "à venir" (classementeDeMatch)
    case 'scan_league_list': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'scan_league_list_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.scanLeagueList?.());
      sendToPython({ action: 'scan_league_list_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande les matchs de la page de ligue desktop courante (classementeDeMatch)
    case 'scan_league_matches': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'scan_league_matches_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.scanLeagueMatches?.());
      sendToPython({ action: 'scan_league_matches_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande d'ouvrir le dropdown de catégorie + filtrer par recherche (AfficherParisMobile)
    case 'open_category_and_search': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'open_category_and_search_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.openCategoryAndSearch?.(args), msg);
      sendToPython({ action: 'open_category_and_search_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Sélectionne l'option du dropdown de catégorie une seule fois (sans rechercher)
    case 'select_category_option': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'select_category_option_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.selectCategoryOption?.(args.categorie_text), msg);
      sendToPython({ action: 'select_category_option_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Retape la recherche (key) sans re-cliquer le dropdown — pour le fallback de clés
    case 'search_market_key': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'search_market_key_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.searchMarketKey?.(args.key), msg);
      sendToPython({ action: 'search_market_key_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de lire l'indicateur "balle" (quel joueur a le point)
    case 'read_ball_indicator': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'read_ball_indicator_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.readBallIndicator?.());
      sendToPython({ action: 'read_ball_indicator_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de sélectionner un marché par texte déjà calculé (GetBetOld)
    case 'select_market_by_text': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'select_market_by_text_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (text) => window._martingale?.selectMarketByText?.(text), msg.text);
      sendToPython({ action: 'select_market_by_text_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // DEBUG uniquement — liste tous les onglets 1xBet détectés (diagnostiquer un mauvais choix d'onglet)
    case 'debug_list_tabs': {
      const allTabs = await chrome.tabs.query({});
      const xbetTabs = allTabs.filter(t => t.url && (t.url.includes('1xbet') || t.url.includes('1x-bet')));
      const info = xbetTabs.map(t => ({ id: t.id, url: t.url, active: t.active, windowId: t.windowId }));
      sendToPython({
        action: 'debug_list_tabs_response',
        req_id: msg.req_id,
        tabs: info,
        pending1xbetTabId,
      });
      break;
    }

    // DEBUG uniquement — scanne les classNames contenant un des mots-clés donnés
    case 'debug_scan_classes': {
      const tabId = await resolveTabId(msg);
      if (!tabId) { sendToPython({ action: 'debug_scan_classes_response', req_id: msg.req_id, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (keywords) => {
        const els = Array.from(document.querySelectorAll('[class]'));
        const seen = new Set();
        const out = [];
        for (const el of els) {
          const cls = el.className;
          if (typeof cls !== 'string') continue;
          for (const kw of keywords) {
            if (cls.toLowerCase().includes(kw) && !seen.has(cls)) {
              seen.add(cls);
              out.push({ cls, tag: el.tagName, text: (el.textContent || '').trim().slice(0, 50), visible: !!el.offsetParent });
              break;
            }
          }
        }
        return out.slice(0, 300);
      }, msg.keywords);
      sendToPython({ action: 'debug_scan_classes_response', req_id: msg.req_id, result, tab_id: tabId });
      break;
    }

    default:
      console.warn('[WS] Action inconnue:', msg.action);
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function is1xbetUrl(url) {
  return !!url && (url.includes('1xbet') || url.includes('1x-bet'));
}

async function find1xbetTab() {
  const tabs = await chrome.tabs.query({});
  const xbetTabs = tabs.filter(t => is1xbetUrl(t.url));
  console.log(`[find1xbetTab] ${xbetTabs.length} onglet(s) 1xBet trouvé(s):`,
    xbetTabs.map(t => ({ id: t.id, url: t.url, active: t.active, windowId: t.windowId })));

  if (xbetTabs.length === 0) return null;

  // Priorité à l'onglet 1xBet actif (au premier plan) — évite de cibler un onglet
  // 1xBet oublié en arrière-plan quand plusieurs sont ouverts.
  const activeOne = xbetTabs.find(t => t.active);
  const chosen = activeOne || xbetTabs[0];
  console.log(`[find1xbetTab] onglet choisi: id=${chosen.id} active=${chosen.active} url=${chosen.url}`);
  return chosen;
}

// Résout l'onglet cible : tab_id explicite > dernier onglet navigué > recherche live
async function resolveTabId(msg) {
  if (msg.tab_id) {
    console.log(`[resolveTabId] tab_id explicite: ${msg.tab_id}`);
    return msg.tab_id;
  }
  // Re-vérifie l'onglet 1xBet actif à chaque appel (pas seulement pending1xbetTabId,
  // qui peut être obsolète si l'utilisateur a changé d'onglet depuis le dernier navigate()).
  const tab = await find1xbetTab();
  if (tab) return tab.id;
  if (pending1xbetTabId) {
    console.log(`[resolveTabId] fallback pending1xbetTabId: ${pending1xbetTabId}`);
    return pending1xbetTabId;
  }
  console.warn('[resolveTabId] aucun onglet 1xBet trouvé');
  return null;
}

async function execInTab(tabId, fn, args = null) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: fn,
      args: args ? [args] : [],
    });
    console.log('[execInTab] résultat brut:', results);
    if (results?.[0]?.result === undefined && results?.[0]?.result !== null) {
      console.warn('[execInTab] result undefined — le contenu de la page a peut-être renvoyé undefined');
    }
    return results?.[0]?.result ?? null;
  } catch (e) {
    console.error('[execInTab] Erreur:', e && e.message, e);
    return { error: 'exec_exception', message: String(e && e.message || e) };
  }
}

// ─── Messages depuis content scripts / popup ─────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.action === 'get_ws_status') {
    sendResponse({ connected: wsConnected });
    return true;
  }
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

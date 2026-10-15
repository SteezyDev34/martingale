// Service Worker — maintient une connexion WebSocket PAR SCRIPT PYTHON (un port
// dédié par scriptType, cf. WS_PORT dans chaque fichier SCRIPTS_*/*.py), chacune
// liée à son propre onglet 1xBet. Ça permet à plusieurs bots de tourner en même
// temps sans se marcher dessus : contrairement à l'ancienne version (un seul ws
// global + find1xbetTab() qui prenait "l'onglet 1xBet actif"), chaque connexion
// ne pilote jamais que l'onglet qu'elle a elle-même ouvert.

const RECONNECT_DELAY = 2000;
const KEEPALIVE_INTERVAL = 20; // secondes (chrome.alarms, limite 1 min)

// Liste des ports à surveiller — un par script bridge-only. La plupart n'auront
// personne à l'écoute la majeure partie du temps (le script correspondant n'est
// pas lancé) : la connexion échoue et retente toutes les RECONNECT_DELAY ms sans
// conséquence, exactement comme l'ancien connectWS() le faisait déjà pour 9999.
const WS_PORTS = [
  9001, // SCRIPTS_1530A/1530A-1.py
  9002, // SCRIPTS_1530A/1530A-2.py
  9003, // SCRIPTS_1530A/1530A-3.py
  9004, // SCRIPTS_4P6P/4P6P-1.py
  9005, // SCRIPTS_4P6P/4P6P-2.py
  9006, // SCRIPTS_4P6P2/4P6P2-1.py
  9007, // SCRIPTS_4P6P2/4P6P2-2.py
  9008, // SCRIPTS_5P40A/5P40A-1.py
  9009, // SCRIPTS_5P40A/5P40A-2.py
  9010, // SCRIPTS_5P40A2/5P40A2-1.py
  9011, // SCRIPTS_5P40A2/5P40A2-2.py
  9012, // SCRIPTS_BREAK/BREAKP-1.py
  9013, // SCRIPTS_BREAK/BREAKP-2.py
  9014, // SCRIPTS_BREAK2/BREAK2-1.py
  9015, // SCRIPTS_BREAK2/BREAK2-2.py
  9016, // SCRIPTS_HOLD/HOLD-1.py
  9101, // Functions/Bookmakers/StakeBridge.py (router.py — placement Stake.bet)
  9999, // port historique — usage manuel/debug (python websocket_server.py)
];

// port → { ws, connected, tabId }
const connections = new Map(WS_PORTS.map(p => [p, { ws: null, connected: false, tabId: null }]));

// ─── Keepalive via chrome.alarms (empêche le service worker de s'endormir) ───

chrome.alarms.get('keepalive', (a) => { if (!a) chrome.alarms.create('keepalive', { periodInMinutes: 0.4 }); });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'keepalive') {
    for (const port of WS_PORTS) {
      if (!connections.get(port).connected) connectWS(port);
    }
  }
});

// Si l'onglet d'un bot est fermé manuellement, oublier son tabId pour que le
// prochain navigate() en recrée un neuf au lieu de cibler un onglet mort.
chrome.tabs.onRemoved.addListener((tabId) => {
  for (const conn of connections.values()) {
    if (conn.tabId === tabId) conn.tabId = null;
  }
});

// ─── WebSocket ────────────────────────────────────────────────────────────────

function connectWS(port) {
  const conn = connections.get(port);
  if (conn.ws && (conn.ws.readyState === WebSocket.OPEN || conn.ws.readyState === WebSocket.CONNECTING)) return;

  let ws;
  try {
    ws = new WebSocket(`ws://localhost:${port}`);
  } catch (e) {
    console.warn(`[WS:${port}] Impossible de créer WebSocket:`, e);
    setTimeout(() => connectWS(port), RECONNECT_DELAY);
    return;
  }
  conn.ws = ws;

  ws.onopen = () => {
    conn.connected = true;
    console.log(`[WS:${port}] Connecté à Python`);
    ws.send(JSON.stringify({ action: 'extension_ready', version: '2.0.0' }));
  };

  ws.onmessage = (event) => {
    let msg;
    try { msg = JSON.parse(event.data); } catch { return; }
    handlePythonMessage(msg, port).catch(e => console.error(`[WS:${port}] handlePythonMessage erreur:`, e));
  };

  ws.onclose = () => {
    conn.connected = false;
    console.warn(`[WS:${port}] Déconnecté, reconnexion dans`, RECONNECT_DELAY, 'ms');
    setTimeout(() => connectWS(port), RECONNECT_DELAY);
  };

  ws.onerror = () => {
    console.warn(`[WS:${port}] Erreur WebSocket`);
    ws.close();
  };
}

// ─── Envoi vers Python ────────────────────────────────────────────────────────

function sendToPython(port, msg) {
  const conn = connections.get(port);
  if (conn?.ws && conn.ws.readyState === WebSocket.OPEN) {
    conn.ws.send(JSON.stringify(msg));
  } else {
    console.warn(`[WS:${port}] Message perdu (WS fermé):`, msg);
  }
}

// ─── Dispatcher des messages Python → Extension ──────────────────────────────

async function handlePythonMessage(msg, port) {
  console.log(`[Python:${port}→Ext]`, msg);
  const conn = connections.get(port);

  switch (msg.action) {

    // Python demande à naviguer vers une URL 1xBet. Onglet explicite pour cette
    // connexion : si on en a déjà un (msg.tab_id ou conn.tabId mémorisé), on le
    // réutilise ; sinon (premier appel de ce script) on en crée un NEUF — jamais
    // "l'onglet 1xBet actif" comme avant, pour ne pas voler l'onglet d'un autre
    // script déjà en cours.
    case 'navigate': {
      let targetTabId = msg.tab_id || conn.tabId;
      if (targetTabId) {
        try {
          await chrome.tabs.update(targetTabId, { url: msg.url });
        } catch (e) {
          // Onglet fermé entre-temps (ex: fermé manuellement) → en recréer un.
          targetTabId = null;
        }
      }
      if (!targetTabId) {
        const tab = await chrome.tabs.create({ url: msg.url, active: false });
        targetTabId = tab.id;
      }
      conn.tabId = targetTabId;
      await waitForTabLoad(targetTabId);
      sendToPython(port, { action: 'navigate_ack', req_id: msg.req_id, tab_id: targetTabId });
      break;
    }

    // Python demande l'état actuel du DOM (score, jeu, set)
    case 'get_state': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'error', req_id: msg.req_id, error: 'no_tab' }); break; }
      const result = await activateThenExec(tabId, () => window._martingale?.getState?.() || null);
      sendToPython(port, { action: 'state_response', req_id: msg.req_id, data: result, tab_id: tabId });
      break;
    }

    // Python demande de placer un pari
    case 'place_bet': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'bet_result', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.placeBet?.(args), msg);
      sendToPython(port, { action: 'bet_result', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de supprimer le pari dans le betslip
    case 'delete_bet': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'delete_bet_ack', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.deleteBet?.() || {});
      sendToPython(port, { action: 'delete_bet_ack', req_id: msg.req_id, ...(result || {}), tab_id: tabId });
      break;
    }

    // Python demande de remplir uniquement la mise (marché déjà sélectionné)
    case 'set_stake': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'set_stake_ack', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (mise) => window._martingale?.setStake?.(mise), msg.mise);
      sendToPython(port, { action: 'set_stake_ack', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de valider (confirmer) le pari
    case 'validate_bet': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'validate_bet_ack', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.validateBet?.(args), msg);
      sendToPython(port, { action: 'validate_bet_ack', req_id: msg.req_id, ...(result || { validated: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande le résultat du dernier pari (WIN/LOSE)
    case 'get_result': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'result_response', req_id: msg.req_id, result: null, error: 'no_tab' }); break; }
      const result = await activateThenExec(tabId, () => window._martingale?.getResult?.() || {});
      sendToPython(port, { action: 'result_response', req_id: msg.req_id, ...(result || { result: null }), tab_id: tabId });
      break;
    }

    // Python demande les noms des joueurs
    case 'get_players': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'players_response', req_id: msg.req_id, p1: null, p2: null, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.getPlayers?.() || {});
      sendToPython(port, { action: 'players_response', req_id: msg.req_id, ...(result || { p1: null, p2: null }), tab_id: tabId });
      break;
    }

    // Python demande la liste des ligues/matchs (page live tennis)
    case 'get_match_list': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'match_list_response', req_id: msg.req_id, leagues: [] }); break; }
      // getMatchList() est async — executeScript attend la Promise (Chrome 90+)
      const result = await execInTab(tabId, () => window._martingale?.getMatchList?.() ?? null);
      sendToPython(port, { action: 'match_list_response', req_id: msg.req_id, leagues: result || [], tab_id: tabId });
      break;
    }

    // Python demande de rechercher un match par nom d'équipes
    case 'search_match': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'search_match_response', req_id: msg.req_id, found: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.searchMatch?.(args), msg);
      sendToPython(port, { action: 'search_match_response', req_id: msg.req_id, ...(result || { found: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Étape 1 : clique le bouton recherche (provoque une navigation vers /search-events —
    // on ne fait QUE cliquer ici, sans rien attendre après, cf. searchOnResultsPage).
    case 'click_search_button': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'click_search_button_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.clickSearchButton?.());
      sendToPython(port, { action: 'click_search_button_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Étape 2 : une fois sur la page /search-events (nouveau contexte JS réinjecté),
    // tape le texte de recherche et lit les résultats.
    case 'search_on_results_page': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'search_on_results_page_response', req_id: msg.req_id, found: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.searchOnResultsPage?.(args), msg);
      sendToPython(port, { action: 'search_on_results_page_response', req_id: msg.req_id, ...(result || { found: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de sélectionner un marché simple
    case 'select_market': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'select_market_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.selectMarket?.(args), msg);
      sendToPython(port, { action: 'select_market_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de sélectionner plusieurs marchés (pari combiné / constructor bet)
    case 'select_combined_markets': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'select_combined_markets_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (legs) => window._martingale?.selectCombinedMarkets?.(legs), msg.legs);
      sendToPython(port, { action: 'select_combined_markets_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de charger un code coupon
    case 'load_coupon_code': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'load_coupon_code_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (code) => window._martingale?.loadCouponCode?.(code), msg.code);
      sendToPython(port, { action: 'load_coupon_code_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // DEBUG uniquement — liste les options du dropdown de catégorie sans en cliquer aucune
    case 'debug_list_category_options': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'debug_list_category_options_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.debugListCategoryOptions?.());
      sendToPython(port, { action: 'debug_list_category_options_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de cliquer une option déjà visible du dropdown de catégorie (RetourTpsRegMobile)
    case 'click_category_option': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'click_category_option_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (text) => window._martingale?.clickCategoryOption?.(text), msg.text);
      sendToPython(port, { action: 'click_category_option_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande la liste des ligues sur la page desktop "à venir" (classementeDeMatch)
    case 'scan_league_list': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'scan_league_list_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.scanLeagueList?.());
      sendToPython(port, { action: 'scan_league_list_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande le menu complet des compétitions (newclassementeDeMatch, classement complet)
    case 'scan_full_league_menu': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'scan_full_league_menu_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.scanFullLeagueMenu?.());
      sendToPython(port, { action: 'scan_full_league_menu_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande les matchs de la page de ligue desktop courante (classementeDeMatch)
    case 'scan_league_matches': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'scan_league_matches_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.scanLeagueMatches?.());
      sendToPython(port, { action: 'scan_league_matches_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande d'ouvrir le dropdown de catégorie + filtrer par recherche (AfficherParisMobile)
    case 'open_category_and_search': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'open_category_and_search_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.openCategoryAndSearch?.(args), msg);
      sendToPython(port, { action: 'open_category_and_search_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Sélectionne l'option du dropdown de catégorie une seule fois (sans rechercher)
    case 'select_category_option': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'select_category_option_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.selectCategoryOption?.(args.categorie_text), msg);
      sendToPython(port, { action: 'select_category_option_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Retape la recherche (key) sans re-cliquer le dropdown — pour le fallback de clés
    case 'search_market_key': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'search_market_key_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.searchMarketKey?.(args.key, args.categorie_text || null), msg);
      sendToPython(port, { action: 'search_market_key_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de lire l'indicateur "balle" (quel joueur a le point)
    case 'read_ball_indicator': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'read_ball_indicator_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, () => window._martingale?.readBallIndicator?.());
      sendToPython(port, { action: 'read_ball_indicator_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // Python demande de sélectionner un marché par texte déjà calculé (GetBetOld)
    case 'select_market_by_text': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'select_market_by_text_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (text) => window._martingale?.selectMarketByText?.(text), msg.text);
      sendToPython(port, { action: 'select_market_by_text_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    // DEBUG uniquement — liste tous les onglets 1xBet détectés + la correspondance port→onglet
    case 'debug_list_tabs': {
      const allTabs = await chrome.tabs.query({});
      const xbetTabs = allTabs.filter(t => t.url && (t.url.includes('1xbet') || t.url.includes('1x-bet')));
      const info = xbetTabs.map(t => ({ id: t.id, url: t.url, active: t.active, windowId: t.windowId }));
      const byPort = [...connections.entries()].map(([p, c]) => ({ port: p, connected: c.connected, tab_id: c.tabId }));
      sendToPython(port, {
        action: 'debug_list_tabs_response',
        req_id: msg.req_id,
        tabs: info,
        connections: byPort,
      });
      break;
    }

    // DEBUG uniquement — scanne les classNames contenant un des mots-clés donnés
    case 'debug_scan_classes': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'debug_scan_classes_response', req_id: msg.req_id, error: 'no_tab' }); break; }
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
      sendToPython(port, { action: 'debug_scan_classes_response', req_id: msg.req_id, result, tab_id: tabId });
      break;
    }

    // DEBUG uniquement — compte les éléments correspondant à un sélecteur CSS exact
    // (contrairement à debug_scan_classes qui dédoublonne par nom de classe).
    // Python demande une capture d'écran de l'onglet — utilisé pour le trace
    // forensique d'un pari en échec (Functions/Logs/BetTrace.py). Générique :
    // marche pour n'importe quelle connexion (1xBet comme Stake), pas besoin
    // d'un case dédié par bookmaker.
    case 'capture_screenshot': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'screenshot_response', req_id: msg.req_id, error: 'no_tab' }); break; }
      const image = await captureTabScreenshot(tabId);
      sendToPython(port, { action: 'screenshot_response', req_id: msg.req_id, image, tab_id: tabId });
      break;
    }

    case 'debug_count_selector': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'debug_count_selector_response', req_id: msg.req_id, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (selector) => {
        return {
          count: document.querySelectorAll(selector).length,
          scrollHeight: document.body.scrollHeight,
          innerHeight: window.innerHeight,
          scrollY: window.scrollY,
        };
      }, msg.selector);
      sendToPython(port, { action: 'debug_count_selector_response', req_id: msg.req_id, result, tab_id: tabId });
      break;
    }

    // ─── Stake.bet (Functions/Bookmakers/StakeBridge.py) ─────────────────────
    // Même logique que les actions 1xBet ci-dessus (resolveTabId + exec sur
    // window._martingale), juste un contenu de page différent (content_scripts/stake.js).

    case 'stake_get_state': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'stake_state_response', req_id: msg.req_id, error: 'no_tab' }); break; }
      const result = await activateThenExec(tabId, () => window._martingale?.getState?.() || null);
      sendToPython(port, { action: 'stake_state_response', req_id: msg.req_id, data: result, tab_id: tabId });
      break;
    }

    case 'stake_search_match': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'stake_search_match_response', req_id: msg.req_id, found: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (equipe1) => window._martingale?.searchMatch?.(equipe1), msg.equipe1);
      sendToPython(port, { action: 'stake_search_match_response', req_id: msg.req_id, ...(result || { found: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    case 'stake_get_odds': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'stake_odds_response', req_id: msg.req_id, found: false, error: 'no_tab' }); break; }
      const result = msg.dnb_team_idx
        ? await execInTab(tabId, (idx) => window._martingale?.getDnbOdds?.(idx), msg.dnb_team_idx)
        : await execInTab(tabId, (labels) => window._martingale?.getOddsByLabel?.(labels), msg.search_labels);
      sendToPython(port, { action: 'stake_odds_response', req_id: msg.req_id, ...(result || { found: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    case 'stake_place_bet': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'stake_place_bet_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.placeBet?.(args), {
        searchLabels: msg.search_labels, mise: msg.mise, dnbTeamIdx: msg.dnb_team_idx,
      });
      sendToPython(port, { action: 'stake_place_bet_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    case 'stake_place_sgm': {
      const tabId = await resolveTabId(msg, conn);
      if (!tabId) { sendToPython(port, { action: 'stake_place_sgm_response', req_id: msg.req_id, success: false, error: 'no_tab' }); break; }
      const result = await execInTab(tabId, (args) => window._martingale?.placeSameGameMulti?.(args), {
        combinedLegs: msg.combined_legs, mise: msg.mise,
      });
      sendToPython(port, { action: 'stake_place_sgm_response', req_id: msg.req_id, ...(result || { success: false, error: 'exec_failed' }), tab_id: tabId });
      break;
    }

    default:
      console.warn(`[WS:${port}] Action inconnue:`, msg.action);
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

// Résout l'onglet cible : STRICTEMENT le tab_id envoyé par Python (celui que
// cette connexion a ouvert via navigate), avec repli sur le tabId mémorisé côté
// extension si Python ne l'a pas renvoyé. Plus de "deviner l'onglet 1xBet actif"
// — c'est exactement ça qui faisait qu'un deuxième script pouvait piloter
// l'onglet d'un autre. Si on n'a vraiment aucun tab_id, c'est que navigate()
// n'a jamais été appelé pour cette connexion : erreur franche (no_tab) plutôt
// que deviner.
async function resolveTabId(msg, conn) {
  if (msg.tab_id) return msg.tab_id;
  if (conn?.tabId) return conn.tabId;
  console.warn('[resolveTabId] aucun tab_id pour cette connexion — navigate() a-t-il été appelé ?');
  return null;
}

// Attend que l'onglet ait fini de charger (status 'complete') après une navigation,
// avec un timeout de sécurité pour ne jamais bloquer indéfiniment le bridge.
function waitForTabLoad(tabId, timeoutMs = 15000) {
  return new Promise((resolve) => {
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      chrome.tabs.onUpdated.removeListener(listener);
      clearTimeout(timer);
      resolve();
    };
    const listener = (updatedTabId, changeInfo) => {
      // Le content script s'injecte en 'document_idle' (manifest.json), qui peut se
      // déclencher juste APRÈS que l'onglet passe à 'complete' — sans ce délai, un
      // scan lancé immédiatement après navigate_ack tombe en race condition
      // (window._martingale pas encore attaché → exec_failed).
      if (updatedTabId === tabId && changeInfo.status === 'complete') {
        setTimeout(finish, 400);
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
    const timer = setTimeout(finish, timeoutMs);
  });
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

// Certains éléments de la page (score, résultat) ne se mettent pas forcément à jour de
// façon fiable tant que l'onglet n'est pas au premier plan (confirmé en usage réel avec
// plusieurs onglets en arrière-plan). Pour les lectures critiques où une donnée périmée
// fausserait une décision de pari, on active brièvement l'onglet avant de lire, puis on
// restaure l'onglet qui était actif avant — au prix d'un peu de changement d'onglet
// visible si plusieurs scripts lisent en même temps.
async function activateThenExec(tabId, fn, args = null) {
  let previousActiveTabId = null;
  try {
    const tab = await chrome.tabs.get(tabId);
    if (!tab.active) {
      const [currentActive] = await chrome.tabs.query({ active: true, windowId: tab.windowId });
      previousActiveTabId = currentActive ? currentActive.id : null;
      await chrome.tabs.update(tabId, { active: true });
      // Laisser le temps à Chrome de "réveiller" l'onglet et au DOM de se rafraîchir
      await new Promise(r => setTimeout(r, 150));
    }
  } catch (e) {
    console.warn('[activateThenExec] activation échouée, lecture quand même:', e && e.message);
  }

  const result = await execInTab(tabId, fn, args);

  if (previousActiveTabId) {
    try {
      await chrome.tabs.update(previousActiveTabId, { active: true });
    } catch (e) {
      // L'onglet précédent a peut-être été fermé entre-temps — rien à faire
    }
  }

  return result;
}

// Capture un PNG (dataURL base64) de l'onglet donné, même s'il n'est pas actif
// (captureVisibleTab ne fonctionne que sur l'onglet ACTIF de sa fenêtre) —
// même pattern que activateThenExec : active brièvement, capture, restaure.
async function captureTabScreenshot(tabId) {
  let previousActiveTabId = null;
  let windowId = null;
  try {
    const tab = await chrome.tabs.get(tabId);
    windowId = tab.windowId;
    if (!tab.active) {
      const [currentActive] = await chrome.tabs.query({ active: true, windowId });
      previousActiveTabId = currentActive ? currentActive.id : null;
      await chrome.tabs.update(tabId, { active: true });
      await new Promise(r => setTimeout(r, 150));
    }
  } catch (e) {
    console.warn('[captureTabScreenshot] activation échouée:', e && e.message);
  }

  let image = null;
  try {
    image = await chrome.tabs.captureVisibleTab(windowId, { format: 'png' });
  } catch (e) {
    console.warn('[captureTabScreenshot] capture échouée:', e && e.message);
  }

  if (previousActiveTabId) {
    try {
      await chrome.tabs.update(previousActiveTabId, { active: true });
    } catch (e) {
      // onglet précédent fermé entre-temps — rien à faire
    }
  }

  return image;
}

// Retrouve quelle connexion (port) possède cet onglet — utilisé pour router les
// messages poussés par le content script (score_update, etc.) vers le bon process.
function portForTabId(tabId) {
  for (const [port, conn] of connections) {
    if (conn.tabId === tabId) return port;
  }
  return null;
}

// ─── Messages depuis content scripts / popup ─────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.action === 'get_ws_status') {
    const status = [...connections.entries()].map(([p, c]) => ({ port: p, connected: c.connected, tab_id: c.tabId }));
    sendResponse({ connected: status.some(s => s.connected), connections: status });
    return true;
  }
  if (!msg || !msg.action) return;

  const tabId = sender.tab?.id;
  const port = tabId != null ? portForTabId(tabId) : null;
  if (port == null) {
    // Onglet non rattaché à une connexion connue (ex: onglet 1xBet ouvert
    // manuellement par l'utilisateur, pas par un bot) — rien à transmettre.
    return;
  }

  const enriched = { ...msg, tab_id: tabId };
  sendToPython(port, enriched);
});

// ─── Init ─────────────────────────────────────────────────────────────────────

for (const port of WS_PORTS) connectWS(port);

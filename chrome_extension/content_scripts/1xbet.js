// Content Script 1xBet — injecté dans toutes les pages 1xBet
// Expose window._martingale avec toutes les actions DOM
// Pousse les changements de score automatiquement via MutationObserver

(function () {
  'use strict';

  // ─── Sélecteurs DOM 1xBet (mobile_site / new_site) ──────────────────────────

  const SEL = {
    // Score jeu en cours (ex: "30:15")
    score: {
      mobile: '.scoreboard-scores__item--team-1, .scoreboard-scores__item--team-2',
      new: '.c-scoreboard-score__point',     // à confirmer sur new_site
    },
    // Set actuel (numéro)
    set_heading: '.c-scoreboard-score__heading',
    // Jeu actuel (par set) — rows joueurs
    jeu_rows: '.c-scoreboard-player-score__row',
    jeu_cell: '.c-scoreboard-player-score__cell',
    // Betslip
    betslip_header: '.sb-betslip-header',
    betslip_delete: '.sb-betslip-item-v2__delete',
    betslip_input: '.sb-bet-slip-loader__input input',
    betslip_confirm: '.sb-place-bet',        // bouton "Placer le pari"
    betslip_cote: '.sb-betslip-item-v2__coef',
    betslip_result_win: '.c-bet-place__message--win, .bet-success, [class*="success"]',
    betslip_result_lose: '.c-bet-place__message--lose, [class*="lose"], [class*="lost"]',
    // Marché (onglets jeu en cours)
    market_tabs: '.c-tab-switcher-item, .period_select',
    market_bets: '.o-bet-box-list__item',
    market_bet_title: '.c-bet-box__market',
    market_bet_odd: '.c-bet-box__bet',
    // Joueurs
    player_names: '.c-scoreboard-player__name, .c-participant__name',
    // État jeu (en cours / terminé)
    game_active: '.scoreboard-scores, .c-scoreboard-score',
    game_timer: '.c-scoreboard-timer, .scoreboard-timer',
  };

  // ─── Utilitaires ──────────────────────────────────────────────────────────

  function qs(sel, root = document) { return root.querySelector(sel); }
  function qsa(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  async function waitFor(sel, timeout = 5000, root = document) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const el = qs(sel, root);
      if (el) return el;
      await sleep(100);
    }
    return null;
  }

  function readScore() {
    // mobile_site : deux éléments séparés
    const mob1 = qs('.scoreboard-scores__item--team-1');
    const mob2 = qs('.scoreboard-scores__item--team-2');
    if (mob1 && mob2) {
      const s = (mob1.textContent.trim() + ':' + mob2.textContent.trim()).toUpperCase();
      if (s !== ':') return s;
    }
    // new_site / old_site : points dans .c-scoreboard-score__point
    const pts = qsa('.c-scoreboard-score__point');
    if (pts.length >= 2) return (pts[0].textContent.trim() + ':' + pts[1].textContent.trim()).toUpperCase();
    return null;
  }

  function readSet() {
    const el = qs(SEL.set_heading);
    return el ? el.textContent.trim() : null;
  }

  function readJeu() {
    const rows = qsa(SEL.jeu_rows);
    if (rows.length < 2) return null;
    // set actuel = dernier set non vide (cellule index = set - 1)
    const cells1 = qsa(SEL.jeu_cell, rows[0]);
    const cells2 = qsa(SEL.jeu_cell, rows[1]);
    if (!cells1.length) return null;
    // La dernière cellule non-vide est le jeu actuel
    for (let i = cells1.length - 1; i >= 0; i--) {
      const t1 = cells1[i]?.textContent.trim();
      const t2 = cells2[i]?.textContent.trim();
      if (t1 !== '' && t1 !== undefined) return { jeu1: t1, jeu2: t2, col: i };
    }
    return null;
  }

  // ─── API exposée à service_worker via chrome.scripting.executeScript ────────

  window._martingale = {

    getState() {
      const score = readScore();
      const set = readSet();
      const jeu = readJeu();
      const players = window._martingale.getPlayers();
      return { score, set_actuel: set, jeu_actuel: jeu, players, url: location.href };
    },

    getPlayers() {
      const els = qsa(SEL.player_names);
      if (els.length >= 2) return { p1: els[0].textContent.trim(), p2: els[1].textContent.trim() };
      return { p1: null, p2: null };
    },

    async placeBet({ market, mise, tab_index }) {
      // 1) Sélectionner le bon onglet marché si nécessaire
      if (tab_index != null) {
        const tabs = qsa(SEL.market_tabs);
        if (tabs[tab_index]) tabs[tab_index].click();
        await sleep(500);
      }

      // 2) Trouver le bon item de pari par intitulé de marché
      const betItems = qsa(SEL.market_bets);
      let targetItem = null;
      for (const item of betItems) {
        const title = qs(SEL.market_bet_title, item)?.textContent?.trim() || '';
        if (market && title.toLowerCase().includes(market.toLowerCase())) {
          targetItem = item;
          break;
        }
      }

      if (!targetItem && betItems.length > 0) {
        targetItem = betItems[0]; // fallback : premier pari disponible
      }

      if (!targetItem) return { success: false, error: 'market_not_found', market };

      const oddEl = qs(SEL.market_bet_odd, targetItem);
      const cote = oddEl ? parseFloat(oddEl.textContent.replace(',', '.')) : null;
      targetItem.click();
      await sleep(800);

      // 3) Remplir la mise dans le betslip
      const input = await waitFor(SEL.betslip_input, 4000);
      if (!input) return { success: false, error: 'betslip_input_not_found' };

      input.focus();
      input.select();
      // Vider puis taper la mise
      const nativeInputSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeInputSetter.call(input, String(mise));
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(400);

      return { success: true, cote, market, mise };
    },

    async validateBet({ confirm = true } = {}) {
      if (!confirm) return { validated: false };
      const btn = await waitFor(SEL.betslip_confirm, 3000);
      if (!btn) return { validated: false, error: 'confirm_button_not_found' };
      btn.click();
      await sleep(1000);
      // Vérifier résultat
      const win = qs(SEL.betslip_result_win);
      const lose = qs(SEL.betslip_result_lose);
      return { validated: true, accepted: !!win || !lose };
    },

    async deleteBet() {
      const delBtns = qsa(SEL.betslip_delete);
      for (const btn of delBtns) { btn.click(); await sleep(200); }
      return { deleted: delBtns.length };
    },

    getResult() {
      const win = qs(SEL.betslip_result_win);
      const lose = qs(SEL.betslip_result_lose);
      if (win) return { result: 'WIN' };
      if (lose) return { result: 'LOSE' };
      return { result: null };
    },

    async getMatchList() {
      // Attendre que les blocs de ligue apparaissent (site lent — jusqu'à 15s)
      const firstChamp = await waitFor('.dashboard-champ, .dashboard-champ-content', 15000);
      if (!firstChamp) return null;
      // Petit délai pour laisser les scores se charger
      await sleep(800);

      // Retourne [{leagueName, matches:[{p1,p2,score,url,hasBall}]}]
      const champEls = qsa('.dashboard-champ, .dashboard-champ-content');
      if (!champEls.length) return null;

      const leagues = [];
      for (const champ of champEls) {
        const nameEl = champ.querySelector('.dashboard-champ-name__label--is-link, .c-events__liga');
        const leagueName = nameEl ? nameEl.textContent.trim().toLowerCase() : '';
        const matchEls = champ.querySelectorAll('.dashboard-game-block, .c-events-scoreboard__item');
        const matches = [];
        for (const matchEl of matchEls) {
          const teamsEl = matchEl.querySelector('.ui-team-scores__teams, .c-events__teams');
          const teams = teamsEl ? teamsEl.textContent.trim().split('\n').map(t => t.trim()).filter(Boolean) : [];
          const p1 = teams[0] || null;
          const p2 = teams[1] || null;

          // Score jeu courant — debug : affiche toutes les classes/valeurs
          const scoreItems = matchEl.querySelectorAll('.ui-game-scores__item, .c-events-scoreboard__score');
          const _dbg = Array.from(scoreItems).map(el => ({ cls: el.className, val: el.textContent.trim() }));
          if (_dbg.length) console.log('[getMatchList] score items:', JSON.stringify(_dbg));

          let score = null;
          const active = matchEl.querySelectorAll('.ui-game-scores__item--current, .ui-game-scores__item--active, .ui-game-scores__item--inning');
          if (active.length >= 2) {
            score = active[0].textContent.trim() + ':' + active[1].textContent.trim();
          } else if (scoreItems.length >= 2) {
            const vals = Array.from(scoreItems).map(el => el.textContent.trim());
            score = vals[vals.length - 2] + ':' + vals[vals.length - 1];
          }

          const linkEl = matchEl.querySelector('.dashboard-game-block__link, .c-events__name');
          const url = linkEl ? linkEl.href : null;
          const hasBall = matchEl.querySelectorAll('.ui-game-scores__item--inning, .c-events-scoreboard__icon').length > 0;
          if (url) matches.push({ p1, p2, score, url, hasBall });
        }
        leagues.push({ leagueName, matches });
      }
      return leagues;
    },
  };

  // ─── MutationObserver score — push automatique ───────────────────────────

  let lastScore = null;
  let lastJeu = null;

  function pushScoreIfChanged() {
    const score = readScore();
    if (!score) return;
    if (score !== lastScore) {
      lastScore = score;
      chrome.runtime.sendMessage({ action: 'score_update', score, url: location.href });
    }
    const jeu = readJeu();
    if (jeu && JSON.stringify(jeu) !== JSON.stringify(lastJeu)) {
      lastJeu = jeu;
      chrome.runtime.sendMessage({ action: 'game_update', jeu, set_actuel: readSet(), url: location.href });
    }
  }

  const observer = new MutationObserver(pushScoreIfChanged);
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });

  // Lecture initiale
  setTimeout(pushScoreIfChanged, 1000);

  console.log('[Martingale] Content script 1xBet chargé');
})();

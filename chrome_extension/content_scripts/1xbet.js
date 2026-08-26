// Content Script 1xBet — injecté dans toutes les pages 1xBet
// Expose window._martingale avec toutes les actions DOM
// Pousse les changements de score automatiquement via MutationObserver

(function () {
  'use strict';
  console.log('[1xBet] Début script');
  try {

  // ─── Sélecteurs DOM 1xBet (mobile_site / new_site) ──────────────────────────

  const SEL = {
    // Score jeu en cours (ex: "30:15")
    score: {
      mobile: '.scoreboard-scores__item--team-1, .scoreboard-scores__item--team-2',
      new: '.c-scoreboard-score__point',     // à confirmer sur new_site
    },
    // Set actuel (numéro) — port de GetSetActuel.py (config.classes['set_container']['mobile_site'])
    set_heading: '.scoreboard-timer, .c-scoreboard-score__heading',
    // Jeu actuel (par set) — rows joueurs
    jeu_rows: '.c-scoreboard-player-score__row',
    jeu_cell: '.c-scoreboard-player-score__cell',
    // Betslip (coupon rapide mobile_site — vérifié en conditions réelles le 2026-08-25)
    betslip_header: '.quick-coupon-header, .sb-betslip-header',
    betslip_delete: '.quick-coupon-events-card__remove, .sb-betslip-item-v2__delete',
    betslip_input: '.ui-number-input__field, .sb-bet-slip-loader__input input',
    betslip_confirm: '.quick-coupon-put-bet-button, .sb-place-bet',
    betslip_cote: '.quick-coupon-events-card-coefs__new, .sb-betslip-item-v2__coef',
    betslip_result_win: '.ui-notification-alert--status-success, .c-bet-place__message--win',
    betslip_result_lose: '.ui-notification-alert--status-error, .c-bet-place__message--lose',
    // Marché (onglets jeu en cours)
    market_tabs: '.c-tab-switcher-item, .period_select',
    market_bets: '.o-bet-box-list__item',
    market_bet_title: '.c-bet-box__market',
    market_bet_odd: '.c-bet-box__bet',
    // Joueurs
    player_names: '.scoreboard-intro__team, .c-scoreboard-player__name, .c-participant__name',
    // État jeu (en cours / terminé)
    game_active: '.scoreboard-scores, .c-scoreboard-score',
    game_timer: '.c-scoreboard-timer, .scoreboard-timer',
  };

  // ─── Utilitaires ──────────────────────────────────────────────────────────

  function qs(sel, root = document) { return root.querySelector(sel); }
  function qsa(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // Identité de match tolérante : l'URL live 1xBet change parfois d'elle-même (l'ID
  // numérique d'événement se renouvelle en cours de match) sans changer de match réel.
  // On compare le slug (noms d'équipes) plutôt que l'URL exacte pour détecter une vraie
  // navigation involontaire (incident du 2026-08-25) sans faux positif sur ce cas normal.
  function matchSlug(url) {
    try {
      const last = url.split('?')[0].split('/').filter(Boolean).pop() || '';
      return last.replace(/^\d+-/, '');
    } catch (e) {
      return url;
    }
  }

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
    if (!el) return null;
    // Port de GetSetActuel.py : premier "mot" du texte ("1er set" / "2ème set"), on ne
    // garde que les chiffres pour obtenir un set_actuel numérique propre.
    const firstWord = el.textContent.trim().split(' ')[0] || '';
    const digits = firstWord.replace(/[^0-9]/g, '');
    return digits || null;
  }

  function readJeu() {
    // Port de GetJeuActuel.py (mobile_site) : config.classes['jeu_container'] renvoie
    // PLUSIEURS colonnes .scoreboard-periods-column__body — l'index 0 est la colonne des
    // libellés joueurs ("Et1"/"Et2"), l'index N (N = numéro du set) est la colonne des
    // scores de jeu de ce set, avec 2 cellules .scoreboard-periods-column__td (joueur 1/2).
    const bodies = qsa('.scoreboard-periods-column__body');
    const setNum = parseInt(readSet() || '1', 10);
    const target = bodies[setNum];
    if (!target) return null;
    const cells = qsa('.scoreboard-periods-column__td', target);
    if (cells.length < 2) return null;
    const j1 = parseInt(cells[0].textContent.trim(), 10);
    const j2 = parseInt(cells[1].textContent.trim(), 10);
    if (Number.isNaN(j1) || Number.isNaN(j2)) return null;
    return { jeu1: j1, jeu2: j2, col: setNum };
  }

  // ─── API exposée à service_worker via chrome.scripting.executeScript ────────

  window._martingale = {

    async getState() {
      // Le scoreboard de la page (SPA) se démonte/remonte parfois brièvement lors des
      // rafraîchissements internes 1xBet (changement d'ID d'événement pour le même
      // match) — on tolère ça avec quelques ré-essais courts avant de renvoyer vide,
      // plutôt qu'un faux négatif immédiat (observé en conditions réelles le 2026-08-25).
      const SCORE_SEL = '.scoreboard-status, .scoreboard-scores, .c-scoreboard-score__period, .c-scoreboard-score, .c-scoreboard-score__heading';

      let scoreDiv = null;
      let score = null, set = null, jeu = null;
      for (let attempt = 0; attempt < 4; attempt++) {
        scoreDiv = document.querySelector(SCORE_SEL);
        if (!scoreDiv) {
          try {
            const iframe = document.querySelector('iframe');
            if (iframe && iframe.contentDocument) {
              scoreDiv = iframe.contentDocument.querySelector(SCORE_SEL);
            }
          } catch (e) {
            // silence
          }
        }
        score = readScore();
        set = readSet();
        jeu = readJeu();
        if (scoreDiv && score) break;
        await sleep(400);
      }

      const players = window._martingale.getPlayers();
      const isMatchPage = !!scoreDiv;
      console.log('[getState] isMatchPage:', isMatchPage);
      return { score, set_actuel: set, jeu_actuel: jeu, players, url: location.href, isMatchPage };
    },

    getPlayers() {
      // Port de GetPlayersName.py : retire le suffixe entre parenthèses (seed/pays), ex. "Nom (3)".
      const clean = (s) => (s || '').split('(')[0].trim();
      const els = qsa(SEL.player_names);
      if (els.length >= 2) return { p1: clean(els[0].textContent), p2: clean(els[1].textContent) };
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

    // Port de PlacerMise (Functions/PlacerMise.py) : l'input de mise est cherché DANS le
    // wrapper cpn_amount (quick-coupon-bet-amount__steps), pas globalement sur la page.
    async setStake(mise) {
      const wrapper = await waitFor('.quick-coupon-bet-amount__steps', 5000);
      const input = wrapper ? qs('.ui-number-input__field', wrapper) : await waitFor(SEL.betslip_input, 5000);
      if (!input) return { success: false, error: 'betslip_input_not_found' };

      input.focus();
      input.select();
      const nativeInputSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeInputSetter.call(input, String(mise));
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(400);

      // Vérification (comme ValidationDuParis.py) : si la valeur n'a pas pris, retenter une fois.
      if (input.value !== String(mise)) {
        nativeInputSetter.call(input, String(mise));
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        await sleep(400);
      }

      return { success: input.value === String(mise), mise };
    },

    async validateBet({ confirm = true } = {}) {
      if (!confirm) return { validated: false };
      const btn = await waitFor(SEL.betslip_confirm, 3000);
      if (!btn) return { validated: false, error: 'confirm_button_not_found' };
      btn.click();
      await sleep(1500);

      // Notification de succès (le texte contient "effectué" sur mobile_site)
      let notif = await waitFor('.ui-notification-alert--status-success', 4000);
      if (notif) {
        const text = (notif.textContent || '').trim();
        const accepted = /effectu/i.test(text);
        const closeBtn = qs('.ui-notification-base__close', notif) || qs('.ui-notification-base__close');
        if (closeBtn) closeBtn.click();
        return { validated: true, accepted, message: text };
      }

      // Notification d'erreur ou question (cote modifiée, mise max, pari déjà placé, etc.)
      notif = qs('.ui-notification-alert--status-error, .ui-notification-alert--status-question');
      if (notif) {
        const text = (notif.textContent || '').trim();
        const alreadyPlaced = /déjà|peut être accepté/i.test(text);
        const closeBtn = qs('.ui-notification-base__close', notif) || qs('.ui-notification-base__close');
        if (closeBtn) closeBtn.click();
        return { validated: true, accepted: alreadyPlaced, message: text };
      }

      // Fallback : sélecteurs génériques (autres site_type)
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

    // ATTENTION (2026-08-26) : cliquer sur le bouton de recherche NAVIGUE vers une page
    // dédiée /search-events (ce n'est plus une modal en overlay) — cette navigation détruit
    // le contexte JS en cours d'exécution. On sépare donc en deux actions distinctes :
    // clickSearchButton() (retourne aussitôt après le clic) puis, une fois le content script
    // réinjecté sur la nouvelle page, searchOnResultsPage() (tape le texte, lit les résultats).
    async clickSearchButton() {
      const searchBtn = await waitFor('.home-navigation__link--search', 20000);
      if (!searchBtn) return { success: false, error: 'search_button_not_found' };
      searchBtn.click();
      return { success: true };
    },

    async searchOnResultsPage({ equipe1, equipe2 }) {
      const modalContent = await waitFor('.search-app__content', 15000);
      if (!modalContent) return { found: false, error: 'search_modal_not_found' };

      const inputSelectors = [
        '.games-search-modal__input', 'input.ui-field__input', 'input.ui-search-default',
        'input.search-app-head__search', 'input.ui-field__input.search-app-head__search',
      ];
      let input = null;
      for (const sel of inputSelectors) {
        input = qs(sel, modalContent);
        if (input) break;
      }
      if (!input) return { found: false, error: 'search_input_not_found' };

      const term = `${equipe1} - ${equipe2}`;
      const nativeInputSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeInputSetter.call(input, term);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));

      const cardsFound = await waitFor('.ui-game-card__content', 15000);
      if (!cardsFound) return { found: false, error: 'no_search_results' };
      await sleep(1500);

      const matches = qsa('.search-game-card');
      const candidates = [];
      const norm = (s) => (s || '').toLowerCase().trim();
      const loose = (a, b) => norm(a).includes(norm(b)) || norm(b).includes(norm(a));

      for (const m of matches) {
        let team1 = null, team2 = null, link = null;
        const teamNames = qsa('.ui-game-card-scoreboard-teams-name__caption', m);
        if (teamNames.length >= 2) {
          team1 = teamNames[0].textContent.trim();
          team2 = teamNames[1].textContent.trim();
        } else {
          const scoreboard = qs('.ui-game-card-scoreboard', m);
          const teamsText = scoreboard ? scoreboard.textContent : '';
          if (teamsText.includes(' - ')) {
            [team1, team2] = teamsText.split(' - ').map(s => s.trim());
          }
        }
        const a = m.querySelector('a');
        link = a ? a.href : null;
        if (!team1 || !team2 || !link) continue;

        if (loose(team1, equipe1) && loose(team2, equipe2)) {
          return { found: true, url: link, team1, team2 };
        }
        candidates.push({ team1, team2, url: link });
      }

      return { found: false, candidates };
    },

    // Port de GetBetOld (Functions/GetBetOld.py, branche non-allScriptType/mobile_site) :
    // cherche le bouton de marché par .ui-market__name, clique, vérifie l'ajout au coupon rapide
    // (.quick-coupon-events-card) et retire+réessaie si le mauvais pari a été ajouté.
    // Validé en conditions réelles le 2026-08-25 (paris simples).
    //
    // Récupération auto (retour utilisateur 2026-08-25) : il arrive que 1xBet n'affiche plus
    // aucun marché (bug côté site) — le correctif connu est de changer d'onglet de catégorie
    // puis de revenir sur "Temps réglementaire" pour forcer le rechargement. Fait une fois si
    // aucun bouton de marché n'est trouvé du tout avant d'abandonner.
    async selectMarketByText(selection, _retried = false) {
      // Ouvrir les groupes de marchés fermés — Selenium peut cliquer un élément du DOM
      // même replié dans certains cas ; on le rend explicitement visible pour un clic JS fiable.
      for (let round = 0; round < 3; round++) {
        const headers = qsa('.game-markets-group-header');
        let clicked = 0;
        for (const h of headers) {
          if (!h.className.includes('is-opened')) { h.click(); clicked++; await sleep(150); }
        }
        if (clicked === 0) break;
        await sleep(400);
      }

      const norm = (s) => (s || '').toLowerCase().trim();
      const betButtons = qsa('.game-markets-group__market');

      if (betButtons.length === 0 && !_retried) {
        const recovered = await window._martingale._reloadMarketsViaCategoryToggle();
        if (recovered) return window._martingale.selectMarketByText(selection, true);
      }

      const candidates = [];
      for (const btn of betButtons) {
        if (btn.className.includes('locked') || btn.disabled) continue;
        const nameEl = qs('.ui-market__name', btn);
        const name = nameEl ? nameEl.textContent.trim() : '';
        if (!name) continue;
        if (!norm(name).includes(norm(selection))) { candidates.push(name); continue; }

        btn.click();
        await sleep(800);

        const card = await waitFor('.quick-coupon-events-card', 3000);
        const cardText = card ? card.textContent.toLowerCase() : '';
        if (!cardText.includes(norm(selection))) {
          const removeBtn = card && qs('.quick-coupon-events-card__remove', card);
          if (removeBtn) { removeBtn.click(); await sleep(300); }
          candidates.push(name);
          continue;
        }

        const oddEl = qs('.ui-market__value', btn);
        const cote = oddEl ? parseFloat(oddEl.textContent.replace(',', '.')) : null;
        return { success: true, cote };
      }

      if (candidates.length === 0 && !_retried) {
        const recovered = await window._martingale._reloadMarketsViaCategoryToggle();
        if (recovered) return window._martingale.selectMarketByText(selection, true);
      }

      return { success: false, error: 'selection_not_found', candidates };
    },

    // Clique un autre onglet de catégorie puis revient sur "Temps réglementaire" pour
    // forcer 1xBet à recharger la liste des marchés (correctif observé manuellement).
    async _reloadMarketsViaCategoryToggle() {
      const listWrapper = await waitFor('.game-sub-games__list', 3000);
      if (!listWrapper) return false;
      const options = qsa('.game-sub-games__item', listWrapper);
      const current = options.find(o => o.className.includes('is-selected'));
      const other = options.find(o => o !== current);
      const target = options.find(o => /temps r.glementaire/i.test(o.textContent));
      if (!other || !target) return false;

      other.click();
      await sleep(600);
      target.click();
      await sleep(800);
      return true;
    },

    // Alias conservé pour compat (PlacerPari/OneXBetBridge) : ignore categorie/type_de_pari,
    // ce flux (paris tipster) ne passe pas par le dropdown AfficherParisMobile.
    async selectMarket({ categorie, type_de_pari, selection }) {
      return window._martingale.selectMarketByText(selection);
    },

    // Port de la lecture "balle" de GetBetOld.py (branche allScriptType, mobile_site) :
    // scoreboard_player_score → ball_container → score_ball. Retourne un booléen équivalent
    // à `len(first_player) > 0` côté Selenium — la décision (win_type, sType) reste en Python.
    readBallIndicator() {
      const players = qsa('.scoreboard-periods-column__body');
      if (!players.length) return { success: false, error: 'scoreboard_player_score_not_found' };
      const container = qs('.scoreboard-periods-column__td--has-inning', players[0]);
      if (!container) return { success: false, error: 'ball_container_not_found' };
      const balls = qsa('.scoreboard-periods__inning', container);
      return { success: true, hasBall: balls.length > 0 };
    },

    // DEBUG uniquement — liste les options de la barre de catégories déjà visible
    // (game-sub-games__list), sans cliquer aucune.
    async debugListCategoryOptions() {
      const listWrapper = await waitFor('.game-sub-games__list', 5000);
      const options = listWrapper ? qsa('.game-sub-games__item', listWrapper).map(o => o.textContent.trim()) : [];
      return { success: true, options };
    },

    // Port de RetourTpsRegMobile (Functions/retour_section_tps_reglementaire.py) : clique
    // l'option déjà visible dans la barre de catégories (game-sub-games__list) — sur
    // mobile_site cette liste est affichée directement, ce n'est pas un dropdown à ouvrir.
    async clickCategoryOption(text) {
      const urlBefore = location.href;
      const listWrapper = await waitFor('.game-sub-games__list', 5000);
      if (!listWrapper) return { success: false, error: 'category_list_not_found' };
      const norm = (s) => (s || '').toLowerCase().trim();
      const options = qsa('.game-sub-games__item', listWrapper);
      for (const opt of options) {
        if (norm(opt.textContent) === norm(text)) {
          opt.click();
          await sleep(400);
          if (matchSlug(location.href) !== matchSlug(urlBefore)) return { success: false, error: 'unexpected_navigation' };
          return { success: true };
        }
      }
      return { success: false, error: 'category_option_not_found' };
    },

    // Port de AfficherParisMobile (Functions/AfficherParis.py, branche allScriptType) :
    // clique la catégorie déjà visible dans la barre game-sub-games__list, puis filtre par
    // `key` via la recherche de marché (game-search*). categorie_text et key sont déjà
    // calculés par le code Python (theset/args/key) — ici on ne fait QUE le geste DOM.
    //
    // Garde de sécurité (incident du 2026-08-25 : un clic ambigu a navigué vers un autre match) :
    // on vérifie l'URL avant/après chaque clic et on annule si elle change de façon inattendue.
    async openCategoryAndSearch({ categorie_text, key }) {
      const urlBefore = location.href;

      const listWrapper = await waitFor('.game-sub-games__list', 5000);
      if (!listWrapper) return { success: false, error: 'category_list_not_found' };

      const norm = (s) => (s || '').toLowerCase().trim();
      const options = qsa('.game-sub-games__item', listWrapper);
      let matched = null;
      for (const opt of options) {
        if (norm(opt.textContent) === norm(categorie_text)) { matched = opt; break; }
      }
      if (!matched) return { success: false, error: 'category_option_not_found', categorie_text };

      matched.click();
      await sleep(500);
      if (matchSlug(location.href) !== matchSlug(urlBefore)) return { success: false, error: 'unexpected_navigation', step: 'category_option' };

      const toolbar = qs('.game-search');
      const searchInput = toolbar ? qs('input.game-search__input', toolbar) : qs('input.game-search__input');
      if (!searchInput) return { success: false, error: 'search_input_not_found' };

      const nativeInputSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeInputSetter.call(searchInput, '');
      searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      nativeInputSetter.call(searchInput, key);
      searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      searchInput.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(600);
      if (matchSlug(location.href) !== matchSlug(urlBefore)) return { success: false, error: 'unexpected_navigation', step: 'search_input' };

      const container = await waitFor('.game-markets-content', 2000);
      if (!container) return { success: false, error: 'bet_list_container_not_found', key };

      return { success: true };
    },

    async selectCombinedMarkets(legs) {
      const constructorBtn = await waitFor('.ico--constructor-bet', 20000);
      if (!constructorBtn) return { success: false, error: 'constructor_bet_not_found' };
      constructorBtn.click();
      await sleep(1500);

      const results = [];
      for (const leg of legs) {
        const r = await window._martingale.selectMarket(leg);
        results.push(r);
        if (!r.success) return { success: false, error: 'leg_failed', leg, results };
        await sleep(1000);
      }

      const redirectBtn = await waitFor('.quick-coupon-header__redirect', 20000);
      if (!redirectBtn) return { success: false, error: 'combo_redirect_not_found', results };
      redirectBtn.click();
      await sleep(1000);

      return { success: true, results };
    },

    // Port de PlacerCode (Functions/PlacerCode.py) — classes tirées de conf/classes.py
    // (coupon_loader_toggle='coupon-loader-toggle', coupon_loader_input='coupon-loader__input').
    async loadCouponCode(code) {
      const toggle = await waitFor('.coupon-loader-toggle', 10000);
      if (!toggle) return { success: false, error: 'coupon_toggle_not_found' };
      const inputBefore = qs('.coupon-loader__input input, input.coupon-loader__input');
      if (!inputBefore || !inputBefore.offsetParent) {
        toggle.click();
        await sleep(600);
      }

      const input = await waitFor('.coupon-loader__input input, input.coupon-loader__input', 8000);
      if (!input) return { success: false, error: 'coupon_input_not_found' };

      const nativeInputSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeInputSetter.call(input, String(code));
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(500);

      const boxes = qsa('.coupon-loader__box');
      let chargerBtn = null;
      for (const box of boxes) {
        for (const btn of qsa('button', box)) {
          if (btn.textContent.trim().toLowerCase().includes('charger')) { chargerBtn = btn; break; }
        }
        if (chargerBtn) break;
      }
      if (!chargerBtn) return { success: false, error: 'charger_button_not_found' };

      chargerBtn.removeAttribute('disabled');
      chargerBtn.classList.remove('ui-button--is-disabled');
      chargerBtn.click();
      await sleep(1500);

      return { success: true };
    },

    // Port de classementeDeMatch (Functions/ScriptRechercheDeMatch.py, page desktop
    // "line"/à venir, site_type='new_site') — étape 1 : liste des ligues visibles sur la
    // page d'accueil des paris à venir. Classes desktop (conf/classes.py) :
    // dashboard_champ='dashboard-champ', dashboard_champ_name='dashboard-champ-name__label--is-link'.
    async scanLeagueList() {
      console.log('[scanLeagueList] début');
      let champEls = [];
      for (let i = 0; i < 20; i++) {
        champEls = qsa('.dashboard-champ');
        console.log(`[scanLeagueList] tentative ${i}: ${champEls.length} .dashboard-champ`);
        if (champEls.length) break;
        await sleep(500);
      }

      const leagues = [];
      for (const champ of champEls) {
        const nameEl = qs('.dashboard-champ-name__label--is-link', champ);
        if (!nameEl) continue;
        const name = nameEl.textContent.trim();
        const href = nameEl.href || nameEl.getAttribute('href');
        if (name && href) leagues.push({ name, href });
      }
      console.log('[scanLeagueList] fin, leagues:', leagues.length);
      return { success: true, leagues };
    },

    // Étape 2 : matchs d'une page de ligue (desktop). Classes desktop (conf/classes.py) :
    // dashboard_champ_body_games='dashboard-champ-body__games', dashboard_game_block_row=
    // 'dashboard-game-block', team_wrap='dashboard-game-block__teams', team_name=
    // 'dashboard-game-team-info', match_link='dashboard-game-block__link', events_time=
    // 'dashboard-game-block__info' (contenant lui-même .dashboard-game-info__date/__time).
    async scanLeagueMatches() {
      const gamesContainer = await waitFor('.dashboard-champ-body__games', 8000);
      if (!gamesContainer) return { success: true, matches: [] };
      await sleep(500);

      const rows = qsa('.dashboard-game-block');
      const matches = [];
      for (const row of rows) {
        try {
          const teamWrap = qs('.dashboard-game-block__teams', row);
          const playerEls = teamWrap ? qsa('.dashboard-game-team-info', teamWrap) : [];
          const players = playerEls.map(p => p.textContent.split('(')[0].trim()).filter(Boolean);
          if (players.length < 2) continue;

          const linkEl = qs('.dashboard-game-block__link', row);
          const href = linkEl ? (linkEl.href || linkEl.getAttribute('href')) : null;
          if (!href) continue;

          const infoEl = qs('.dashboard-game-block__info', row);
          const dateEl = infoEl ? qs('.dashboard-game-info__date', infoEl) : null;
          const timeEl = infoEl ? qs('.dashboard-game-info__time', infoEl) : null;
          const dateText = dateEl ? dateEl.textContent.trim() : '';
          const timeText = timeEl ? timeEl.textContent.trim() : '';

          matches.push({ players, href, date: dateText, time: timeText });
        } catch (e) {
          continue;
        }
      }
      return { success: true, matches };
    },

    async getMatchList() {
      // Attendre que les blocs de ligue apparaissent (site lent après navigation fraîche,
      // beaucoup de données à charger — jusqu'à 25s observés en conditions réelles).
      const firstChamp = await waitFor('.dashboard-champ, .dashboard-champ-content', 25000);
      if (!firstChamp) return null;
      // Petit délai pour laisser les scores se charger
      await sleep(1200);

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
          // Noms des joueurs : scopés à .dashboard-game-team-info__name (le conteneur
          // .dashboard-game-block__teams mélange noms ET score dans son textContent brut).
          const teamsWrap = matchEl.querySelector('.dashboard-game-block__teams, .ui-team-scores__teams, .c-events__teams');
          const nameEls = teamsWrap ? qsa('.dashboard-game-team-info__name', teamsWrap) : [];
          const clean = (s) => (s || '').split('(')[0].trim();
          let p1 = nameEls[0] ? clean(nameEls[0].textContent) : null;
          let p2 = nameEls[1] ? clean(nameEls[1].textContent) : null;
          if (!p1 && teamsWrap) {
            // Fallback ancien layout (mobile/old_site) : noms séparés par retour à la ligne
            const teams = teamsWrap.textContent.trim().split('\n').map(t => t.trim()).filter(Boolean);
            p1 = teams[0] || null;
            p2 = teams[1] || null;
          }

          // Score du jeu en cours : élément .ui-game-scores__item--sub, texte "(X) (Y)".
          let score = null;
          const subEl = matchEl.querySelector('.ui-game-scores__item--sub');
          if (subEl) {
            const nums = (subEl.textContent.match(/\(([^)]*)\)/g) || []).map(s => s.replace(/[()]/g, '').trim());
            if (nums.length >= 2) score = `${nums[0]}:${nums[1]}`;
          }

          // Score brut complet (jeux + points), même conteneur et même format que
          // l'ancien Selenium (bet_item.find_elements(By.CLASS_NAME, 'ui-game-scores').text,
          // comparé tel quel à config.score_to_start, ex: "00(0)00(0)") — indispensable
          // pour vérifier que le match est bien au tout début d'un set (jeux 0-0), pas
          // seulement que le point en cours est dans les tout premiers.
          let rawScore = null;
          const gameScoresEl = matchEl.querySelector('.ui-game-scores') || (subEl ? subEl.closest('[class*="game-scores"]') : null);
          if (gameScoresEl) {
            rawScore = gameScoresEl.textContent.replace(/\s+/g, '');
          }
          const linkEl = matchEl.querySelector('.dashboard-game-block__link, .c-events__name');
          const url = linkEl ? linkEl.href : null;
          const hasBall = qsa('.ui-game-scores__item--inning', matchEl).length > 0;
          if (url) matches.push({ p1, p2, score, rawScore, url, hasBall });
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

  // Injecter aussi dans l'iframe si elle existe (retry toutes les 500ms pendant 5s)
  function injectIntoIframe() {
    try {
      const iframe = document.querySelector('iframe');
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow._martingale = window._martingale;
        console.log('[1xBet] API injectée dans iframe ✓');
        return true;
      }
    } catch (e) {
      // silence on cross-origin errors
    }
    return false;
  }

  let attempts = 0;
  const iframeInterval = setInterval(() => {
    if (injectIntoIframe() || ++attempts > 10) {
      clearInterval(iframeInterval);
    }
  }, 500);

  console.log('[1xBet] window._martingale créé ✓');
  } catch (e) {
    console.error('[1xBet] ERREUR:', e);
  }
})();

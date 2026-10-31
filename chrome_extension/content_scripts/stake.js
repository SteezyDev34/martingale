// Content script Stake.bet — porte en JS pur (DOM direct, plus de Selenium) la
// logique de Functions/Bookmakers/StakeScraper.py. Les décisions "intelligentes"
// (résolution IA du bon match/bouton, labels via BetLabelsDB) restent côté Python ;
// ce script ne fait que des opérations DOM "bêtes" : chercher, cliquer, lire, taper.

(function () {
  try {
    if (window._martingale && window._martingale.__site === 'stake') return;

    function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

    function firstVisible(selectors) {
      for (const sel of selectors) {
        const els = Array.from(document.querySelectorAll(sel));
        for (const el of els) {
          if (el.offsetParent !== null) return el;
        }
      }
      return null;
    }

    function dispatchClick(el) {
      el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }

    // ─── État / session ──────────────────────────────────────────────────────

    const SEL_SESSION = [
      "[class*='userBalance']", "[class*='user-balance']",
      "[data-test='balance']", "[class*='HeaderUser']",
      "[class*='walletBalance']", "[class*='wallet-balance']",
      "button[class*='wallet']",
    ];

    function getState() {
      let loggedIn = false;
      for (const sel of SEL_SESSION) {
        const els = Array.from(document.querySelectorAll(sel));
        if (els.some((el) => (el.textContent || '').trim())) { loggedIn = true; break; }
      }
      if (!loggedIn) {
        const btns = Array.from(document.querySelectorAll('button'));
        loggedIn = !btns.some((b) => (b.textContent || '').toLowerCase().includes('connecter'));
      }
      return { loggedIn, url: location.href };
    }

    // ─── Recherche de match ──────────────────────────────────────────────────
    // Retourne la liste des candidats {text, url} — Python choisit (exact match
    // ou résolution IA) puis renavigue directement via bridge.navigate(url).

    async function searchMatch(equipe1) {
      const SEARCH_INPUT_SELS = [
        'input.game-search__input',
        '[class*="game-search__input"]',
        'input[placeholder*="Rechercher sur Stake"]',
        'input[placeholder*="Search"]',
      ];
      const findInput = () => firstVisible(SEARCH_INPUT_SELS);

      await sleep(500);
      let input = findInput();

      if (!input) {
        for (const sel of ['[data-testid="top-search"]', 'button[data-testid*="search"]',
          '[class*="search-icon"]', '[class*="game-search"]']) {
          const btns = Array.from(document.querySelectorAll(sel));
          for (const btn of btns) {
            dispatchClick(btn);
            await sleep(400);
            input = findInput();
            if (input) break;
          }
          if (input) break;
        }
      }

      // Refonte UI Stake constatée le 2026-10-28 : les sélecteurs data-testid/class
      // ci-dessus ne matchent plus rien (0 résultat vérifié en DOM), le bouton loupe
      // réel n'a ni testid ni class reconnaissable -- seulement aria-label="Rechercher"
      // (ou "Search" en UI anglaise). Pas pris par le fallback générique ci-dessous, qui
      // ignore explicitement tout bouton portant un aria-label.
      if (!input) {
        const byAria = Array.from(document.querySelectorAll('button[aria-label]')).find((b) => {
          const a = (b.getAttribute('aria-label') || '').toLowerCase();
          return a.includes('recherch') || a.includes('search');
        });
        if (byAria) {
          dispatchClick(byAria);
          await sleep(400);
          input = findInput();
        }
      }

      if (!input) {
        const SKIP_TESTID = new Set(['coin-toggle', 'wallet', 'user-dropdown-toggle', 'left-sidebar-close']);
        const SKIP_ARIA = new Set(['Toggle Notifications Widget', 'Open Dropdown', 'Toggle Sidebar']);
        const all = Array.from(document.querySelectorAll('button'));
        for (const b of all) {
          const r = b.getBoundingClientRect();
          if (r.x <= 0 || r.y < 0 || r.y > 80 || r.width <= 0) continue;
          const tid = b.getAttribute('data-testid') || '';
          const aria = b.getAttribute('aria-label') || '';
          if (SKIP_TESTID.has(tid) || SKIP_ARIA.has(aria)) continue;
          if (tid || aria) continue;
          let p = b.parentElement;
          while (p) {
            if (p.tagName === 'SECTION') { dispatchClick(b); break; }
            p = p.parentElement;
          }
        }
        await sleep(400);
        input = findInput();
      }

      if (!input) return { found: false, candidates: [] };

      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;

      async function _typeAndCollect(query) {
        input.focus();
        setter.call(input, query);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        await sleep(900);

        // Clic "Paris Sportifs" si présent (bascule l'onglet de résultats)
        for (const btn of Array.from(document.querySelectorAll('button'))) {
          if ((btn.textContent || '').toLowerCase().includes('paris sportifs')) {
            dispatchClick(btn);
            await sleep(300);
            break;
          }
        }

        const found = [];
        const seen = new Set();
        for (const link of Array.from(document.querySelectorAll("a[href*='/sports/']"))) {
          if (link.offsetParent === null) continue;
          const href = (link.getAttribute('href') || '').split('?')[0];
          const text = (link.textContent || '').trim();
          if (!href || seen.has(href)) continue;
          const parts = href.replace(/\/$/, '').split('/');
          if (parts.length < 7) continue; // URL de match = au moins 7 segments
          seen.add(href);
          const absolute = href.startsWith('http') ? href : (location.origin + href);
          found.push({ text, url: absolute });
        }
        return found;
      }

      let candidates = await _typeAndCollect(equipe1);

      // Repli : certains noms de joueurs tennis extraits "Nom Prénom" (ex: "Humbert
      // Ugo") ne remontent aucun résultat sur la recherche Stake (constaté le
      // 2026-10-28 -- "Humbert Ugo" → 0 résultat, "Humbert" seul → trouvé), alors que
      // le nom complet fonctionne en saisie manuelle réelle (événements clavier
      // caractère par caractère, pas un seul 'input' synthétique). Repli sur le
      // premier mot NON-article (ex: "Le Havre" → "Havre", pas "Le" -- constaté le
      // 2026-10-30, "Le" seul ne retrouve pas le bon match) plutôt que de dépendre
      // du timing de saisie.
      const STOPWORDS = new Set(['le', 'la', 'les', 'l', 'un', 'une', 'des', 'de', 'du']);
      function _meaningfulWord(s) {
        const words = (s || '').trim().split(/\s+/);
        return words.find((w) => !STOPWORDS.has(w.toLowerCase())) || words[0];
      }

      let keyWord = _meaningfulWord(equipe1);
      if (candidates.length === 0 && keyWord && keyWord !== equipe1) {
        candidates = await _typeAndCollect(keyWord);
      }

      // Repli : la recherche Stake semble mettre en cache un résultat vide pour une
      // chaîne exacte (constaté le 2026-10-30 -- "Havre" → 0 résultat de façon
      // répétée et stable, alors que "havre"/"HAVRE"/"Havr" trouvent le même match
      // instantanément). Rejouer avec une casse différente change la clé de cache
      // sans changer le sens de la recherche.
      if (candidates.length === 0) {
        const lastTry = keyWord || equipe1;
        const altCase = lastTry.toLowerCase() === lastTry ? lastTry.toUpperCase() : lastTry.toLowerCase();
        if (altCase && altCase !== lastTry) {
          candidates = await _typeAndCollect(altCase);
        }
      }

      return { found: candidates.length > 0, candidates };
    }

    // ─── Cotes / sélection — Draw No Bet (Handicap X (0)) ───────────────────

    function _findDnbOutcomeTexts() {
      const spans = Array.from(document.querySelectorAll('span'));
      const dnbSpan = spans.find((s) => {
        const t = (s.textContent || '').trim().toLowerCase();
        return t.includes('remboursé si match nul') || t.includes('draw no bet');
      });
      if (!dnbSpan) return null;
      let container = dnbSpan;
      for (let i = 0; i < 10; i++) {
        container = container.parentElement;
        if (!container) break;
        const btns = Array.from(container.querySelectorAll('[data-testid="fixture-outcome"]'));
        if (btns.length >= 2) return btns;
      }
      return null;
    }

    function _dedupeByFirstLine(btns) {
      const seenK = new Set(); const unique = [];
      for (const b of btns) {
        const k = (b.textContent || '').trim().split('\n')[0].trim().toLowerCase();
        if (!seenK.has(k)) { seenK.add(k); unique.push(b); }
      }
      return unique;
    }

    function getDnbOdds(teamIdx) {
      const btns = _findDnbOutcomeTexts();
      if (!btns) return { found: false, odds: null };
      const unique = _dedupeByFirstLine(btns);
      const idx = teamIdx - 1;
      if (idx >= unique.length) return { found: false, odds: null };
      const parts = (unique[idx].textContent || '').trim().split('\n');
      for (const p of parts) {
        const v = parseFloat(p.replace(',', '.'));
        if (!Number.isNaN(v) && v > 1.01 && v < 200) return { found: true, odds: v };
      }
      return { found: false, odds: null };
    }

    function clickDnbOutcome(teamIdx) {
      const btns = _findDnbOutcomeTexts();
      if (!btns) return { clicked: false };
      const unique = _dedupeByFirstLine(btns);
      const btn = unique[teamIdx - 1];
      if (!btn) return { clicked: false };
      btn.scrollIntoView({ behavior: 'instant', block: 'center' });
      btn.click();
      return { clicked: true };
    }

    // ─── Cotes / sélection — marchés "table à 2 colonnes" (tennis) ──────────
    // Couvre Handicap de sets/jeux, Total de jeux (global ou par joueur) : Stake
    // affiche ces marchés en table à 2 colonnes (joueur 1/joueur 2, ou Plus de/
    // Moins de), chaque bouton ne contenant QUE la valeur + la cote (ex: "1.5
    // 1,70"), jamais le nom de la colonne. La recherche par label
    // (clickOutcomeByLabel) ne peut donc jamais matcher ces marchés. Constaté le
    // 2026-10-28 sur "Set handicap" / "Jeux handicap" / "Total jeux" / "Djokovic,
    // Novak total jeux".
    //
    // marketLabel : texte EXACT de l'en-tête de section (marchés à nom fixe :
    //   "Set handicap", "Jeux handicap", "Total jeux", "1st set - total jeux").
    // marketSubstrings : liste de sous-chaînes devant TOUTES apparaître dans
    //   l'en-tête (marchés à nom dynamique contenant le nom du joueur, ex:
    //   ["humbert", "total jeux"] → trouve "Humbert, Ugo total jeux" même si le
    //   nom extrait côté bot ("Humbert Ugo") ne correspond pas exactement à
    //   l'affichage Stake ("Humbert, Ugo")).

    function _findMarketContainer(marketLabel, marketSubstrings) {
      const matchFn = marketSubstrings
        ? (t) => { const low = t.toLowerCase(); return marketSubstrings.every((s) => low.includes(s.toLowerCase())); }
        : (t) => t.toLowerCase() === (marketLabel || '').toLowerCase();
      const all = Array.from(document.querySelectorAll('*'));
      const headerEl = all.find((el) => el.children.length === 0 && matchFn((el.textContent || '').trim()));
      if (!headerEl) return null;
      let container = headerEl;
      for (let i = 0; i < 10 && container; i++) {
        if (container.querySelectorAll('[data-testid="fixture-outcome"]').length >= 2) break;
        container = container.parentElement;
      }
      if (!container) return null;
      const outcomeBtns = Array.from(container.querySelectorAll('[data-testid="fixture-outcome"]'));
      if (outcomeBtns.length < 2) return null;

      const headerOwnText = (headerEl.textContent || '').trim().toLowerCase();
      const SKIP = new Set([headerOwnText, 'table', 'tout', 'tous']);
      const headers = [];
      for (const el of container.querySelectorAll('*')) {
        if (el.children.length !== 0 || el.closest('button')) continue;
        const t = (el.textContent || '').trim();
        if (!t || SKIP.has(t.toLowerCase()) || /^-?\d/.test(t)) continue; // valeur numérique = pas un en-tête
        headers.push(t);
        if (headers.length === 2) break;
      }
      if (headers.length < 2) return null;
      return { headers, outcomeBtns };
    }

    function _findTableMarketButton(args) {
      const { marketLabel, marketSubstrings, targetName, handicapValue } = args || {};
      const parsed = _findMarketContainer(marketLabel, marketSubstrings);
      if (!parsed) return null;
      const { headers, outcomeBtns } = parsed;
      const name = (targetName || '').trim();
      const firstWord = name.split(/\s+/)[0].toLowerCase();
      let colIndex = headers.findIndex((h) => h.toLowerCase().includes(firstWord));
      if (colIndex === -1) {
        colIndex = headers.findIndex((h) => h.toLowerCase().includes(name.toLowerCase())
          || name.toLowerCase().includes(h.toLowerCase()));
      }
      if (colIndex === -1) return null;
      const numCols = headers.length;
      for (let i = colIndex; i < outcomeBtns.length; i += numCols) {
        const txt = (outcomeBtns[i].textContent || '').trim();
        const m = txt.match(/^(-?\d+(?:[.,]\d+)?)/);
        if (m && Math.abs(parseFloat(m[1].replace(',', '.')) - handicapValue) < 0.01) return outcomeBtns[i];
      }
      return null;
    }

    function getHandicapSetGameOdds(args) {
      const btn = _findTableMarketButton(args);
      if (!btn) return { found: false, odds: null };
      const parts = (btn.textContent || '').trim().split(/\s+/);
      const odds = parseFloat((parts[parts.length - 1] || '').replace(',', '.'));
      return Number.isNaN(odds) ? { found: false, odds: null } : { found: true, odds };
    }

    function clickHandicapSetGameOutcome(args) {
      const btn = _findTableMarketButton(args);
      if (!btn) return { clicked: false };
      btn.scrollIntoView({ behavior: 'instant', block: 'center' });
      dispatchClick(btn);
      return { clicked: true };
    }

    // ─── Cotes / sélection — marché standard (recherche par label) ──────────
    // searchLabels: tableau de variantes de texte à chercher (déjà résolues côté
    // Python via BetLabelsDB / IA) — le premier bouton dont le marché parent
    // contient une des variantes est choisi.

    function _marketText(el) {
      const market = el.closest('[class*="market"], [class*="Market"], [class*="bet"]');
      return market ? (market.textContent || '') : '';
    }

    // Texte de recherche d'un bouton d'issue : son PROPRE texte en priorité (ex:
    // "Djokovic, Novak 1,27" -- le nom ET la cote sont dans le bouton lui-même sur
    // la UI Stake actuelle), complété par le texte d'un ancêtre "market" s'il existe
    // (ancienne UI / autres layouts). _marketText seul ne suffit plus depuis la
    // refonte Stake du 2026-10-28 : plus aucune classe "market"/"bet" dans l'arbre
    // ancêtre des boutons d'issue, donc _marketText renvoie '' et AUCUN label ne
    // matchait jamais (constaté sur "Vainqueur" -- V1/V2 systématiquement en échec).
    function _outcomeSearchText(el) {
      return `${(el.textContent || '')} ${_marketText(el)}`.toLowerCase();
    }

    function getOddsByLabel(searchLabels) {
      const labelsLower = searchLabels.map((s) => s.toLowerCase());
      const els = Array.from(document.querySelectorAll(
        "[class*='odd'], [class*='Odd'], [class*='price'], [data-test*='odd']"));
      for (const el of els) {
        const searchText = _outcomeSearchText(el);
        if (labelsLower.some((l) => searchText.includes(l))) {
          // El peut maintenant être le bouton entier ("Djokovic, Novak 1,27") --
          // ne garder que le DERNIER nombre du texte, pas tout parseFloat() dessus
          // (qui échoue dès qu'il y a un nom avant la cote, cf. _outcomeSearchText).
          const parts = (el.textContent || '').trim().split(/\s+/);
          const v = parseFloat((parts[parts.length - 1] || '').replace(',', '.'));
          if (!Number.isNaN(v) && v > 1.01 && v < 200) return { found: true, odds: v };
        }
      }
      return { found: false, odds: null };
    }

    function clickOutcomeByLabel(searchLabels, noReset) {
      const labelsLower = searchLabels.map((s) => s.toLowerCase());
      // Vider le betslip AVANT de cliquer (évite reset post-clic) -- sauté pour une
      // jambe de combiné multi-matchs (noReset=true), où les sélections précédentes
      // doivent rester dans le betslip.
      if (!noReset) {
        const reset = document.querySelector('[data-testid="reset-betslip"]');
        if (reset) reset.click();
      }
      const btns = Array.from(document.querySelectorAll(
        "button[class*='outcome'], [class*='odd'], [class*='Odd'], [class*='price'], [data-test*='odd']"));
      for (const btn of btns) {
        const searchText = _outcomeSearchText(btn);
        if (labelsLower.some((l) => searchText.includes(l))) {
          dispatchClick(btn);
          return { clicked: true };
        }
      }
      return { clicked: false };
    }

    // ─── Combiné multi-matchs (accumulateur "classique", matchs différents) ──
    // Contrairement au Same Game Multi (même match), Stake construit AUTOMATIQUEMENT
    // une section "Pari multiple" (combiné) dans le betslip dès que 2+ sélections de
    // matchs DIFFÉRENTS y sont ajoutées sans reset entre les deux -- validé le
    // 2026-10-28 par inspection manuelle (clic sur un match, navigation vers un
    // second match, clic sur une sélection : le betslip affiche alors "Pari combiné
    // à 2 sélections" avec sa PROPRE mise, distincte des paris simples). Chaque
    // jambe est ajoutée séparément depuis Python (navigate vers le match, puis appel
    // à addComboLeg) -- ce module ne gère qu'UNE jambe à la fois, pas l'ensemble.

    function resetBetslip() {
      const reset = document.querySelector('[data-testid="reset-betslip"]');
      if (reset) reset.click();
      return { reset: !!reset };
    }

    function addComboLeg(args) {
      const { searchLabels, dnbTeamIdx, handicapMarket } = args || {};
      if (dnbTeamIdx) return clickDnbOutcome(dnbTeamIdx);
      if (handicapMarket) return clickHandicapSetGameOutcome(handicapMarket);
      return clickOutcomeByLabel(searchLabels || [], true);
    }

    async function confirmCombo(args) {
      const { mise, dryRun } = args || {};
      // Laisse le temps à la section "Pari multiple" de se (re-)rendre après le clic
      // sur la 2e jambe (appel séparé depuis Python, juste après addComboLeg) --
      // sans cette pause, _waitMiseInput pouvait tomber sur un DOM pas encore à jour
      // (constaté le 2026-10-29 : mise_input_not_found malgré les 2 jambes ajoutées).
      await sleep(800);
      const miseInput = await _waitMiseInput();
      if (!miseInput) return { success: false, error: 'mise_input_not_found' };
      // Le 1er input-bet-amount du betslip est celui de la section "Pari multiple"
      // (combiné) -- elle se rend AVANT la section "Paris simples" (vérifié en DOM,
      // même ordre que l'affichage visuel). Les paris simples individuels restent à
      // mise vide et ne sont donc pas inclus au clic sur "Parier" (Stake ne place que
      // les entrées dont la mise est renseignée).
      miseInput.scrollIntoView({ behavior: 'instant', block: 'center' });
      _setInputValue(miseInput, mise);
      await sleep(600);

      if (dryRun) {
        console.log('[Stake combo] 🧪 dry-run — combiné NON confirmé (simulation)');
        return { success: true, simulated: true };
      }

      await sleep(400);
      const btn = document.querySelector('[data-testid="betSlip-place-bets-button"]');
      if (btn && !btn.disabled) {
        btn.click();
        await sleep(2000);
        return { success: true };
      }
      return { success: false, error: 'confirm_button_unavailable' };
    }

    // ─── Saisie de la mise + confirmation (pari simple) ─────────────────────

    async function _waitMiseInput(timeoutMs = 8000) {
      const sels = ['[data-testid="input-bet-amount"]', 'input[type="number"][class*="spacing"]', 'input[type="number"]'];
      const start = Date.now();
      while (Date.now() - start < timeoutMs) {
        const el = firstVisible(sels);
        if (el) return el;
        await sleep(500);
      }
      return null;
    }

    function _setInputValue(el, value) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      el.focus();
      setter.call(el, '');
      el.dispatchEvent(new Event('input', { bubbles: true }));
      setter.call(el, String(value));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }

    async function placeBet(args) {
      const { searchLabels, mise, dnbTeamIdx, handicapMarket, dryRun } = args || {};
      let clicked = false;
      if (dnbTeamIdx) {
        clicked = clickDnbOutcome(dnbTeamIdx).clicked;
      } else if (handicapMarket) {
        clicked = clickHandicapSetGameOutcome(handicapMarket).clicked;
      } else {
        clicked = clickOutcomeByLabel(searchLabels || []).clicked;
      }
      if (!clicked) return { success: false, error: 'outcome_not_found' };

      await sleep(900);
      // Pour DNB : vider betslip puis re-cliquer (Stake peut reset le 1er clic)
      if (dnbTeamIdx) {
        const reset = document.querySelector('[data-testid="reset-betslip"]');
        if (reset) { reset.click(); await sleep(800); }
        await sleep(300);
        clickDnbOutcome(dnbTeamIdx);
      }

      const miseInput = await _waitMiseInput();
      if (miseInput && mise != null) {
        miseInput.scrollIntoView({ behavior: 'instant', block: 'center' });
        _setInputValue(miseInput, mise);
        await sleep(600);
      }

      await sleep(500);

      if (dryRun) {
        console.log('[Stake] 🧪 dry-run — pari NON confirmé (simulation)');
        return { success: true, simulated: true };
      }

      const btn = document.querySelector('[data-testid="betSlip-place-bets-button"]');
      if (btn && !btn.disabled) {
        btn.click();
        await sleep(2000);
        return { success: true };
      }
      return { success: false, error: 'confirm_button_unavailable' };
    }

    // ─── Same Game Multi ("Pari Multiple sur un Même Match") ────────────────
    // combinedLegs: [{ searchLabels: [variantes...] }, ...] déjà résolues côté Python.

    async function _fetchSgmButtons() {
      for (let i = 0; i < 8; i++) {
        let btns = Array.from(document.querySelectorAll('[data-testid="fixture-outcome"]'));
        if (!btns.length) btns = Array.from(document.querySelectorAll('.market button.outcome'));
        if (!btns.length) btns = Array.from(document.querySelectorAll("button[class*='outcome']"));
        if (btns.length) return btns;
        await sleep(500);
      }
      return [];
    }

    async function placeSameGameMulti(args) {
      const { combinedLegs, mise, dryRun } = args || {};

      // 1. Onglet SGM
      let sgmClicked = false;
      for (const sel of ['[data-testid="tab-customBet"]', 'button[data-testid*="customBet"]']) {
        const btns = Array.from(document.querySelectorAll(sel));
        if (btns.length) { dispatchClick(btns[0]); sgmClicked = true; await sleep(1200); break; }
      }
      if (!sgmClicked) {
        for (const btn of Array.from(document.querySelectorAll('button'))) {
          const t = (btn.textContent || '').toLowerCase();
          if (t.includes('pari multiple sur un même match') || t.includes('same game')) {
            dispatchClick(btn); sgmClicked = true; await sleep(1200); break;
          }
        }
      }

      // 2. Sélectionner chaque jambe
      let selectionsClicked = 0;
      for (const leg of (combinedLegs || [])) {
        // Marché "table à 2 colonnes" (Total, Handicap de sets/jeux) -- même
        // onglet "Pari Multiple" que les marchés simples, donc _findTableMarketButton
        // (conçu pour la page match standard) fonctionne ici aussi tel quel.
        // Clé en snake_case (pas camelCase) : contrairement aux autres actions,
        // service_worker.js transmet le tableau combined_legs tel quel depuis
        // Python, sans renommer les clés internes de chaque jambe.
        const legHandicapMarket = leg.handicapMarket || leg.handicap_market;
        if (legHandicapMarket) {
          const btn = _findTableMarketButton(legHandicapMarket);
          if (btn) {
            btn.scrollIntoView({ behavior: 'instant', block: 'center' });
            await sleep(350);
            dispatchClick(btn);
            selectionsClicked++;
            await sleep(700);
          } else {
            console.warn('[Stake SGM] sélection table non trouvée:', legHandicapMarket);
          }
          continue;
        }

        const labelsLower = (leg.searchLabels || []).map((s) => s.toLowerCase());
        let btns = await _fetchSgmButtons();
        let clicked = false;
        for (const btn of btns) {
          const lbl = (btn.textContent || '').trim().toLowerCase().split('\n')[0].trim();
          if (labelsLower.some((v) => lbl.includes(v))) {
            btn.scrollIntoView({ behavior: 'instant', block: 'center' });
            await sleep(350);
            btn.click();
            clicked = true;
            selectionsClicked++;
            await sleep(700);
            break;
          }
        }
        if (!clicked) {
          console.warn('[Stake SGM] sélection non trouvée:', leg.searchLabels);
        }
      }

      if (selectionsClicked < 2) {
        return { success: false, error: 'not_enough_selections', selectionsClicked };
      }

      await sleep(1000);

      // 3. "Ajouter un pari"
      let ajouterClicked = false;
      for (const btn of Array.from(document.querySelectorAll('button'))) {
        if ((btn.textContent || '').toLowerCase().includes('ajouter un pari')) {
          btn.click(); // vrai clic nécessaire (état Svelte)
          ajouterClicked = true;
          await sleep(2200);
          break;
        }
      }
      if (!ajouterClicked) return { success: false, error: 'add_bet_button_not_found', selectionsClicked };

      // 4. Mise dans le betslip
      let miseInput = null;
      for (let i = 0; i < 20; i++) {
        await sleep(500);
        const sels = ['[data-testid="input-bet-amount"]', 'input[type="number"][placeholder="0.00"]', 'input[type="number"]'];
        for (const sel of sels) {
          const candidates = Array.from(document.querySelectorAll(sel)).filter((el) => {
            const ph = (el.getAttribute('placeholder') || '').toLowerCase();
            return !ph.includes('recherch') && !ph.includes('search');
          });
          if (candidates.length) { miseInput = candidates[0]; break; }
        }
        if (miseInput) break;
      }
      if (!miseInput) return { success: false, error: 'mise_input_not_found', selectionsClicked };

      miseInput.scrollIntoView({ behavior: 'instant', block: 'center' });
      await sleep(300);
      _setInputValue(miseInput, mise);
      await sleep(700);

      if (dryRun) {
        console.log(`[Stake SGM] 🧪 dry-run — pari NON confirmé (simulation, ${selectionsClicked} sélections)`);
        return { success: true, simulated: true, selectionsClicked };
      }

      // 5. "Parier"
      let parierClicked = false;
      for (let attempt = 0; attempt < 5 && !parierClicked; attempt++) {
        for (const btn of Array.from(document.querySelectorAll('button'))) {
          if ((btn.textContent || '').trim().toLowerCase() === 'parier') {
            btn.scrollIntoView({ behavior: 'instant', block: 'center' });
            await sleep(300);
            if (btn.disabled) break;
            btn.click();
            parierClicked = true;
            break;
          }
        }
        if (!parierClicked) await sleep(1000);
      }

      if (parierClicked) {
        await sleep(2500);
        return { success: true, selectionsClicked };
      }
      return { success: false, error: 'confirm_button_unavailable', selectionsClicked };
    }

    window._martingale = {
      __site: 'stake',
      getState,
      searchMatch,
      getDnbOdds,
      clickDnbOutcome,
      getHandicapSetGameOdds,
      clickHandicapSetGameOutcome,
      getOddsByLabel,
      clickOutcomeByLabel,
      placeBet,
      placeSameGameMulti,
      resetBetslip,
      addComboLeg,
      confirmCombo,
    };

    console.log('[Stake] window._martingale créé ✓');
  } catch (e) {
    console.error('[Stake] ERREUR:', e);
  }
})();

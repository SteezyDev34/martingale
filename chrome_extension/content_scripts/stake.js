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

      input.focus();
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(input, equipe1);
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

      const candidates = [];
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
        candidates.push({ text, url: absolute });
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

    // ─── Cotes / sélection — marché standard (recherche par label) ──────────
    // searchLabels: tableau de variantes de texte à chercher (déjà résolues côté
    // Python via BetLabelsDB / IA) — le premier bouton dont le marché parent
    // contient une des variantes est choisi.

    function _marketText(el) {
      const market = el.closest('[class*="market"], [class*="Market"], [class*="bet"]');
      return market ? (market.textContent || '') : '';
    }

    function getOddsByLabel(searchLabels) {
      const labelsLower = searchLabels.map((s) => s.toLowerCase());
      const els = Array.from(document.querySelectorAll(
        "[class*='odd'], [class*='Odd'], [class*='price'], [data-test*='odd']"));
      for (const el of els) {
        const parentText = _marketText(el).toLowerCase();
        if (labelsLower.some((l) => parentText.includes(l))) {
          const raw = (el.textContent || '').trim().replace(',', '.');
          const v = parseFloat(raw);
          if (!Number.isNaN(v) && v > 1.01 && v < 200) return { found: true, odds: v };
        }
      }
      return { found: false, odds: null };
    }

    function clickOutcomeByLabel(searchLabels) {
      const labelsLower = searchLabels.map((s) => s.toLowerCase());
      // Vider le betslip AVANT de cliquer (évite reset post-clic)
      const reset = document.querySelector('[data-testid="reset-betslip"]');
      if (reset) reset.click();
      const btns = Array.from(document.querySelectorAll(
        "button[class*='outcome'], [class*='odd'], [class*='Odd'], [class*='price'], [data-test*='odd']"));
      for (const btn of btns) {
        const parentText = _marketText(btn).toLowerCase();
        if (labelsLower.some((l) => parentText.includes(l))) {
          dispatchClick(btn);
          return { clicked: true };
        }
      }
      return { clicked: false };
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
      const { searchLabels, mise, dnbTeamIdx } = args || {};
      let clicked = false;
      if (dnbTeamIdx) {
        clicked = clickDnbOutcome(dnbTeamIdx).clicked;
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
      const { combinedLegs, mise } = args || {};

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
      getOddsByLabel,
      clickOutcomeByLabel,
      placeBet,
      placeSameGameMulti,
    };

    console.log('[Stake] window._martingale créé ✓');
  } catch (e) {
    console.error('[Stake] ERREUR:', e);
  }
})();

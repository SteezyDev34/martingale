# Lollybet — Implémentation complète

## Résumé

Le scraper Lollybet est **entièrement validé** end-to-end :
- Session active détectée (`balance`)
- Recherche de match via la barre de recherche shadow DOM
- Récupération de la cote
- Placement du pari avec confirmation

**Différence clé vs Winamax/Betclic** : Lollybet bloque Playwright/CDP. On utilise **Selenium** avec le driver partagé existant (fenêtre 8, port 43151).

---

## Fichiers concernés

| Fichier | Rôle |
|---------|------|
| `Functions/Bookmakers/LollybetScraper.py` | Scraper principal |
| `Functions/Bookmakers/_test_lollybet_bet.py` | Script de test end-to-end |
| `ChromeDriver/SetDriver.py` | Driver Selenium partagé (`get_script_driver(8)`) |
| `ChromeDriver/lollybet_profile/` | Profil Chrome persistant (session) |

---

## Particularité : Shadow DOM + Selenium 4

Le sportsbook Lollybet est rendu dans un **Shadow Root** (`SG-SB-ROOT-*` custom element).

**Solution** : Selenium 4 expose `element.shadow_root` qui retourne un objet `ShadowRoot` sur lequel on peut faire `find_element` et `send_keys` nativement — pas besoin de JS.

```python
sg_el = driver.execute_script(
    "return Array.from(document.querySelectorAll('*'))"
    ".find(function(e){ return e.tagName.startsWith('SG-'); });"
)
sr = sg_el.shadow_root                          # ShadowRoot natif Selenium 4
inp = sr.find_element(By.CSS_SELECTOR, ".sb-search-field__input")
inp.send_keys("Sinner")                         # fonctionne directement
```

---

## Sélecteurs CSS validés (shadow root)

| Élément | Sélecteur |
|---------|-----------|
| Barre de recherche | `.sb-search-field__input` |
| Résultat de recherche | `.sb-search-results-item` |
| Bouton de cote (conteneur) | `.sb-game-event-content.sb-bet-button` |
| Label de sélection | `.sb-game-event__name` |
| Input de mise | `input[placeholder='Mise']` / `.sb-betslip-bet-input_buttons__input` |
| Bouton Parier | `.sb-bet-slip-footer-v2__btn_submit` |

### Sélecteurs DOM principal (session)

| Élément | Sélecteur |
|---------|-----------|
| Solde / session active | `[class*='balance']` |

---

## Format des scores

Lollybet utilise `:` comme séparateur : `3:0`, `2:1`, etc.
Le bot reçoit les sélections avec `-` : `3-0`.
La fonction `_norm_lollybet()` normalise les deux vers `-` avant comparaison.

---

## Mapping des sports

| Sport (interne) | Slug URL |
|----------------|----------|
| 1 — Football | `football` |
| 2 — Tennis | `tennis` |
| 4 — Basketball | `basketball` |
| 5 — Rugby | `rugby` |
| 8 — Handball | `handball` |
| 9 — Hockey | `hockey` |

URL sportsbook : `https://lolly-bet99.com/fr/sportsbook#/events/{sport_slug}`

---

## Flux de placement d'un pari

### 1. `is_logged_in(driver)`
Navigation vers `https://lolly-bet99.com` → cherche `[class*='balance']` dans le DOM principal.

### 2. `search_match(driver, equipe_1, equipe_2, sport, date)`
1. Navigation `#/events/{sport_slug}`
2. `_wait_shadow_root()` (max 15s)
3. `sr.find_element(".sb-search-field__input")` → `clear()` + `send_keys(equipe_1)`
4. Attente 2–3s → `sr.find_elements(".sb-search-results-item")`
5. Clic sur l'item contenant les deux noms → retourne `driver.current_url`

### 3. `get_odds(driver, match_url, selection, categorie)`
1. Navigation `match_url`
2. `_wait_shadow_root()` → recherche `.sb-game-event-content.sb-bet-button`
3. Dans chaque bouton : compare `.sb-game-event__name` normalisé avec `search_label`
4. Extrait la cote numérique du texte du bouton

### 4. `place_bet(driver, match_url, selection, categorie, mise)`
1. Navigation + shadow root
2. `_clear_betslip()` → supprimer sélections existantes
3. `_click_outcome()` → clic sur `.sb-bet-button` avec le bon label
4. `_verify_betslip()` → vérifie que la sélection est dans le betslip
5. `input[placeholder='Mise']` → `clear()` + `send_keys("0,10")`
6. `.sb-bet-slip-footer-v2__btn_submit` → clic → confirmation

---

## Résultat du test de validation

**Pari testé :**
```
equipe_1  : Sinner
equipe_2  : Kecmanovic
sport     : 2 (tennis)
date      : 2026-06-27
selection : 3-0
categorie : Score exact
mise      : 0.10€
```

**Résultat :**
```
✅ Session active ([class*='balance']) → '598,71 €'
✅ Match trouvé: ATP - Wimbledon, Simple Messieurs — Sinner, Jannik v Kecmanovic, Miomir
   URL: https://lolly-bet99.com/fr/sportsbook#/sports/tennis/atp/wimbledon-men-singles/match_8478671
✅ Cote trouvée: 1.35
✅ Clic cote: '3:0'
✅ Betslip vérifié: '3-0' présent
✅ Mise saisie: 0,10
✅ Pari validé (bouton 'Parier' + confirmation détectée)
```

---

## Points d'attention

- **Selenium 4 obligatoire** pour `element.shadow_root`. Selenium 3 ne supporte pas.
- **Driver partagé fenêtre 8** : `get_script_driver(8)` sur port `43151`. Chrome doit être lancé avec `--remote-debugging-port=43151 --user-data-dir=lollybet_profile`.
- **Format score `:` vs `-`** : toujours normaliser via `_norm_lollybet()` avant comparaison.
- **SG-* tag dynamique** : le tag exact (`SG-SB-ROOT-1782511523200`) change selon la version du widget. On le trouve via `tagName.startsWith('SG-')`.
- **Betslip persistant** : `_clear_betslip()` avant chaque pari pour éviter les combinés.

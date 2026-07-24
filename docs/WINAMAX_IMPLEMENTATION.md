# Winamax — Implémentation complète

## Résumé

Le scraper Winamax utilise **Selenium** avec le driver partagé (fenêtre 9, port 43151).
DOM standard — pas de shadow root, pas de Playwright.

---

## Fichiers concernés

| Fichier | Rôle |
|---------|------|
| `Functions/Bookmakers/WinamaxScraper.py` | Scraper principal |
| `ChromeDriver/SetDriver.py` | Driver Selenium partagé (`get_script_driver(9)`) |
| `ChromeDriver/winamax_profile/` | Profil Chrome persistant (session) |

---

## Architecture

- **Fenêtre 9** dans le driver partagé Chrome (port 43151)
- DOM standard Winamax — `driver.find_element(By.CSS_SELECTOR, ...)` directement
- Interface router asynchrone : `run(bet)` et `fetch_odds(bet)` wrappent les méthodes sync via `run_in_executor`
- Pas de `BookmakerScraper` base (Playwright) — classe standalone

---

## Sélecteurs CSS validés

| Élément | Sélecteur |
|---------|-----------|
| Session active | `[data-test='account-menu']`, `[class*='UserMenu']`, `[class*='userBalance']` |
| Barre de recherche | `input[placeholder='Rechercher']` |
| Résultat de recherche | `.search-row-result` |
| Conteneur cote | `.bet-group-outcome-odd` |
| Bouton cote | `.odd-button-wrapper` |
| Valeur cote | `span.odd-button-value` |
| Input mise | `input.sc-bSoiow` |
| Bouton Parier | `button` (filtré par texte `parier`) |

---

## Flux de placement d'un pari

### 1. `is_logged_in(driver)`
Navigation `https://www.winamax.fr` → cherche les sélecteurs de session dans le DOM.

### 2. `search_match(driver, equipe_1, equipe_2, sport, date)`
1. Navigation `https://www.winamax.fr/paris-sportifs/sports/{sport_id}`
2. `input[placeholder='Rechercher']` → `send_keys(equipe_1)`
3. `.search-row-result` → clic sur le résultat contenant les deux équipes
4. Fallback equipe_2 si non trouvé

### 3. `get_odds(driver, match_url, selection, categorie)`
1. Navigation `match_url`
2. `.bet-group-outcome-odd` → filtre par label normalisé
3. `span.odd-button-value` → retourne la cote float

### 4. `place_bet(driver, match_url, selection, categorie, mise)`
1. Navigation + clic sur `.odd-button-wrapper` dans le bon conteneur
2. `input.sc-bSoiow` → saisie mise
3. `button[text*='parier']` → clic + détection confirmation

---

## Mapping des sports

| Sport (interne) | ID URL Winamax |
|----------------|----------------|
| 1 — Football | `/sports/1` |
| 2 — Tennis | `/sports/5` |
| 4 — Basketball | `/sports/4` |
| 5 — Rugby | `/sports/6` |
| 8 — Handball | `/sports/8` |
| 9 — Hockey | `/sports/9` |

---

## Points d'attention

- **Fenêtre 9** : Chrome doit être lancé sur le port 43151 avec `--remote-debugging-port=43151`
- **Sélecteur stake** `input.sc-bSoiow` : classe générée par Styled Components — peut changer. Fallback : `[class*='betslip'] input`
- **Confirmation** : cherche `"Ton pari est validé"` dans le DOM — si absent mais pas d'erreur, le pari est considéré placé

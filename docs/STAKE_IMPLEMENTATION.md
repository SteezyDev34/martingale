# Stake — Implémentation complète

## Résumé

Le scraper Stake utilise **Selenium** avec le driver partagé (fenêtre 11, port 43151).
DOM standard, pas de shadow root, pas de Playwright. VPN requis (Canada / Toronto).

---

## Fichiers concernés

| Fichier | Rôle |
|---------|------|
| `Functions/Bookmakers/StakeScraper.py` | Scraper principal |
| `ChromeDriver/SetDriver.py` | Driver Selenium partagé (`get_script_driver(11)`) |
| `ChromeDriver/stake_profile/` | Profil Chrome persistant (session) |

---

## Architecture

- **Fenêtre 11** dans le driver partagé Chrome (port 43151)
- DOM standard — `driver.find_element(By.CSS_SELECTOR, ...)` directement
- Interface router : `run(bet)` et `fetch_odds(bet)` → `run_in_executor`
- Classe standalone, pas de `BookmakerScraper` Playwright

---

## VPN

Stake.bet est accessible uniquement depuis certains pays (Canada recommandé).
Le scraper ne gère pas le VPN — il doit être actif avant de lancer le script.
`StakeScraper.requires_vpn = True` est utilisé par le router pour logging.

---

## Sélecteurs CSS (indicatifs — à valider en inspection réelle)

| Élément | Sélecteur |
|---------|-----------|
| Session active | `[class*='userBalance']`, `[class*='HeaderUser']`, `button[class*='wallet']` |
| Lien de match | `a[href*='/sports/']` |
| Cote / odd | `[class*='odd']`, `[class*='price']`, `[data-test*='odd']` |
| Input mise | `input[placeholder*='amount']`, `input[placeholder*='stake']` |
| Bouton confirmer | `[class*='placeBet']`, `button[class*='confirm']` |

> **Note** : Stake.bet utilise des classes CSS générées dynamiquement. Ces sélecteurs sont indicatifs et devront être mis à jour après inspection DOM réelle sur la version live du site.

---

## Flux de placement d'un pari

### 1. `is_logged_in(driver)`
Navigation `https://stake.bet` → cherche les sélecteurs de session.

### 2. `search_match(driver, equipe_1, equipe_2, sport, date)`
1. Navigation `https://stake.bet/sports/{sport_slug}/matches`
2. Recherche optionnelle via `input[type='search']`
3. `a[href*='/sports/']` → filtre les liens par texte contenant les deux équipes

### 3. `get_odds(driver, match_url, selection, categorie)`
1. Navigation `match_url`
2. `[class*='odd']` → JS `closest('[class*="market"]')` pour obtenir le contexte
3. Filtre par `search_label` dans le texte du marché parent

### 4. `place_bet(driver, match_url, selection, categorie, mise)`
1. Clic sur le bouton de cote trouvé via le même mécanisme
2. Saisie de la mise dans `input[placeholder*='amount']`
3. Clic sur `[class*='placeBet']` pour confirmer

---

## Mapping des sports

| Sport (interne) | Slug URL |
|----------------|----------|
| 2 — Tennis | `tennis` |
| 3 — Football | `soccer` |
| 4 — Basketball | `basketball` |
| 5 — Rugby | `rugby` |
| 8 — Handball | `handball` |

---

## Points d'attention

- **VPN obligatoire** avant de naviguer sur stake.bet
- **Fenêtre 11** : Chrome sur port 43151
- **Sélecteurs dynamiques** : les classes CSS de Stake changent fréquemment — inspecter le DOM si les cotes ne sont pas trouvées
- **Login manuel uniquement** : `session_init.py` ouvre la page de login et attend que l'utilisateur se connecte dans la fenêtre

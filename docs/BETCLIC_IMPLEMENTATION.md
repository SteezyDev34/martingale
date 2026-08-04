# Betclic — Implémentation complète

## Résumé

Le scraper Betclic utilise **Selenium** avec le driver partagé (fenêtre 10, port 43151).
Application Angular — DOM standard accessible directement, pas de shadow root, pas de Playwright.

---

## Fichiers concernés

| Fichier | Rôle |
|---------|------|
| `Functions/Bookmakers/BetclicScraper.py` | Scraper principal |
| `ChromeDriver/SetDriver.py` | Driver Selenium partagé (`get_script_driver(10)`) |
| `ChromeDriver/betclic_profile/` | Profil Chrome persistant (session) |

---

## Architecture

- **Fenêtre 10** dans le driver partagé Chrome (port 43151)
- Application Angular — les composants custom (`sports-betting-slip`, `betting-slip-selection-card`) sont des éléments Angular, pas du Shadow DOM : accessibles via CSS standard
- Interface router : `run(bet)` et `fetch_odds(bet)` → `run_in_executor` (sync → async)
- Classe standalone, pas de `BookmakerScraper` Playwright

---

## Sélecteurs CSS validés

| Élément | Sélecteur |
|---------|-----------|
| Session active | `[class*='balance']`, `[data-automation-id='user-balance']`, `betclic-header-user` |
| Barre de recherche | `input[placeholder*='Joueur']` |
| Carte de match | `a.cardEvent` |
| Marché | `[class*='market']` |
| Label sélection | `.marketBox_label` |
| Bouton cote | `button.btn.is-odd` |
| Input mise | `input[placeholder='Mise']` |
| Bouton Parier | `sports-betting-slip button` (texte `parier`) |
| Betslip | `sports-betting-slip` |

---

## Logique de recherche de cote (DOM traversal JS)

Betclic sépare le label de la cote dans deux éléments frères. Pour trouver le bouton `is-odd` associé à un label `.marketBox_label`, on remonte le DOM via JS :

```javascript
var el = labelEl;
for (var i = 0; i < 6; i++) {
    el = el.parentElement;
    if (!el) break;
    var btn = el.querySelector('button.btn.is-odd');
    if (btn) return btn;
}
return null;
```

Exécuté via `driver.execute_script("...", label_el)`.

---

## Flux de placement d'un pari

### 1. `is_logged_in(driver)`
Navigation `https://www.betclic.fr` → cherche `[class*='balance']` ou `betclic-header-user`.

### 2. `search_match(driver, equipe_1, equipe_2, sport, date)`
1. Navigation `https://www.betclic.fr/{sport_slug}`
2. `input[placeholder*='Joueur']` → `send_keys(equipe_1)`
3. `a.cardEvent` → clic sur la carte contenant les deux équipes
4. Fallback equipe_2

### 3. `get_odds(driver, match_url, selection, categorie)`
1. Navigation `match_url`
2. `[class*='market']` → filtre par catégorie + label normalisé
3. JS traversal → `button.btn.is-odd` → retourne la cote float

### 4. `place_bet(driver, match_url, selection, categorie, mise)`
1. `_clear_betslip()` → supprime les sélections existantes
2. Trouve et clique le bouton `is-odd` via JS traversal
3. `_verify_betslip()` → vérifie que la sélection est dans `sports-betting-slip`
4. `input[placeholder='Mise']` → saisie mise
5. Clic `Parier` → détection `"Ton pari est validé"`

---

## Mapping des sports

| Sport (interne) | Slug URL |
|----------------|----------|
| 1 — Football | `football-sfootball` |
| 2 — Tennis | `tennis-stennis` |
| 4 — Basketball | `basketball-sbasketball` |
| 5 — Rugby | `rugby-srugby` |
| 8 — Handball | `handball-shandball` |
| 9 — Hockey | `hockey-sur-glace-shockey` |

---

## Points d'attention

- **Fenêtre 10** : Chrome sur port 43151
- **Angular CDK** : les composants Angular (`sports-betting-slip`, etc.) sont dans le DOM principal, pas dans un shadow root — CSS standard fonctionne
- **`_clear_betslip`** obligatoire avant chaque pari pour éviter les combinés accidentels
- **Bouton Parier désactivé** : si `disabled` est présent, la cote ou la mise est invalide

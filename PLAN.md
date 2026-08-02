# Plan d'intégration des bookmakers

## Objectif

À chaque pari reçu via Telegram, le bot :
1. Récupère les cotes sur **Winamax, Betclic, Lollybet, Stake**
2. Place le pari sur le bookmaker avec la **meilleure cote**
3. Notifie l'API que le pari est traité (`telegram_bets_api.mark_bet_as_processed(bet_id)`)

---

## Contraintes

- Connexion **manuelle** au démarrage (pas de login automatique — anti-bot)
- **Cloudflare** sur Betclic, Lollybet, Stake → login via Chrome subprocess (sans Playwright)
- Mises de test : **0.10€**
- Alerte Telegram (`alertGroup`) si session expirée en cours de route
- 1xBet et VPN mis de côté pour l'instant

---

## Architecture

```
SCRIPTS_WATCH/main-1.py
    └── init_bookmaker_sessions()        ← ouvre Chrome pour login manuel
            ├── Winamax   (Playwright)
            ├── Betclic   (Chrome subprocess)
            ├── Lollybet  (Chrome subprocess)
            └── Stake     (Chrome subprocess)

    └── boucle Telegram (pari reçu)
            └── place_best_bet(bet)
                    ├── get_best_odds()  ← récupère cotes sur les 4 en parallèle
                    │       ├── WinamaxScraper.fetch_odds()
                    │       ├── BetclicScraper.fetch_odds()
                    │       ├── LollybetScraper.fetch_odds()
                    │       └── StakeScraper.fetch_odds()
                    └── _place_bet_sync(meilleur_bookmaker, bet)
                            └── mark_bet_as_processed(bet_id)  ← API
```

---

## État actuel

| Bookmaker | Session init | fetch_odds | place_bet | Statut |
|-----------|-------------|------------|-----------|--------|
| Winamax   | ✅ OK        | ✅ OK      | ✅ Validé  | **Terminé** |
| Betclic   | ✅ Chrome subprocess | ❌ Sélecteurs inconnus | ❌ Non testé | **En cours** |
| Lollybet  | ✅ Chrome subprocess | ❌ Sélecteurs inconnus | ❌ Non testé | **En cours** |
| Stake     | ✅ Chrome subprocess | ❌ Cloudflare bloque | ❌ Non testé | **Bloqué** |

---

## Étapes détaillées

---

### ✅ ÉTAPE 0 — Winamax (terminé)

- [x] Session init Playwright avec profil persistant
- [x] `search_match()` via barre de recherche + sélecteur `.search-row-result`
- [x] `get_odds()` via `.bet-group-outcome-odd` + `span.odd-button-value`
- [x] `place_bet()` : clic `.odd-button-wrapper`, saisie `input.sc-bSoiow`, clic "parier"
- [x] Modal de validation : `page.locator("text=Ton pari est validé").wait_for(timeout=8000)`
- [x] Test end-to-end : Sinner vs Kecmanovic, score exact 3-0, 0.10€ ✅

---

### 🔲 ÉTAPE 1 — Betclic

#### 1.1 Inspecter le DOM
Ouvrir `https://www.betclic.fr` dans Chrome (profil `betclic_profile`) et inspecter :

- [ ] Sélecteur barre de recherche (input de recherche de match)
- [ ] Sélecteur des suggestions de résultats (dropdown après frappe)
- [ ] Sélecteur du lien cliquable vers la page du match
- [ ] Sélecteur des conteneurs de cote (bloc contenant le libellé + la valeur)
- [ ] Sélecteur de la valeur de la cote (le chiffre)
- [ ] Sélecteur du bouton cliquable pour sélectionner une cote
- [ ] Sélecteur du champ de mise (input dans le betslip)
- [ ] Sélecteur du bouton de confirmation ("Valider mon pari" ou équivalent)
- [ ] Texte ou sélecteur de la modal de confirmation après placement
- [ ] Sélecteur indiquant que l'utilisateur est connecté (pour `is_logged_in`)

#### 1.2 Mettre à jour `BetclicScraper.py`
- [ ] Remplacer les sélecteurs génériques par les vrais sélecteurs trouvés
- [ ] Implémenter `search_match()` avec le bon flux de navigation
- [ ] Implémenter `get_odds()` avec les bons sélecteurs
- [ ] Implémenter `place_bet()` avec confirmation modale
- [ ] Mettre à jour `is_logged_in()` avec le bon sélecteur

#### 1.3 Tester
- [ ] Lancer `_test_betclic_bet.py` avec mise 0.10€
- [ ] Vérifier : session active → match trouvé → cote récupérée → pari placé → modal détectée

---

### 🔲 ÉTAPE 2 — Lollybet

#### 2.1 Inspecter le DOM
Ouvrir `https://lolly-bet99.com` dans Chrome (profil `lollybet_profile`) et inspecter :

- [ ] Sélecteur barre de recherche
- [ ] Sélecteur des suggestions de résultats
- [ ] Sélecteur des conteneurs de cote
- [ ] Sélecteur de la valeur de la cote
- [ ] Sélecteur du bouton de sélection de cote
- [ ] Sélecteur du champ de mise
- [ ] Sélecteur du bouton de confirmation
- [ ] Texte/sélecteur de la modal de confirmation
- [ ] Sélecteur de connexion active (pour `is_logged_in`)

#### 2.2 Mettre à jour `LollybetScraper.py`
- [ ] Remplacer les sélecteurs génériques par les vrais sélecteurs
- [ ] Implémenter `search_match()`, `get_odds()`, `place_bet()`
- [ ] Mettre à jour `is_logged_in()`

#### 2.3 Tester
- [ ] Lancer `_test_lollybet_bet.py` avec mise 0.10€
- [ ] Vérifier le flux complet

---

### 🔲 ÉTAPE 3 — Stake

#### 3.1 Contourner Cloudflare pour Playwright
Options à tester dans l'ordre :
- [ ] `playwright-stealth` (déjà installé) + vrai Chrome (`executable_path`)
- [ ] Si échec : tester `undetected-playwright` ou `nodriver`
- [ ] Si échec : session via Chrome subprocess, puis Playwright en `headless=False` avec stealth sur profil déjà connecté

#### 3.2 Inspecter le DOM de Stake
Ouvrir `https://stake.bet` dans Chrome (profil `stake_profile`) et inspecter :

- [ ] Sélecteur barre de recherche
- [ ] Sélecteur des suggestions
- [ ] Sélecteur des cotes
- [ ] Sélecteur du champ de mise
- [ ] Sélecteur du bouton confirmer
- [ ] Modal de validation
- [ ] Sélecteur de connexion active

#### 3.3 Mettre à jour `StakeScraper.py`
- [ ] Implémenter `search_match()`, `get_odds()`, `place_bet()`

#### 3.4 Tester
- [ ] Lancer `_test_stake_bet.py` avec mise 0.10€

---

### 🔲 ÉTAPE 4 — Intégration finale

#### 4.1 Session init
- [ ] Vérifier que les 4 fenêtres s'ouvrent correctement au démarrage
- [ ] Vérifier que Winamax détecte la session existante sans redemander la connexion
- [ ] Vérifier que Chrome subprocess s'ouvre pour Betclic/Lollybet/Stake sans bloquer

#### 4.2 Router
- [ ] Vérifier que `get_best_odds()` interroge les 4 bookmakers en parallèle
- [ ] Vérifier que `place_best_bet()` place sur **un seul** (le meilleur)
- [ ] Vérifier que `mark_bet_as_processed(bet_id)` est appelé après succès

#### 4.3 Flux Telegram complet
- [ ] Envoyer un vrai pari via Telegram
- [ ] Vérifier que le bot le reçoit, compare les cotes, place et notifie l'API

---

## Fichiers clés

| Fichier | Rôle |
|---------|------|
| `Functions/Bookmakers/session_init.py` | Login manuel au démarrage |
| `Functions/Bookmakers/router.py` | Comparaison cotes + placement unique |
| `Functions/Bookmakers/base.py` | Classe abstraite + `fetch_odds()` + `run()` |
| `Functions/Bookmakers/WinamaxScraper.py` | ✅ Complet |
| `Functions/Bookmakers/BetclicScraper.py` | ⚠️ Sélecteurs à remplir |
| `Functions/Bookmakers/LollybetScraper.py` | ⚠️ Sélecteurs à remplir |
| `Functions/Bookmakers/StakeScraper.py` | ⚠️ Cloudflare + sélecteurs à remplir |
| `Functions/Bookmakers/_test_winamax_bet.py` | Test Winamax |
| `SCRIPTS_WATCH/main-1.py` | Script principal |

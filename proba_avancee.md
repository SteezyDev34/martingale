# 🧠 Tennis Prediction Bot — Documentation Technique Complète

Auteur : Documentation technique  
Langage : Python  
Source de données : SofaScore API  
Type de modèle : **Simulation probabiliste + Markov Chain**

---

# 1. Objectif du bot

Ce bot a pour objectif de **calculer la probabilité que certains événements apparaissent dans un match de tennis**.

Ces probabilités sont utiles pour analyser :

- les marchés de paris
- les stratégies de trading
- les modèles statistiques

---

# 2. Philosophie du modèle

Le modèle repose sur un principe fondamental :

> Un match de tennis peut être modélisé comme une succession de **points indépendants probabilistes**.

Chaque point possède une probabilité :

```
P(point gagné par le serveur)
```

À partir de cette probabilité, on peut simuler :

```
point → jeu → set → match
```

---

# 3. Architecture du système

```
            SofaScore API
                 │
                 ▼
        Collecte des données
                 │
        ┌────────┴────────┐
        ▼                 ▼
   Stats joueurs      Point-by-point
        │                 │
        ▼                 ▼
   Calcul probabilité point
                 │
                 ▼
         Modèle Markov tennis
                 │
                 ▼
          Simulation du match
                 │
                 ▼
       Détection des événements
                 │
                 ▼
      Fusion avec historique réel
                 │
                 ▼
          Probabilités finales
```

---

# 4. API utilisées

Le bot utilise plusieurs endpoints SofaScore.

---

# 4.1 Matchs en direct

```
https://www.sofascore.com/api/v1/sport/tennis/events/live
```

Renvoie :

- matchs en cours
- joueurs
- identifiant match
- identifiant H2H

---

# 4.2 Statistiques des joueurs

```
/api/v1/team/{id}/statistics/overall
```

Données récupérées :

| variable                | description                |
|-------------------------|----------------------------|
 firstServeTotal         | nombre de premières balles |
 totalServeAttempts      | total services             |
 firstServePointsScored  | points gagnés 1ère balle   |
 secondServePointsScored | points gagnés 2e balle     |

---

# 4.3 Historique des matchs

```
/api/v1/team/{id}/events/last/0
```

Utilisé pour :

```
fatigue
historique point-by-point
```

---

# 4.4 Point-by-point

```
/api/v1/event/{id}/point-by-point
```

Contient :

```
liste des jeux
liste des points
score après chaque point
```

Exemple :

```
15-0
15-15
30-15
30-30
40-30
```

---

# 4.5 H2H

```
/api/v1/event/{customId}/h2h/events
```

Le bot utilise uniquement :

```
matchs des 2 dernières années
```

---

# 5. Modélisation mathématique

## Probabilité de gagner un point

La probabilité de gagner un point au service est estimée par :

```
P = 0.50 × service
  + 0.35 × (1 − retour)
  + 0.15 × H2H
```

Puis corrigée par la fatigue.

---

# 6. Modèle Markov tennis

Un jeu de tennis peut être représenté par une **chaîne de Markov**.

Les états possibles :

```
0-0
15-0
0-15
15-15
30-15
15-30
30-30
40-30
30-40
40-40
A-40
40-A
```

Transitions :

```
P(serveur gagne point) = p
P(retourneur gagne point) = 1 − p
```

---

# 7. Simulation Markov

Chaque point est simulé avec :

```python
random.random() < p
```

Si vrai :

```
serveur gagne le point
```

Sinon :

```
retourneur gagne le point
```

---

# 8. Fin d'un jeu

Un jeu se termine lorsque :

```
≥4 points
ET
2 points d'écart
```

Exemples :

```
40-15
40-30
A-40
```

---

# 9. Simulation d'un match

Structure :

```
jeu → set → match
```

Le match se joue en :

```
2 sets gagnants
```

Le serveur alterne :

```
A B A B A B
```

---

# 10. Événements détectés

Le bot détecte si un jeu atteint :

```
15-0
0-15
15-15
30-30
40-40
30-0
0-30
40-0
0-40
40-15
15-40
```

---

# 11. Événements après 3 points

Après 3 points :

```
30-15
15-30
```

Ces marchés existent chez certains bookmakers.

---

# 12. Longueur des jeux

Le bot calcule aussi :

```
jeu en 4 points
jeu en 5 points
jeu en 6 points
```

---

# 13. Simulation Monte Carlo

Le match est simulé :

```
SIM_MATCHES = 8000
```

Plus il y a de simulations :

```
plus la probabilité est précise
```

---

# 14. Calcul des probabilités

Pour chaque événement :

```
probabilité =
nombre simulations où l'événement apparaît
-------------------------------------------
nombre total simulations
```

---

# 15. Historique réel

Le bot analyse les **5 derniers matchs**.

Il reconstruit les jeux pour mesurer :

```
fréquence 30-30
fréquence deuce
fréquence 40-0
```

---

# 16. Fusion simulation + historique

Formule :

```
probabilité finale =
0.7 × simulation
+
0.3 × historique
```

Pourquoi ?

La simulation donne :

```
modèle théorique
```

L'historique donne :

```
réalité du joueur
```

---

# 17. Exemple de sortie

```
MATCH sinner-alcaraz

15_0 = 0.998
0_15 = 0.998
30_30 = 0.94
40_40 = 0.71
40_0 = 0.63
0_40 = 0.52
game4 = 0.58
game5 = 0.81
game6 = 0.89
```

---

# 18. Interprétation

```
30_30 = 0.94
```

signifie :

```
94% de chance qu'un jeu atteigne 30-30 dans le match
```

---

# 19. Forces du modèle

Ce modèle utilise :

```
statistiques joueurs
point-by-point réel
simulation Markov
historique matchs
fatigue
H2H
```

C'est proche des modèles utilisés en **trading tennis**.

---

# 20. Améliorations possibles

Pour améliorer encore le modèle :

### vitesse du court

```
surface rapide = moins de break
```

---

### pression des break points

certains joueurs sont :

```
clutch
```

---

### importance du tournoi

un joueur joue différemment en :

```
grand chelem
```

---

# 21. Limites du modèle

Comme tout modèle probabiliste :

```
il ne prédit pas le futur avec certitude
```

Il donne seulement :

```
une probabilité
```

---

# 22. Conclusion

Ce bot est un **modèle probabiliste avancé pour le tennis**.

Il combine :

```
statistiques
historique réel
simulation mathématique
```

pour estimer la probabilité de nombreux événements dans un match.

Ce type de système est utilisé dans :

```
trading sportif
modélisation tennis
analyse statistique
```

---

# Fin de la documentation
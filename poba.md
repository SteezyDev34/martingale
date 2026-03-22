# 📊 Tennis Probability Bot – Documentation Complète

## Objectif du bot

Ce bot Python analyse les matchs de tennis via l'API **SofaScore** et calcule la probabilité que certains événements se
produisent **au moins une fois dans un match**.

Les probabilités sont obtenues en combinant :

- Modèle **Markov tennis (simulation point par point)**
- **Statistiques de service**
- **Statistiques de retour**
- **Historique point-by-point**
- **Fatigue des joueurs**
- **Historique des confrontations (H2H)**
- **Corrélation des jeux serrés**

Le bot simule ensuite **plusieurs milliers de matchs** afin d'estimer les probabilités.

---

# Architecture générale

Le pipeline du modèle est le suivant :

```
API SofaScore
      │
      ├── statistiques joueur
      ├── historique des matchs
      ├── point-by-point
      ├── confrontations H2H
      │
      ▼
Calcul probabilité de gagner un point
      │
      ▼
Simulation Markov du jeu
      │
      ▼
Simulation du match complet
      │
      ▼
Fusion avec historique réel
      │
      ▼
Probabilité finale des événements
```

---

# Événements calculés

Le bot calcule la probabilité qu'un événement apparaisse **au moins une fois dans le match**.

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
score 30-15 après 3 points
score 15-30 après 3 points
jeu en 4 points
jeu en 5 points
jeu en 6 points
```

---

# Paramètres principaux

```python
SIM_MATCHES = 8000
```

Nombre de matchs simulés pour calculer les probabilités.

Plus ce nombre est élevé :

- plus la précision augmente
- mais plus le calcul est long

---

# API SofaScore utilisées

## Matchs en direct

```
https://www.sofascore.com/api/v1/sport/tennis/events/live
```

Permet d'obtenir :

- les matchs en cours
- les joueurs
- l'identifiant du match

---

## Statistiques des joueurs

```
https://www.sofascore.com/api/v1/team/{player_id}/statistics/overall
```

Données récupérées :

- pourcentage première balle
- points gagnés sur première balle
- points gagnés sur seconde balle

Ces données servent à calculer la **force au service**.

---

## Historique des matchs

```
https://www.sofascore.com/api/v1/team/{player_id}/events/last/0
```

Permet de récupérer :

- les derniers matchs
- la date du dernier match
- l'adversaire

Ces données servent à calculer :

- fatigue
- performances récentes

---

## Point-by-point

```
https://www.sofascore.com/api/v1/event/{event_id}/point-by-point
```

C'est la donnée la plus importante.

Elle permet d'obtenir :

- chaque point joué
- l'évolution du score

Exemple :

```
15-0
15-15
30-15
30-30
```

Cela permet de reconstruire **tous les jeux du match**.

---

## Confrontations H2H

```
https://www.sofascore.com/api/v1/event/{custom_id}/h2h/events
```

Le bot utilise uniquement :

- les confrontations des **2 dernières années**
- seulement si **au moins 2 matchs**

---

# Calcul de la force au service

Fonction :

```python
service_strength(stats)
```

Cette fonction calcule la probabilité moyenne de gagner un point au service.

Formule :

```
P(point gagné au service) =
P(première balle in) × P(point gagné première balle)
+
P(seconde balle) × P(point gagné seconde balle)
```

Exemple :

```
first_in = 0.62
first_win = 0.73
second_win = 0.52
```

```
P = 0.62 × 0.73 + 0.38 × 0.52
```

---

# Calcul de la force en retour

Fonction :

```python
return_strength(events)
```

Le bot analyse les **5 derniers matchs**.

Pour chaque point :

```
awayPointType == 1
```

signifie que le joueur **gagne le point en retour**.

La probabilité est :

```
points gagnés en retour / total points
```

---

# Calcul de la fatigue

Fonction :

```python
fatigue_factor(events)
```

Le bot compare :

```
date actuelle
date du dernier match
```

Règles :

| jours de repos | facteur |
|----------------|---------|
 <1             | 0.95    |
 1-3            | 1       |
 >3             | 1.02    |

---

# Analyse historique des jeux

Fonction :

```
game_profile(events)
```

Le bot reconstruit chaque jeu à partir du point-by-point.

Exemple :

```
15-0
15-15
30-15
30-30
40-30
```

Les états rencontrés sont comptés :

```
30-30
40-40
30-0
0-30
```

Puis divisés par le nombre total de jeux.

Cela donne la **distribution historique des scores de jeu**.

---

# Calcul de la probabilité de gagner un point

Fonction :

```
point_probability()
```

Le modèle combine :

```
service strength
retour adversaire
H2H
fatigue
```

Formule :

```
p = 0.50 × service
  + 0.35 × (1 - retour)
  + 0.15 × H2H
```

Puis :

```
p = p × fatigue
```

La probabilité est ensuite bornée :

```
0.45 ≤ p ≤ 0.75
```

Cela évite les valeurs irréalistes.

---

# Modèle Markov tennis

Fonction :

```
simulate_game(p)
```

Le jeu est simulé **point par point**.

À chaque point :

```
random.random() < p
```

si vrai → le serveur gagne le point.

Sinon → le retourneur gagne.

---

## États détectés

Pendant la simulation :

```
15-0
0-15
15-15
30-30
40-40
```

sont enregistrés.

---

# Fin du jeu

Le jeu s'arrête lorsque :

```
≥4 points
et 2 points d'écart
```

Exemples :

```
40-15
40-30
A-40
```

---

# Simulation d'un match

Fonction :

```
simulate_match(pA, pB)
```

Le serveur alterne entre les joueurs.

Chaque jeu appelle :

```
simulate_game()
```

Le match s'arrête lorsque :

```
2 sets gagnants
```

---

# Calcul des probabilités

Fonction :

```
compute_probabilities()
```

Le match est simulé :

```
SIM_MATCHES fois
```

Chaque événement est compté.

Puis :

```
probabilité = compteur / nombre simulations
```

---

# Fusion avec l'historique réel

Le modèle combine :

```
Markov simulation
+
historique point-by-point
```

Formule :

```
prob_finale =
0.7 × simulation
+
0.3 × historique
```

Cela stabilise les résultats.

---

# Scanner automatique des matchs

Fonction :

```
scan_matches()
```

Le bot :

1. récupère les matchs en direct
2. analyse chaque match
3. calcule les probabilités
4. affiche les résultats

Exemple de sortie :

```
MATCH sinner-alcaraz

30_30 0.94
40_40 0.72
40_0 0.61
0_40 0.48
game4 0.54
game5 0.79
game6 0.88
```

---

# Interprétation

Exemple :

```
30_30 = 0.94
```

signifie :

```
94% de chance qu'un jeu atteigne 30-30 dans le match
```

---

# Forces du modèle

Ce bot utilise :

- données réelles point-by-point
- statistiques joueurs
- simulation Markov
- historique des matchs
- fatigue
- H2H

Ce type de modèle est proche des systèmes utilisés en **trading tennis**.

---

# Améliorations possibles

Pour améliorer encore le modèle :

- vitesse du court
- style du joueur
- pression des break points
- importance du tournoi
- classement ATP/WTA

---

# Conclusion

Ce bot est un **modèle probabiliste avancé pour le tennis**.

Il permet de prédire la probabilité que différents **événements de jeu** apparaissent dans un match.

Grâce à la combinaison :

```
statistiques
historique
simulation
```

il produit des probabilités réalistes pour analyser les matchs.

---
# 🧠 Advanced Tennis Probability Engine

## Documentation mathématique et technique complète

Auteur : Documentation technique avancée  
Langage : Python  
Type de modèle : Simulation probabiliste + Chaîne de Markov + Monte Carlo

---

# 1. Introduction

Ce projet implémente un **moteur probabiliste pour analyser les matchs de tennis**.

L'objectif est de calculer :

```
P(événement dans le match)
```

pour différents événements de score.

Exemples :

```
30-30 apparaît dans un jeu
40-40 apparaît dans un jeu
40-0 apparaît
score après 3 points
```

---

# 2. Philosophie du modèle

Un match de tennis peut être modélisé comme une succession de :

```
points → jeux → sets → match
```

Chaque point possède une probabilité :

```
P = probabilité que le serveur gagne le point
```

À partir de cette probabilité, nous pouvons simuler :

```
point → jeu → set → match
```

---

# 3. Architecture globale du moteur

```
                   SofaScore API
                        │
                        ▼
              Extraction des données
                        │
        ┌───────────────┼───────────────┐
        ▼                               ▼
   statistiques service           point-by-point
        │                               │
        ▼                               ▼
    calcul force serveur          analyse historique
        │                               │
        └──────────────┬────────────────┘
                       ▼
           probabilité de gagner un point
                       │
                       ▼
               modèle Markov tennis
                       │
                       ▼
            simulation Monte Carlo
                       │
                       ▼
         probabilité des événements
```

---

# 4. Données utilisées

Le modèle combine plusieurs sources.

---

# 4.1 Statistiques service

API :

```
/api/v1/team/{player_id}/statistics/overall
```

Données utilisées :

| Statistique             | Description                |
|-------------------------|----------------------------|
 firstServeTotal         | nombre de premières balles |
 totalServeAttempts      | total services             |
 firstServePointsScored  | points gagnés 1ère balle   |
 secondServePointsScored | points gagnés 2e balle     |

---

# 4.2 Point-by-point

API :

```
/api/v1/event/{event_id}/point-by-point
```

Permet de reconstruire chaque jeu.

Exemple :

```
0-0
15-0
15-15
30-15
30-30
40-30
```

---

# 4.3 Historique des matchs

API :

```
/team/{id}/events/last/0
```

Utilisé pour :

```
fatigue
analyse des jeux
```

---

# 4.4 Confrontations H2H

API :

```
/event/{customId}/h2h/events
```

Le modèle filtre :

```
matchs des 2 dernières années
```

et nécessite :

```
≥ 2 matchs
```

---

# 5. Calcul de la probabilité de gagner un point

La probabilité de gagner un point est estimée par :

```
P = 0.50 × service
  + 0.35 × (1 − retour)
  + 0.15 × H2H
```

Puis ajustée par :

```
fatigue
```

Ensuite bornée :

```
0.45 ≤ P ≤ 0.75
```

---

# 6. Chaîne de Markov du tennis

Un jeu de tennis peut être représenté par une **chaîne de Markov**.

États possibles :

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

---

# 7. Matrice de transition

Exemple pour l'état :

```
30-30
```

Transitions possibles :

```
serveur gagne → 40-30
retourneur gagne → 30-40
```

Probabilités :

```
P(40-30) = p
P(30-40) = 1 − p
```

---

# 8. Simulation d'un point

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
retourneur gagne
```

---

# 9. Fin d'un jeu

Un jeu se termine lorsque :

```
≥ 4 points
et
2 points d'écart
```

Exemples :

```
40-15
40-30
A-40
```

---

# 10. Simulation d'un match

Structure :

```
jeu → set → match
```

Match standard :

```
2 sets gagnants
```

Le serveur alterne :

```
A B A B A B
```

---

# 11. Simulation Monte Carlo

Le match est simulé :

```
8000 fois
```

Chaque simulation produit :

```
une séquence de jeux
```

et on détecte si les événements apparaissent.

---

# 12. Calcul des probabilités

Formule :

```
probabilité =
nombre simulations où événement apparaît
-----------------------------------------
nombre total simulations
```

---

# 13. Analyse historique des jeux

Le bot reconstruit les jeux des **5 derniers matchs**.

Il mesure :

```
fréquence 30-30
fréquence 40-40
fréquence 40-0
```

---

# 14. Fusion historique + simulation

Formule :

```
prob_finale =
0.7 × simulation
+
0.3 × historique
```

Pourquoi ?

Simulation = théorie  
Historique = réalité

---

# 15. Événements calculés

Le moteur calcule :

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
30-15 après 3 points
15-30 après 3 points
jeu en 4 points
jeu en 5 points
jeu en 6 points
```

---

# 16. Exemple de sortie

```
MATCH djokovic-alcaraz

15_0 0.998
0_15 0.998
30_30 0.94
40_40 0.72
40_0 0.63
0_40 0.54
game4 0.58
game5 0.80
game6 0.89
```

---

# 17. Interprétation

```
30_30 = 0.94
```

signifie :

```
94% de chance qu'un jeu atteigne 30-30 dans le match
```

---

# 18. Optimisation du modèle

Pour améliorer la précision :

### surface

```
terre battue → plus de breaks
gazon → plus de services gagnants
```

---

### pression des points

Certains joueurs sont meilleurs sur :

```
break points
deuce
```

---

### forme du joueur

Mesurable via :

```
10 derniers matchs
```

---

# 19. Comment atteindre 95% de précision

Les modèles professionnels utilisent :

```
Markov analytique
+
machine learning
+
base de données complète
```

Données supplémentaires :

```
classement
vitesse du court
conditions météo
style du joueur
```

---

# 20. Limites du modèle

Un modèle probabiliste ne donne jamais :

```
une certitude
```

mais seulement :

```
une probabilité
```

---

# 21. Conclusion

Ce moteur combine :

```
statistiques
historique réel
simulation mathématique
```

pour produire des probabilités fiables sur les événements d'un match de tennis.

Ce type de modèle est utilisé dans :

```
trading sportif
modélisation tennis
analyse statistique avancée
```

---

# Fin de la documentation
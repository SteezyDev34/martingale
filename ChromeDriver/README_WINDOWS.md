# 🪟 Gestion des Fenêtres Chrome Multiples

Ce module permet de contrôler une fenêtre Chrome spécifique lorsque plusieurs fenêtres sont ouvertes sur le même port de debugging.

## 🚀 Utilisation Rapide

### 1. Lancer Chrome avec debugging

```bash
# macOS / Linux
open -na "Google Chrome" --args --remote-debugging-port=43151 --user-data-dir="$HOME/ChromeDebugProfile43151"

# Windows
start chrome --remote-debugging-port=43151 --user-data-dir="%USERPROFILE%\ChromeDebugProfile43151"
```

### 2. Ouvrir plusieurs onglets/fenêtres

Ouvrez autant de fenêtres que nécessaire dans ce navigateur Chrome.

### 3. Utiliser SetDriver1.py

```python
from ChromeDriver.SetDriver1 import driver

# Le script détectera automatiquement les fenêtres multiples
# et vous proposera de choisir
```

## 📋 Modes de Sélection

### Mode 1 : Interface Interactive Complète

- Affiche toutes les fenêtres avec détails complets
- Permet de rechercher par URL, titre ou index
- Le plus flexible mais nécessite plus d'interactions

### Mode 2 : Recherche Automatique par URL

- Recherche automatiquement une fenêtre contenant "1xbet" dans l'URL
- Rapide si vous travaillez toujours sur le même site
- Fallback vers sélection manuelle si non trouvé

### Mode 3 : Sélection Manuelle Rapide (Défaut)

- Liste toutes les fenêtres avec numéros
- Vous choisissez par numéro
- Simple et rapide

### Mode 4 : Première Fenêtre

- Utilise automatiquement la première fenêtre
- Aucune interaction requise

## 🔧 Configuration Automatique

Pour éviter de choisir à chaque fois, configurez une sélection automatique :

```bash
# Lancer le configurateur
python ChromeDriver/ConfigureWindow.py
```

### Options de configuration :

1. **Par URL** : Recherche une fenêtre contenant un pattern

   ```
   Pattern d'URL: 1xbet
   → Sélectionnera automatiquement la fenêtre avec "1xbet" dans l'URL
   ```

2. **Par titre** : Recherche une fenêtre avec un titre spécifique

   ```
   Pattern de titre: Paris Sportifs
   → Sélectionnera la fenêtre dont le titre contient "Paris Sportifs"
   ```

3. **Par index** : Utilise toujours la même fenêtre (0, 1, 2...)
   ```
   Index: 1
   → Utilisera toujours la deuxième fenêtre (index 1)
   ```

La configuration est sauvegardée dans `ChromeDriver/window_config.json`.

## 🔍 Utilisation Programmatique

### Sélection de fenêtre dans vos scripts

```python
from ChromeDriver.WindowManager import (
    list_chrome_windows,
    select_window_by_url,
    select_window_by_title,
    select_window_by_index
)

# Lister toutes les fenêtres
windows = list_chrome_windows(driver)
for w in windows:
    print(f"{w['index']}: {w['title']} - {w['url']}")

# Sélectionner par URL
if select_window_by_url(driver, "1xbet"):
    print("Fenêtre 1xbet sélectionnée")

# Sélectionner par titre
if select_window_by_title(driver, "Paris"):
    print("Fenêtre trouvée")

# Sélectionner par index
select_window_by_index(driver, 1)  # Deuxième fenêtre
```

### Sélection automatique avec fallback

```python
from ChromeDriver.WindowManager import auto_select_window

# Essayer par URL, sinon par index
if not auto_select_window(driver, url_pattern="1xbet"):
    auto_select_window(driver, index=0)  # Fallback première fenêtre
```

## 📝 Exemples d'Utilisation

### Exemple 1 : Bot avec fenêtre 1xbet dédiée

```python
from ChromeDriver.SetDriver1 import driver
from ChromeDriver.WindowManager import select_window_by_url

# Sélectionner automatiquement la fenêtre 1xbet
select_window_by_url(driver, "1xbet")

# Continuer avec votre script...
driver.get("https://1xbet.com/fr/line")
```

### Exemple 2 : Surveillance de plusieurs sites

```python
from ChromeDriver.SetDriver1 import driver
from ChromeDriver.WindowManager import list_chrome_windows, select_window_by_index

windows = list_chrome_windows(driver)

for i, window in enumerate(windows):
    select_window_by_index(driver, i)
    print(f"Surveillance de: {driver.current_url}")
    # Faire des vérifications...
```

### Exemple 3 : Configuration persistante

```python
# Une seule fois : configurer
from ChromeDriver.ConfigureWindow import save_window_preference

# Toujours utiliser la fenêtre avec "1xbet" dans l'URL
save_window_preference(url_pattern="1xbet")

# Maintenant, chaque fois que vous utilisez SetDriver1,
# la bonne fenêtre sera automatiquement sélectionnée !
```

## 🛠️ Résolution de Problèmes

### "WindowManager non disponible"

Le module WindowManager n'a pas pu être importé. Vérifiez que le fichier existe :

```bash
ls ChromeDriver/WindowManager.py
```

### Fenêtre non trouvée avec pattern

- Vérifiez que la fenêtre est bien ouverte
- Le pattern est sensible à la casse (utilisez des minuscules)
- Essayez un pattern plus court : "1xbet" au lieu de "1xbet.com/fr/line"

### Configuration ignorée

La configuration est ignorée si :

- La fenêtre correspondante n'est pas trouvée
- Le fichier `window_config.json` est corrompu
- L'index spécifié dépasse le nombre de fenêtres

Solution : Supprimer la configuration et recommencer

```bash
rm ChromeDriver/window_config.json
python ChromeDriver/ConfigureWindow.py
```

## 📊 Structure des Fichiers

```
ChromeDriver/
├── SetDriver1.py           # Driver principal avec sélection de fenêtre
├── WindowManager.py         # Utilitaires de gestion des fenêtres
├── ConfigureWindow.py       # Script de configuration
└── window_config.json       # Configuration sauvegardée (créé automatiquement)
```

## 💡 Astuces

1. **Nommer vos fenêtres** : Donnez des titres distincts à vos onglets pour faciliter l'identification
2. **Utiliser des profils Chrome différents** : Pour des ports différents
3. **Garder l'ordre** : Les fenêtres gardent généralement le même ordre
4. **Tester avant** : Utilisez mode 3 (manuel) pour identifier le bon index avant de configurer

## 🔗 Intégration avec les Scripts Existants

Le système est rétrocompatible. Si vous avez déjà des scripts utilisant `SetDriver1.py`, ils continueront de fonctionner. La sélection de fenêtre ne s'active que s'il y a plusieurs fenêtres ouvertes.

```python
# Avant (toujours valide)
from ChromeDriver.SetDriver1 import driver

# Après (avec contrôle explicite)
from ChromeDriver.SetDriver1 import driver
from ChromeDriver.WindowManager import select_window_by_url

select_window_by_url(driver, "1xbet")
```

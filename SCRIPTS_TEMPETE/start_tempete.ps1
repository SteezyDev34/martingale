# Script de lancement de tempeteBetting.py avec affichage en temps réel
# L'option -u force Python à ne pas mettre en buffer les sorties

Write-Host "🚀 Démarrage de tempeteBetting.py avec affichage en temps réel..." -ForegroundColor Green
Write-Host ""

# Définir la variable d'environnement pour désactiver le buffering
$env:PYTHONUNBUFFERED = "1"

# Lancer le script Python avec l'option -u (unbuffered)
python -u ".\tempeteBetting.py"

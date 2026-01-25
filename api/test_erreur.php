<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/config.php';

// Tester l'affichage des erreurs
echo "<h1>Test d'affichage des erreurs PHP</h1>";

// Générer une erreur de niveau notice
$variable_non_definie;
echo "Si vous voyez cette erreur concernant une variable non définie, l'affichage des erreurs fonctionne correctement.<br>";

// Générer une erreur de niveau warning
echo "Test d'une erreur de type warning : " . file_get_contents('fichier_inexistant.txt') . "<br>";

// Tester la connexion à la base de données
$conn = getDbConnection();
echo "Connexion à la base de données réussie.";
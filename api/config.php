<?php

// Activer l'affichage des erreurs pour le développement
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);

// Charger les variables d'environnement depuis .env si présent
function loadEnvFile(string $path)
{
    if (!file_exists($path)) {
        return;
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        if (!strpos($line, '=')) continue;
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        if ((substr($value, 0, 1) === '"' && substr($value, -1) === '"') || (substr($value, 0, 1) === "'" && substr($value, -1) === "'")) {
            $value = substr($value, 1, -1);
        }
        putenv("{$name}={$value}");
        $_ENV[$name] = $value;
        $_SERVER[$name] = $value;
    }
}

$envPath = __DIR__ . '/.env';
loadEnvFile($envPath);

// Exposer quelques aliases d'environnement au code existant
$servername = getenv('DB_HOST') ?: 'localhost';
$username = getenv('DB_USER') ?: '';
$password = getenv('DB_PASS') ?: '';
$database = getenv('DB_NAME') ?: '';
$host = $servername;
$dbname = $database;

// Shim de compatibilité : délègue les appels mysqli-legacy à la couche PDO-compat
require_once __DIR__ . '/src/DbCompat.php';

// Remarque : `src/DbCompat.php` fournit une fonction `getDbConnection()` et
// une interface minimale compatible mysqli. Cela permet de supprimer
// progressivement l'ancienne logique contenue ici sans casser les scripts.

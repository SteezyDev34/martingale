<?php

/**
 * Script pour mettre à jour tous les fichiers PHP dans les dossiers de stratégie
 * afin d'utiliser le fichier de configuration commun pour la connexion à la base de données.
 */

// Liste des dossiers de stratégie à mettre à jour
$strategyFolders = [
    'strategy4P',
    'strategy5P',
    'strategy6P',
    'strategy15A',
    'strategy030',
    'strategy30A',
    'strategy40A',
    'strategy300',
    'strategy400',
    'strategy456P',
    'strategy4015',
    'strategy4030',
    'strategy4315A',
    'strategyBREAK',
    'strategyQT',
    'strategyQTV2'
];

// Motif à rechercher (connexion à la base de données codée en dur)
$searchPattern = [
    '/\/\/\s*Configurer les paramètres de la base de données\s*\n\s*\$servername\s*=\s*"pcomstd757\.mysql\.db";\s*\n\s*\$username\s*=\s*"pcomstd757";\s*\n\s*\$password\s*=\s*"RgzQzGkXvsMK";\s*\n\s*\$database\s*=\s*"pcomstd757";\s*\n\s*\/\/\s*Créer une connexion à la base de données\s*\n\s*\$conn\s*=\s*new mysqli\(\$servername,\s*\$username,\s*\$password,\s*\$database\);\s*\n\s*\/\/\s*Vérifier la connexion\s*\n\s*if\s*\(\$conn->connect_error\)\s*{[^}]*}/s',
    '/\/\/\s*Configurer les paramètres de la base de données\s*\n\s*\$servername\s*=\s*"pcomstd757\.mysql\.db";\s*\n\s*\$username\s*=\s*"pcomstd757";\s*\n\s*\$password\s*=\s*"RgzQzGkXvsMK";\s*\n\s*\$database\s*=\s*"pcomstd757";\s*\n\s*\/\/\s*Connexion à la base de données\s*\n\s*\$conn\s*=\s*new mysqli\(\$servername,\s*\$username,\s*\$password,\s*\$database\);\s*\n\s*\/\/\s*Vérifier la connexion\s*\n\s*if\s*\(\$conn->connect_error\)\s*{[^}]*}/s',
    '/\/\/\s*Configurer les paramètres de la base de données\s*\n\s*\$servername\s*=\s*"pcomstd757\.mysql\.db";\s*\n\s*\$username\s*=\s*"pcomstd757";\s*\n\s*\$password\s*=\s*"RgzQzGkXvsMK";\s*\n\s*\$database\s*=\s*"pcomstd757";\s*\n\s*\/\/\s*Créer une connexion à la base de données\s*\n\s*\$conn\s*=\s*new mysqli\(\$servername,\s*\$username,\s*\$password,\s*\$database\);\s*\n\s*\/\/\s*Vérifier la connexion\s*\n\s*if\s*\(\$conn->connect_error\)\s*{[^}]*}\s*\n\s*if\s*\(!\$conn->set_charset\("utf8"\)\)\s*{[^}]*}/s',
    '/ini_set\(\s*\'display_errors\',\s*1\s*\);\s*\n\s*error_reporting\(\s*E_ALL\s*\);\s*\/\/\s*Configurer les paramètres de la base de données\s*\n\s*\$servername\s*=\s*"pcomstd757\.mysql\.db";\s*\n\s*\$username\s*=\s*"pcomstd757";\s*\n\s*\$password\s*=\s*"RgzQzGkXvsMK";\s*\n\s*\$database\s*=\s*"pcomstd757";\s*\n\s*\/\/\s*Créer une connexion à la base de données\s*\n\s*\$conn\s*=\s*new mysqli\(\$servername,\s*\$username,\s*\$password,\s*\$database\);\s*\n\s*\/\/\s*Vérifier la connexion\s*\n\s*if\s*\(\$conn->connect_error\)\s*{[^}]*}\s*\n\s*if\s*\(!\$conn->set_charset\("utf8"\)\)\s*{[^}]*}/s'
];

// Motif de remplacement (utilisation du fichier de configuration)
$replacementPatterns = [
    "// Inclure le fichier de configuration\nrequire_once __DIR__ . '/../../config.php';\n\n// Obtenir la connexion à la base de données\n\$conn = getDbConnection();",
    "// Inclure le fichier de configuration\nrequire_once __DIR__ . '/../../config.php';\n\n// Obtenir la connexion à la base de données\n\$conn = getDbConnection();",
    "// Inclure le fichier de configuration\nrequire_once __DIR__ . '/../../config.php';\n\n// Obtenir la connexion à la base de données\n\$conn = getDbConnection();",
    "ini_set( 'display_errors', 1 );\nerror_reporting( E_ALL );\n// Inclure le fichier de configuration\nrequire_once __DIR__ . '/../../config.php';\n\n// Obtenir la connexion à la base de données\n\$conn = getDbConnection();"
];

// Compteurs pour les statistiques
$totalFiles = 0;
$modifiedFiles = 0;
$errorFiles = [];

// Parcourir chaque dossier de stratégie
foreach ($strategyFolders as $folder) {
    $folderPath = __DIR__ . '/' . $folder;
    
    // Vérifier si le dossier existe
    if (!is_dir($folderPath)) {
        echo "Le dossier {$folder} n'existe pas. Ignoré.\n";
        continue;
    }
    
    // Récupérer tous les fichiers PHP dans le dossier
    $phpFiles = glob($folderPath . '/*.php');
    
    foreach ($phpFiles as $file) {
        $totalFiles++;
        $fileContent = file_get_contents($file);
        $originalContent = $fileContent;
        $modified = false;
        
        // Essayer chaque motif de recherche
        foreach ($searchPattern as $index => $pattern) {
            if (preg_match($pattern, $fileContent)) {
                $fileContent = preg_replace($pattern, $replacementPatterns[$index], $fileContent, 1, $count);
                if ($count > 0) {
                    $modified = true;
                }
            }
        }
        
        // Si le fichier a été modifié, l'enregistrer
        if ($modified && $fileContent !== $originalContent) {
            if (file_put_contents($file, $fileContent)) {
                $modifiedFiles++;
                echo "Fichier modifié avec succès: {$file}\n";
            } else {
                $errorFiles[] = $file;
                echo "Erreur lors de la modification du fichier: {$file}\n";
            }
        } else {
            echo "Aucune modification nécessaire pour: {$file}\n";
        }
    }
}

// Afficher les statistiques
echo "\n=== Rapport de mise à jour ===\n";
echo "Total des fichiers traités: {$totalFiles}\n";
echo "Fichiers modifiés avec succès: {$modifiedFiles}\n";
echo "Fichiers avec erreurs: " . count($errorFiles) . "\n";

if (count($errorFiles) > 0) {
    echo "\nListe des fichiers avec erreurs:\n";
    foreach ($errorFiles as $file) {
        echo "- {$file}\n";
    }
}

echo "\nMise à jour terminée!\n";
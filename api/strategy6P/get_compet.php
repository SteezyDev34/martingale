<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
// Inclure la compat PDO/mysqli
require_once __DIR__ . '/../src/DbCompat.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();
if (!$conn->set_charset("utf8")) {
    printf("Erreur lors du chargement du jeu de caractères utf8 : %s\n", $conn->error);
    exit();
}
// Préparer la requête SQL
$sql = "SELECT compet_ok, compet_not_ok FROM 0_compet6P";

// Exécuter la requête SQL
$result = $conn->query($sql);

// Préparer les données pour JSON
$column1_data = array();
$column2_data = array();
if ($result->num_rows > 0) {
    // Parcourir les résultats et ajouter chaque valeur de colonne aux tableaux respectifs
    while ($row = $result->fetch_assoc()) {
        // Convertir les données en UTF-8 si nécessaire
        if (isset($row['compet_ok']) && $row['compet_ok'] != "") {
            $compet_ok = $row['compet_ok'];
            // S'assurer que les données sont bien encodées en UTF-8
            if (!mb_check_encoding($compet_ok, 'UTF-8')) {
                $compet_ok = utf8_encode($compet_ok);
            }


            $column1_data[] = $compet_ok;
        }
        if (isset($row['compet_not_ok']) && $row['compet_not_ok'] != "") {
            $compet_not_ok = $row['compet_not_ok'];
            // S'assurer que les données sont bien encodées en UTF-8
            if (!mb_check_encoding($compet_not_ok, 'UTF-8')) {
                $compet_not_ok = utf8_encode($compet_not_ok);
            }

            $column2_data[] = $compet_not_ok;
        }
    }
}

// Fermer la connexion
$conn->close();
// Préparer la réponse JSON
$response = array(
    "compet_ok" => $column1_data,
    "compet_not_ok" => $column2_data
);

// Définir le type de contenu comme JSON
header('Content-Type: application/json; charset=utf-8');
// Encoder en JSON et vérifier les erreurs
$json_response = json_encode($response);
if (json_last_error() !== JSON_ERROR_NONE) {
    echo "Erreur d'encodage JSON: " . json_last_error_msg();
    exit();
}
// Retourner les données en JSON
echo $json_response;

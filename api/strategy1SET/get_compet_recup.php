<?php

// Configurer les paramètres de la base de données
$servername = "pcomstd757.mysql.db";
$username = "pcomstd757";
$password = "RgzQzGkXvsMK";
$database = "pcomstd757";

// Créer une connexion à la base de données
$conn = new mysqli($servername, $username, $password, $database);

// Vérifier la connexion
if ($conn->connect_error) {
    die("Échec de la connexion : " . $conn->connect_error);
}
if (!$conn->set_charset("utf8")) {
    printf("Erreur lors du chargement du jeu de caractères utf8 : %s\n", $conn->error);
    exit();
}
// Préparer la requête SQL
$sql = "SELECT compet_recup_ok, compet_recup_not_ok FROM 0_compet_recup1SET";

// Exécuter la requête SQL
$result = $conn->query($sql);

// Préparer les données pour JSON
$column1_data = array();
$column2_data = array();
if ($result->num_rows > 0) {
    // Parcourir les résultats et ajouter chaque valeur de colonne aux tableaux respectifs
    while ($row = $result->fetch_assoc()) {
        // Convertir les données en UTF-8 si nécessaire
        if (isset($row['compet_recup_ok']) && $row['compet_recup_ok'] != "") {
            $compet_recup_ok = $row['compet_recup_ok'];
            // S'assurer que les données sont bien encodées en UTF-8
            if (!mb_check_encoding($compet_recup_ok, 'UTF-8')) {
                $compet_recup_ok = utf8_encode($compet_recup_ok);
            }


            $column1_data[] = $compet_recup_ok;
        }
        if (isset($row['compet_recup_not_ok']) && $row['compet_recup_not_ok'] != "") {
            $compet_recup_not_ok = $row['compet_recup_not_ok'];
            // S'assurer que les données sont bien encodées en UTF-8
            if (!mb_check_encoding($compet_recup_not_ok, 'UTF-8')) {
                $compet_recup_not_ok = utf8_encode($compet_recup_not_ok);
            }

            $column2_data[] = $compet_recup_not_ok;
        }

    }
}

// Fermer la connexion
$conn->close();
// Préparer la réponse JSON
$response = array(
    "compet_recup_ok" => $column1_data,
    "compet_recup_not_ok" => $column2_data
);
// Fermer la connexion
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


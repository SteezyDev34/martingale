<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();

// Préparer la réponse
$response = array("status" => "error", "message" => "Paramètres d'URL manquants.");

// Vérifier si les paramètres d'URL nécessaires sont définis
if (isset($_GET['perte']) && isset($_GET['ligue']) ) {
    // Récupérer les données des paramètres d'URL
    $perte = $_GET['perte'];
    $ligue = $_GET['ligue'];

    // Préparer la requête SQL
    $stmt = $conn->prepare("INSERT INTO 0_perte1SET (perte, ligue) VALUES (?, ?)");

    if ($stmt) {
        $stmt->bind_param("ds", $perte, $ligue); // d = double, s = string


        // Exécuter la requête
        if ($stmt->execute()) {
            $response = array("status" => "success", "message" => "Données insérées avec succès.");
        } else {
            $response = array("status" => "error", "message" => "Erreur lors de l'insertion des données : " . $stmt->error);
        }

        // Fermer la requête préparée
        $stmt->close();
    } else {
        $response = array("status" => "error", "message" => "Erreur lors de la préparation de la requête : " . $conn->error);
    }
}
else{
    $response = array("status" => "error", "message" => "Pas de données : " . $conn->error);

}

// Fermer la connexion
$conn->close();

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner la réponse en JSON
echo json_encode($response);



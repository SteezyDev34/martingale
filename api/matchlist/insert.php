<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();

// Préparer la réponse
$response = array("status" => "error", "message" => "Paramètres manquants.");

// Vérifie si un paramètre "matches" existe dans l'URL
if (isset($_GET['matches'])) {
    // Récupère la valeur
    $matches = $_GET['matches'];

    // Si c'est un JSON encodé (par ex. depuis urlencode côté client)
    $matches = json_decode($matches, true);

    // Extraire les données du tableau matches
    // Le format reste le même que l'ancien code : [joueurs, ligue, slug, date, proba]
    $players = implode(' - ', $matches[0]);
    $ligue   = $matches[1];
    $slug    = $matches[2];
    $time    = $matches[3];
    $proba   = (float) $matches[4];

    // Préparer la requête SQL avec les champs requis
    $stmt = $conn->prepare("INSERT INTO matchlisttodo (players, ligue, slug, proba, time) VALUES (?, ?, ?, ?, ?)");
    if ($stmt) {
        $stmt->bind_param("sssds", $players, $ligue, $slug, $proba, $time);

        // Exécuter la requête
        if ($stmt->execute()) {
            $response = array("status" => "success", "message" => "Données insérées avec succès.");
        } else {
            $response = array("status" => "error", "message" => "Erreur lors de l'insertion : " . $stmt->error);
        }

        $stmt->close();
    } else {
        $response = array("status" => "error", "message" => "Erreur de préparation : " . $conn->error);
    }
} else {
    $response = array("status" => "error", "message" => "Champ 'matches' manquant.");
}

// Fermer la connexion
$conn->close();

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner la réponse en JSON
echo json_encode($response);

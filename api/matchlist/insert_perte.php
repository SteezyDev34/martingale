<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();

// Préparer la réponse
$response = array("status" => "error", "message" => "Paramètres manquants.");

// Lire le JSON brut depuis le corps de la requête POST
$json = file_get_contents('php://input');
$data = json_decode($json, true);

// Vérifier que le champ 'matches' est présent dans le JSON
if (isset($data['matches'])) {
    $matches = $data['matches'];

    // Vérifier que les champs requis sont présents dans 'matches'
    if (isset($matches['players'], $matches['ligue'], $matches['slug'], $matches['proba'], $matches['time'])) {
        $players = $matches[0];
        $ligue   = $matches[1];
        $slug    = $matches[2];
        $time    = $matches[3]; // au format 'Y-m-d H:i:s'
        $proba   = (float) $matches[4];


        // Préparer la requête SQL
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
        $response = array("status" => "error", "message" => "Champs JSON manquants dans 'matches'.");
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

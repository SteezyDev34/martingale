<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';
// Activer l'affichage des erreurs pour faciliter le débogage
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
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

    // Valider et extraire les données du tableau matches
    // Format attendu : [joueurs(Array|String), ligue, slug, date, proba]
    if (!is_array($matches) || count($matches) < 5) {
        http_response_code(400);
        $response = array("status" => "error", "message" => "Format du paramètre 'matches' invalide.");
    } else {
        $rawPlayers = $matches[0];
        // Normaliser players: si c'est un tableau => implode, si string => utiliser telle quelle
        if (is_array($rawPlayers)) {
            $players = implode(' - ', $rawPlayers);
        } else if (is_string($rawPlayers)) {
            $players = $rawPlayers;
        } else {
            $players = strval($rawPlayers);
        }
        $ligue   = isset($matches[1]) ? strval($matches[1]) : '';
        $slug    = isset($matches[2]) ? strval($matches[2]) : '';
        $time    = isset($matches[3]) ? strval($matches[3]) : '';
        $proba   = isset($matches[4]) ? floatval($matches[4]) : 0.0;

        // Vérifier si l'entrée existe déjà (doublon) via le slug
        $check = $conn->prepare("SELECT 1 FROM matchlisttodo WHERE slug = ? LIMIT 1");
        if ($check) {
            $check->bind_param("s", $slug);
            $check->execute();
            $check->store_result();
            if ($check->num_rows > 0) {
                http_response_code(200);
                $response = array("status" => "exists", "message" => "Match déjà présent.");
                $check->close();
                // Fermer la connexion et retourner immédiatement la réponse
                $conn->close();
                header('Content-Type: application/json');
                echo json_encode($response);
                exit;
            }
            $check->close();
        }

        // Préparer la requête SQL avec les champs requis
        $stmt = $conn->prepare("INSERT INTO matchlisttodo (players, ligue, slug, proba, time) VALUES (?, ?, ?, ?, ?)");
        if ($stmt) {
            $stmt->bind_param("sssds", $players, $ligue, $slug, $proba, $time);

            try {
                // Exécuter la requête
                if ($stmt->execute()) {
                    http_response_code(200);
                    $response = array("status" => "success", "message" => "Données insérées avec succès.");
                }
            } catch (mysqli_sql_exception $e) {
                // Gérer les doublons sans renvoyer une 500
                if ($e->getCode() === 1062) { // Duplicate entry
                    http_response_code(200);
                    $response = array("status" => "exists", "message" => "Match déjà présent.");
                } else {
                    http_response_code(500);
                    $response = array("status" => "error", "message" => "Erreur lors de l'insertion : " . $e->getMessage());
                }
            } finally {
                $stmt->close();
            }
        } else {
            http_response_code(500);
            $response = array("status" => "error", "message" => "Erreur de préparation : " . $conn->error);
        }
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

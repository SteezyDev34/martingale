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
    $response = array("status" => "error", "message" => "Échec de la connexion : " . $conn->connect_error);
    header('Content-Type: application/json');
    echo json_encode($response);
    exit();
}

// Définir l'encodage de la connexion en UTF-8
if (!$conn->set_charset("utf8")) {
    $response = array("status" => "error", "message" => "Erreur lors du chargement du jeu de caractères utf8 : " . $conn->error);
    header('Content-Type: application/json');
    echo json_encode($response);
    exit();
}

// Préparer la réponse par défaut
$response = array("status" => "error", "message" => "Paramètres manquants.", "id" => null);

// Check if all required POST parameters are set
if (isset($_POST['coupon_number']['coupon_number']) && isset($_POST['type_pari'])
    && isset($_POST['mise']) && isset($_POST['gains_potentiels']) && isset($_POST['match_details']) 
    && isset($_POST['cote']) && isset($_POST['script'])) {
    
    // Validate match_details is valid JSON
    $match_details = json_decode($_POST['match_details'], true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        $response = array("status" => "error", "message" => "match_details doit être un JSON valide", "id" => null);
        header('Content-Type: application/json');
        echo json_encode($response);
        exit();
    }

    // Check if match_details contains required fields
    if (!isset($match_details['equipes']) || !isset($match_details['ligue'])) {
        $response = array("status" => "error", "message" => "match_details doit contenir 'equipes' et 'ligue'", "id" => null);
        header('Content-Type: application/json');
        echo json_encode($response);
        exit();
    }

    // Prepare the SQL statement
    $stmt = $conn->prepare("INSERT INTO 0_paris (coupon_number, type_pari, mise, 
        gains_potentiels, match_details, cote, script) 
        VALUES (?, ?, ?, ?, ?, ?, ?)");

    if ($stmt) {
        // Bind parameters
        $stmt->bind_param("sssddssss", 
            $_POST['coupon_number'],
            $_POST['type_pari'],
            $_POST['mise'],
            $_POST['gains_potentiels'],
            $_POST['match_details'],
            $_POST['cote'],
            $_POST['script']
        );

        // Execute the query
        if ($stmt->execute()) {
            $new_id = $conn->insert_id;
            $response = array(
                "status" => "success",
                "message" => "Paris enregistré avec succès",
                "id" => $new_id
            );
        } else {
            $response = array("status" => "error", "message" => "Erreur lors de l'insertion : " . $stmt->error, "id" => null);
        }

        // Close the prepared statement
        $stmt->close();
    } else {
        $response = array("status" => "error", "message" => "Erreur de préparation de la requête : " . $conn->error, "id" => null);
    }
} else {
    $response = array("status" => "error", "message" => $_POST, "id" => null);
}

// Fermer la connexion
$conn->close();

// Définir le type de contenu en JSON et retourner la réponse
header('Content-Type: application/json');
echo json_encode($response);

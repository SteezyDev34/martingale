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
$response = array("status" => "error", "message" => "Paramètres d'URL manquants.");

// Vérifier si le paramètre 'perte' est défini
if (isset($_GET['mise'])) {
    // Récupérer la nouvelle perte reçue
    $nouvelle_mise = $_GET['mise'];

    // Récupérer la dernière valeur enregistrée
    $query_last_perte = "SELECT perte FROM 0_perte ORDER BY id DESC LIMIT 1";
    $result = $conn->query($query_last_perte);

    if ($result && $result->num_rows > 0) {
        $row = $result->fetch_assoc();
        $derniere_perte = $row['perte'];
    } else {
        $derniere_perte=0;
    }
    $nouvelle_perte = floatval($derniere_perte) +floatval($nouvelle_mise);
    $nouvelle_perte = $nouvelle_perte<0?0:$nouvelle_perte;
    // Supprimer toutes les anciennes entrées
    $delete_query = "DELETE FROM 0_perte";
    if ($conn->query($delete_query) === TRUE) {
        // Insérer la nouvelle perte
        $stmt = $conn->prepare("INSERT INTO 0_perte (perte) VALUES (?)");
        if ($stmt) {
            $stmt->bind_param("d", $nouvelle_perte);

            // Exécuter la requête d'insertion
            if ($stmt->execute()) {
                $response = array(
                    "status" => "success",
                    "message" => "Données mises à jour avec succès.",
                    "derniere_perte" => $derniere_perte,
                    "nouvelle_perte" => $nouvelle_perte
                );
            } else {
                $response = array("status" => "error", "message" => "Erreur lors de l'insertion des données : " . $stmt->error);
            }

            // Fermer la requête préparée
            $stmt->close();
        } else {
            $response = array("status" => "error", "message" => "Erreur lors de la préparation de la requête : " . $conn->error);
        }
    } else {
        $response = array("status" => "error", "message" => "Erreur lors de la suppression des données : " . $conn->error);
    }

} else {
    $response = array("status" => "error", "message" => "Aucune donnée reçue.");
}

// Fermer la connexion
$conn->close();

// Définir le type de contenu en JSON et retourner la réponse
header('Content-Type: application/json');
echo json_encode($response);

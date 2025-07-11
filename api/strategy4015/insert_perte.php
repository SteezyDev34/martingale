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

// Préparer la réponse
$response = array("status" => "error", "message" => "Paramètres d'URL manquants.");

// Vérifier si les paramètres d'URL nécessaires sont définis
if (isset($_GET['perte'])) {
    // Récupérer les données des paramètres d'URL
    $perte = $_GET['perte'];
    // Préparer la requête SQL pour éviter les injections SQL
    $stmt = $conn->prepare("INSERT INTO 0_perte4015 (perte) VALUES (?)");
    if ($stmt) {
        $stmt->bind_param("d", $perte);

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



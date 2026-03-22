<?php


require_once __DIR__ . '/../src/Database.php';
$db = new Database();
$pdo = $db->getPdo();


// Préparer la réponse
$response = array("status" => "error", "message" => "Paramètres d'URL manquants.");

// Vérifier si les paramètres d'URL nécessaires sont définis
if (isset($_GET['perte'])) {
    // Récupérer les données des paramètres d'URL
    $perte = $_GET['perte'];

    // Préparer la requête SQL pour éviter les injections SQL
    $stmt = $pdo->prepare("INSERT INTO 0_perteBREAK (perte) VALUES (:perte)");
    if ($stmt) {
        // Exécuter la requête
        if ($stmt->execute([':perte' => floatval($perte)])) {
            $response = array("status" => "success", "message" => "Données insérées avec succès.");
        } else {
            $response = array("status" => "error", "message" => "Erreur lors de l'insertion des données.");
        }
    } else {
        $response = array("status" => "error", "message" => "Erreur lors de la préparation de la requête.");
    }
} else {
    $response = array("status" => "error", "message" => "Pas de données : " . $conn->error);
}
// PDO fermera la connexion automatiquement

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner la réponse en JSON
echo json_encode($response);

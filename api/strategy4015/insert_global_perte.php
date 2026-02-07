<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../src/Database.php';
$db = new Database();
$pdo = $db->getPdo();

// Préparer la réponse par défaut
$response = array("status" => "error", "message" => "Paramètres d'URL manquants.");

// Vérifier si le paramètre 'perte' est défini
if (isset($_GET['mise'])) {
    // Récupérer la nouvelle perte reçue
    $nouvelle_mise = $_GET['mise'];

    // Récupérer la dernière valeur enregistrée
    $query_last_perte = "SELECT perte FROM 0_perte ORDER BY id DESC LIMIT 1";
    $stmt_last = $pdo->query($query_last_perte);
    $row = $stmt_last->fetch(PDO::FETCH_ASSOC);
    $derniere_perte = $row['perte'] ?? 0;
    $nouvelle_perte = floatval($derniere_perte) + floatval($nouvelle_mise);
    $nouvelle_perte = $nouvelle_perte < 0 ? 0 : $nouvelle_perte;
    // Supprimer toutes les anciennes entrées
    $delete_query = "DELETE FROM 0_perte";
    $pdo->exec($delete_query);

    // Insérer la nouvelle perte
    $stmt = $pdo->prepare("INSERT INTO 0_perte (perte) VALUES (:perte)");
    if ($stmt->execute([':perte' => $nouvelle_perte])) {
        $response = array(
            "status" => "success",
            "message" => "Données mises à jour avec succès.",
            "derniere_perte" => $derniere_perte,
            "nouvelle_perte" => $nouvelle_perte
        );
    } else {
        $response = array("status" => "error", "message" => "Erreur lors de l'insertion des données.");
    }
} else {
    $response = array("status" => "error", "message" => "Aucune donnée reçue.");
}

// Fermer la connexion
$conn->close();

// Définir le type de contenu en JSON et retourner la réponse
header('Content-Type: application/json');
echo json_encode($response);

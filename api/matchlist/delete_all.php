<?php
// API pour supprimer tous les matchs de la table matchlisttodo
// Toutes les chaînes et commentaires sont en français.

require_once __DIR__ . '/../config.php';

// Vérifier que la méthode est POST pour la sécurité
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'Méthode non autorisée']);
    exit;
}

// Obtenir la connexion à la base de données
$conn = getDbConnection();

// Préparer la requête de suppression de tous les matchs
$sql = "DELETE FROM matchlisttodo";

if ($conn->query($sql) === TRUE) {
    $affected_rows = $conn->affected_rows;
    $response = [
        'status' => 'success', 
        'message' => "Tous les matchs ont été supprimés avec succès ($affected_rows lignes supprimées)",
        'deleted_count' => $affected_rows
    ];
} else {
    $response = [
        'status' => 'error', 
        'message' => 'Erreur lors de la suppression : ' . $conn->error
    ];
}

// Fermer la connexion
$conn->close();

// Retourner la réponse JSON
header('Content-Type: application/json');
echo json_encode($response);
?>
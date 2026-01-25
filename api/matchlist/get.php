<?php
// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();

// Déterminer l'ordre de tri souhaité (par défaut: décroissant)
// Commentaire: Paramètre 'sort' accepté: 'asc' ou 'desc' (insensible à la casse)
$sort = isset($_GET['sort']) ? strtolower(trim($_GET['sort'])) : 'desc';
$orderSql = ($sort === 'asc') ? 'ASC' : 'DESC';

// Préparer la requête SQL pour récupérer tous les matchs triés par probabilité
$sql = "SELECT * FROM matchlisttodo ORDER BY proba " . $orderSql;
$result = $conn->query($sql);

$matches = array();
$response = array("status" => "error", "message" => "Erreur lors de la récupération des matchs");

if ($result) {
    while ($row = $result->fetch_assoc()) {
        $matches[] = array(
            "match_id" => $row['slug'],
            "players" => $row['players'],
            "league" => $row['ligue'],
            "match_date" => $row['time'],
            "probability" => (float)$row['proba']
        );
    }
    
    $response = array(
        "status" => "success",
        "data" => $matches
    );
} else {
    $response = array(
        "status" => "error",
        "message" => "Erreur lors de la récupération des matchs : " . $conn->error
    );
}

$conn->close();

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner la réponse
echo json_encode($response);
<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Gérer les requêtes OPTIONS (preflight CORS)
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once __DIR__ . '/../src/Database.php';
require_once __DIR__ . '/../src/TelegramBetsRepository.php';

try {
    $db = new Database();
    $repo = new TelegramBetsRepository($db);

    // Créer la table si elle n'existe pas
    $db->createTelegramBetsTable();

    // Récupérer les données
    $input = json_decode(file_get_contents('php://input'), true);

    if (!$input) {
        throw new Exception('Aucune donnée reçue ou format JSON invalide');
    }

    $insertId = $repo->insert($input);

    echo json_encode([
        'success' => true,
        'message' => 'Pari ajouté avec succès',
        'id' => $insertId,
        'data' => $input
    ]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'Erreur de base de données: ' . $e->getMessage()
    ]);
} catch (Exception $e) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => $e->getMessage()
    ]);
}

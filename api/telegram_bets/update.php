<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
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

    // Récupérer les données
    $input = json_decode(file_get_contents('php://input'), true);

    if (!$input || !isset($input['id'])) {
        throw new Exception('ID du pari requis');
    }

    $id = intval($input['id']);
    $processed = isset($input['processed']) ? (bool)$input['processed'] : true;

    $rows = $repo->updateProcessed($id, $processed);

    if ($rows > 0) {
        echo json_encode([
            'success' => true,
            'message' => 'Statut mis à jour avec succès',
            'id' => $id,
            'processed' => (bool)$processed
        ]);
    } else {
        throw new Exception('Pari non trouvé ou aucune modification');
    }
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

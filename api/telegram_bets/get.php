<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
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

    // Paramètres de requête
    $processed = $_GET['processed'] ?? null;
    $tipster = $_GET['tipster'] ?? null;
    $limit = isset($_GET['limit']) ? intval($_GET['limit']) : 50;
    $offset = isset($_GET['offset']) ? intval($_GET['offset']) : 0;
    $date_from = $_GET['date_from'] ?? null;
    $date_to = $_GET['date_to'] ?? null;

    $filters = [];
    if ($processed !== null) $filters['processed'] = intval($processed);
    if ($tipster !== null) $filters['tipster'] = $tipster;
    if ($date_from !== null) $filters['date_from'] = $date_from;
    if ($date_to !== null) $filters['date_to'] = $date_to;

    $result = $repo->get($filters, $limit, $offset);

    echo json_encode([
        'success' => true,
        'data' => $result['data'],
        'total' => intval($result['total']),
        'limit' => $result['limit'],
        'offset' => $result['offset'],
        'has_more' => ($result['offset'] + $result['limit']) < $result['total']
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

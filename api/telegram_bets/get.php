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

require_once '../config.php';

try {
    // Connexion à la base de données
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Paramètres de requête
    $processed = $_GET['processed'] ?? null;
    $tipster = $_GET['tipster'] ?? null;
    $limit = isset($_GET['limit']) ? intval($_GET['limit']) : 50;
    $offset = isset($_GET['offset']) ? intval($_GET['offset']) : 0;
    $date_from = $_GET['date_from'] ?? null;
    $date_to = $_GET['date_to'] ?? null;
    
    // Construction de la requête
    $sql = "SELECT * FROM telegram_bets WHERE 1=1";
    $params = [];
    
    if ($processed !== null) {
        $sql .= " AND processed = :processed";
        $params[':processed'] = ($processed === 'true' || $processed === '1') ? 1 : 0;
    }
    
    if ($tipster !== null) {
        $sql .= " AND tipster = :tipster";
        $params[':tipster'] = $tipster;
    }
    
    if ($date_from !== null) {
        $sql .= " AND date_pari >= :date_from";
        $params[':date_from'] = $date_from;
    }
    
    if ($date_to !== null) {
        $sql .= " AND date_pari <= :date_to";
        $params[':date_to'] = $date_to;
    }
    
    $sql .= " ORDER BY created_at DESC LIMIT :limit OFFSET :offset";
    
    $stmt = $pdo->prepare($sql);
    
    // Lier les paramètres
    foreach ($params as $key => $value) {
        $stmt->bindValue($key, $value);
    }
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
    
    $stmt->execute();
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Compter le total pour la pagination
    $countSql = "SELECT COUNT(*) FROM telegram_bets WHERE 1=1";
    if ($processed !== null) {
        $countSql .= " AND processed = " . (($processed === 'true' || $processed === '1') ? 1 : 0);
    }
    if ($tipster !== null) {
        $countSql .= " AND tipster = '$tipster'";
    }
    if ($date_from !== null) {
        $countSql .= " AND date_pari >= '$date_from'";
    }
    if ($date_to !== null) {
        $countSql .= " AND date_pari <= '$date_to'";
    }
    
    $countStmt = $pdo->query($countSql);
    $total = $countStmt->fetchColumn();
    
    echo json_encode([
        'success' => true,
        'data' => $results,
        'total' => intval($total),
        'limit' => $limit,
        'offset' => $offset,
        'has_more' => ($offset + $limit) < $total
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
?>
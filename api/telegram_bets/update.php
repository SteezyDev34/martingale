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

require_once '../config.php';

try {
    // Connexion à la base de données
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Récupérer les données
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input || !isset($input['id'])) {
        throw new Exception('ID du pari requis');
    }
    
    $id = intval($input['id']);
    $processed = isset($input['processed']) ? ($input['processed'] ? 1 : 0) : 1;
    
    // Mettre à jour le statut processed
    $sql = "UPDATE telegram_bets SET processed = :processed WHERE id = :id";
    $stmt = $pdo->prepare($sql);
    
    $result = $stmt->execute([
        ':processed' => $processed,
        ':id' => $id
    ]);
    
    if ($result && $stmt->rowCount() > 0) {
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
?>
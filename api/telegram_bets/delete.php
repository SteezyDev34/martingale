<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: DELETE, OPTIONS');
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
    
    // Récupérer l'ID depuis les paramètres GET ou POST
    $id = $_GET['id'] ?? null;
    
    if (!$id) {
        $input = json_decode(file_get_contents('php://input'), true);
        $id = $input['id'] ?? null;
    }
    
    if (!$id) {
        throw new Exception('ID du pari requis');
    }
    
    $id = intval($id);
    
    // Supprimer le pari
    $sql = "DELETE FROM telegram_bets WHERE id = :id";
    $stmt = $pdo->prepare($sql);
    
    $result = $stmt->execute([':id' => $id]);
    
    if ($result && $stmt->rowCount() > 0) {
        echo json_encode([
            'success' => true,
            'message' => 'Pari supprimé avec succès',
            'id' => $id
        ]);
    } else {
        throw new Exception('Pari non trouvé');
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
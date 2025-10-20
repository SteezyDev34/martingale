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

require_once '../config.php';

try {
    // Connexion à la base de données
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Créer la table si elle n'existe pas
    $createTableSQL = "
    CREATE TABLE IF NOT EXISTS telegram_bets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date_pari VARCHAR(20) NOT NULL,
        equipe_1 VARCHAR(255) NOT NULL,
        equipe_2 VARCHAR(255) NOT NULL,
        categorie VARCHAR(100) NOT NULL,
        type_de_pari VARCHAR(255) NOT NULL,
        selection VARCHAR(500) NOT NULL,
        odds DECIMAL(10,3) NOT NULL,
        tipster VARCHAR(50) NOT NULL,
        message_original TEXT,
        sender_username VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT FALSE,
        INDEX idx_processed (processed),
        INDEX idx_date_pari (date_pari),
        INDEX idx_tipster (tipster)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci";
    
    $pdo->exec($createTableSQL);
    
    // Récupérer les données
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input) {
        throw new Exception('Aucune donnée reçue ou format JSON invalide');
    }
    
    // Validation des champs obligatoires
    $requiredFields = ['date', 'equipe_1', 'equipe_2', 'categorie', 'type_de_pari', 'selection', 'odds', 'tipster'];
    foreach ($requiredFields as $field) {
        if (!isset($input[$field]) || empty($input[$field])) {
            throw new Exception("Champ obligatoire manquant: $field");
        }
    }
    
    // Préparer la requête d'insertion
    $sql = "INSERT INTO telegram_bets 
            (date_pari, equipe_1, equipe_2, categorie, type_de_pari, selection, odds, tipster, message_original, sender_username) 
            VALUES (:date_pari, :equipe_1, :equipe_2, :categorie, :type_de_pari, :selection, :odds, :tipster, :message_original, :sender_username)";
    
    $stmt = $pdo->prepare($sql);
    
    // Exécuter la requête
    $result = $stmt->execute([
        ':date_pari' => $input['date'],
        ':equipe_1' => $input['equipe_1'],
        ':equipe_2' => $input['equipe_2'],
        ':categorie' => $input['categorie'],
        ':type_de_pari' => $input['type_de_pari'],
        ':selection' => $input['selection'],
        ':odds' => floatval($input['odds']),
        ':tipster' => $input['tipster'],
        ':message_original' => $input['message_original'] ?? null,
        ':sender_username' => $input['sender_username'] ?? null
    ]);
    
    if ($result) {
        $insertId = $pdo->lastInsertId();
        echo json_encode([
            'success' => true,
            'message' => 'Pari ajouté avec succès',
            'id' => $insertId,
            'data' => $input
        ]);
    } else {
        throw new Exception('Erreur lors de l\'insertion');
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
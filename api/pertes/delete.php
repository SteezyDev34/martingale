<?php
// API pour supprimer une ligne de perte dans 0_perte ou 0_perte1SET
// Toutes les chaînes et commentaires sont en français.

require_once __DIR__ . '/../config.php';

/**
 * Déterminer la table selon le type.
 * Retourne '0_perte' pour 'normal', '0_perte1SET' pour '1set', sinon null.
 */
function table_pour_type($type) {
    $t = strtolower(trim($type ?? ''));
    if ($t === '1set') return '0_perte1SET';
    if ($t === 'normal' || $t === '') return '0_perte';
    return null;
}

// Lire le corps JSON
$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

if (!is_array($data)) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'Entrée JSON invalide']);
    exit;
}

$type = $data['type'] ?? 'normal';
$id = isset($data['id']) ? intval($data['id']) : 0;

$table = table_pour_type($type);
if ($table === null) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'Type non supporté']);
    exit;
}

if ($id <= 0) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'ID invalide']);
    exit;
}

$conn = getDbConnection();

// Préparer la requête de suppression
$sql = "DELETE FROM `$table` WHERE id = ?";
$stmt = $conn->prepare($sql);
if (!$stmt) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'Préparation échouée: ' . $conn->error]);
    $conn->close();
    exit;
}

$stmt->bind_param('i', $id);

if ($stmt->execute()) {
    $response = ['status' => 'success', 'message' => 'Ligne supprimée', 'id' => $id];
} else {
    $response = ['status' => 'error', 'message' => 'Exécution échouée: ' . $stmt->error];
}

$stmt->close();
$conn->close();

header('Content-Type: application/json');
echo json_encode($response);
?>
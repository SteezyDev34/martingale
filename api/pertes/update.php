<?php
// API pour mettre à jour la valeur du champ 'perte' dans 0_perte et 0_perte1SET
// Commentaires et chaînes en français.

require_once __DIR__ . '/../config.php';

// Fonction: déterminer la table selon le type
// Commentaire: Sécurise en n'autorisant que '0_perte' et '0_perte1SET'.
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
$perte = isset($data['perte']) ? floatval($data['perte']) : null;

$table = table_pour_type($type);
if ($table === null) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'Type non supporté']);
    exit;
}

if ($id <= 0 || $perte === null) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'Paramètres manquants ou invalides']);
    exit;
}

$conn = getDbConnection();

// Préparer la requête de mise à jour
$sql = "UPDATE `$table` SET perte = ? WHERE id = ?";
$stmt = $conn->prepare($sql);
if (!$stmt) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'Préparation échouée: ' . $conn->error]);
    $conn->close();
    exit;
}

$stmt->bind_param('di', $perte, $id);

if ($stmt->execute()) {
    $response = ['status' => 'success', 'message' => 'Perte mise à jour', 'id' => $id, 'perte' => $perte];
} else {
    $response = ['status' => 'error', 'message' => 'Exécution échouée: ' . $stmt->error];
}

$stmt->close();
$conn->close();

header('Content-Type: application/json');
echo json_encode($response);
?>
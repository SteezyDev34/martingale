<?php
// API pour insérer une nouvelle ligne de perte dans 0_perte ou 0_perte1SET
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
$perte = isset($data['perte']) ? floatval($data['perte']) : null;
$wantwin = isset($data['wantwin']) ? floatval($data['wantwin']) : 0.0;
$mise = isset($data['mise']) ? floatval($data['mise']) : 0.0;
$ligue = isset($data['ligue']) ? trim($data['ligue']) : null;

$table = table_pour_type($type);
if ($table === null) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'Type non supporté']);
    exit;
}

// Valider les champs obligatoires
if ($perte === null || !is_numeric($perte)) {
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => "Le champ 'perte' est requis et doit être numérique"]);
    exit;
}

$conn = getDbConnection();

if ($table === '0_perte1SET') {
    // Insertion pour la table 0_perte1SET (avec ligue)
    $sql = "INSERT INTO `0_perte1SET` (perte, wantwin, mise, ligue) VALUES (?, ?, ?, ?)";
    $stmt = $conn->prepare($sql);
    if (!$stmt) {
        header('Content-Type: application/json');
        echo json_encode(['status' => 'error', 'message' => 'Préparation échouée: ' . $conn->error]);
        $conn->close();
        exit;
    }
    $ligueSafe = $ligue ?? '';
    $stmt->bind_param('ddds', $perte, $wantwin, $mise, $ligueSafe);
} else {
    // Insertion pour la table 0_perte
    $sql = "INSERT INTO `0_perte` (perte, wantwin, mise) VALUES (?, ?, ?)";
    $stmt = $conn->prepare($sql);
    if (!$stmt) {
        header('Content-Type: application/json');
        echo json_encode(['status' => 'error', 'message' => 'Préparation échouée: ' . $conn->error]);
        $conn->close();
        exit;
    }
    $stmt->bind_param('ddd', $perte, $wantwin, $mise);
}

if ($stmt->execute()) {
    $response = ['status' => 'success', 'message' => 'Perte ajoutée', 'id' => $conn->insert_id];
} else {
    $response = ['status' => 'error', 'message' => 'Exécution échouée: ' . $stmt->error];
}

$stmt->close();
$conn->close();

header('Content-Type: application/json');
echo json_encode($response);
?>
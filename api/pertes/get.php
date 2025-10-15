<?php
// API pour récupérer les pertes des tables 0_perte et 0_perte1SET
// Commentaires et chaînes en français.

require_once __DIR__ . '/../config.php';

// Fonction: déterminer le nom de la table selon le type
// Commentaire: Retourne '0_perte' pour 'normal' et '0_perte1SET' pour '1set'.
function table_pour_type($type) {
    $t = strtolower(trim($type ?? ''));
    if ($t === '1set') return '0_perte1SET';
    return '0_perte'; // par défaut normal
}

// Lecture paramètre type
$type = isset($_GET['type']) ? $_GET['type'] : 'normal';
$table = table_pour_type($type);

$conn = getDbConnection();

// Construire SQL selon la table
if ($table === '0_perte1SET') {
    $sql = "SELECT id, perte, wantwin, mise, ligue, created_at FROM `0_perte1SET` ORDER BY id DESC";
} else {
    $sql = "SELECT id, perte, wantwin, mise FROM `0_perte` ORDER BY id DESC";
}

$result = $conn->query($sql);

$rows = array();
if ($result) {
    while ($row = $result->fetch_assoc()) {
        $rows[] = $row;
    }
    $response = array('status' => 'success', 'data' => $rows);
} else {
    $response = array('status' => 'error', 'message' => 'Erreur SQL: ' . $conn->error);
}

$conn->close();

header('Content-Type: application/json');
echo json_encode($response);
?>
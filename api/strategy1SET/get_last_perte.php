<?php
// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();

$mtt_recup = 0;
// Vérifier si le paramètre "ligue" est fourni
if (isset($_GET['mtt_recup']) || empty($_GET['mtt_recup'])) {
    $mtt_recup = $_GET['mtt_recup'];
}

// On suppose qu'il y a un champ "id" ou un champ "date" pour trier par ordre décroissant
/* $sql = "SELECT * FROM 0_perte1SET 
        WHERE created_at < NOW() - INTERVAL 1 DAY 
        ORDER BY id DESC 
        LIMIT 1"; */
$sql = "SELECT * FROM 0_perte1SET 
ORDER BY perte DESC 
LIMIT 1";
$result = $conn->query($sql);

$data = array();
if ($result && $result->num_rows > 0) {
    $data[] = $result->fetch_assoc();
}

if (!empty($data)) {
    $data[0]['perte'] -= $mtt_recup;

    if ($data[0]['perte'] >= 0) {
        $sql = "UPDATE 0_perte1SET SET perte = {$data[0]['perte']} WHERE id = {$data[0]['id']}";
        $conn->query($sql);
    } else {
        $sql = "DELETE FROM 0_perte1SET WHERE id = {$data[0]['id']}";
        $conn->query($sql);
    }
}
// Fermer la connexion
$conn->close();
// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner les données en JSON (ou null si aucune ligne trouvée)
echo json_encode($data);

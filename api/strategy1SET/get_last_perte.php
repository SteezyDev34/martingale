<?php
// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();


// On suppose qu'il y a un champ "id" ou un champ "date" pour trier par ordre décroissant
/* $sql = "SELECT * FROM 0_perte1SET 
        WHERE created_at < NOW() - INTERVAL 1 DAY 
        ORDER BY id DESC 
        LIMIT 1"; */
$sql = "SELECT * FROM 0_perte1SET 
ORDER BY id DESC 
LIMIT 1";
$result = $conn->query($sql);

$data = array();
if ($result && $result->num_rows > 0) {
    $data[] = $result->fetch_assoc();
}

// Fermer la connexion
$conn->close();
// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner les données en JSON (ou null si aucune ligne trouvée)
echo json_encode($data);

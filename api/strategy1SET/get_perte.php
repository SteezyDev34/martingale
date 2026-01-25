<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();


// Vérifier si le paramètre "ligue" est fourni
if (!isset($_GET['ligue']) || empty($_GET['ligue'])) {
    echo json_encode(null);
    exit;
}

$ligue = $conn->real_escape_string($_GET['ligue']);
$ligue = urldecode($ligue);
// Requête SQL : sélectionner la dernière perte pour la ligue donnée
// On suppose qu'il y a un champ "id" ou un champ "date" pour trier par ordre décroissant
$sql = "SELECT * FROM 0_perte1SET WHERE ligue = '$ligue' ORDER BY id DESC LIMIT 1";
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

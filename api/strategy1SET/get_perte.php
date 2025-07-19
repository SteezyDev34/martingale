<?php

// Configurer les paramètres de la base de données
$servername = "pcomstd757.mysql.db";
$username = "pcomstd757";
$password = "RgzQzGkXvsMK";
$database = "pcomstd757";

// Créer une connexion à la base de données
$conn = new mysqli($servername, $username, $password, $database);

// Vérifier la connexion
if ($conn->connect_error) {
    die("Échec de la connexion : " . $conn->connect_error);
}

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Vérifier si le paramètre "ligue" est fourni
if (!isset($_GET['ligue']) || empty($_GET['ligue'])) {
    echo json_encode(null);
    exit;
}

$ligue = $conn->real_escape_string($_GET['ligue']);

// Requête SQL : sélectionner la dernière perte pour la ligue donnée
// On suppose qu'il y a un champ "id" ou un champ "date" pour trier par ordre décroissant
$sql = "SELECT * FROM 0_perte1SET WHERE ligue = '$ligue' ORDER BY id DESC LIMIT 1";
$result = $conn->query($sql);

$data = null;
if ($result && $result->num_rows > 0) {
    $data = $result->fetch_assoc();
}

// Fermer la connexion
$conn->close();

// Retourner les données en JSON (ou null si aucune ligne trouvée)
echo json_encode($data);

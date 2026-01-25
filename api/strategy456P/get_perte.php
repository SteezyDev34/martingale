<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();

// Exécuter une requête SQL
$sql = "SELECT * FROM 0_perte456P";
$result = $conn->query($sql);

// Préparer les données pour JSON
$data = array();
if ($result->num_rows > 0) {
    // Parcourir les résultats et ajouter chaque ligne au tableau
    while ($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
}

// Fermer la connexion
$conn->close();

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner les données en JSON
echo json_encode($data);


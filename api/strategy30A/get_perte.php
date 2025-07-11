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

// Exécuter une requête SQL
$sql = "SELECT * FROM 0_perte30A";
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


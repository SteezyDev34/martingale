<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../src/Database.php';

$db = new Database();
$pdo = $db->getPdo();

// Exécuter une requête SQL
$sql = "SELECT * FROM 0_perte4015";
$stmt = $pdo->query($sql);
$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Préparer les données pour JSON
$data = $rows;

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner les données en JSON
echo json_encode($data);

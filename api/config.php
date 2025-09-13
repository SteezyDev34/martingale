<?php

/**
 * Fichier de configuration pour la connexion à la base de données
 * Ce fichier centralise les paramètres de connexion pour toutes les stratégies
 */

// Configurer les paramètres de la base de données
$servername = "localhost";
$username = "sc2vagr6376_auxobetbot";
$password = "go#o]SzuCvjz";
$database = "sc2vagr6376_auxobetbot";

/**
 * Fonction pour établir une connexion à la base de données
 * @return mysqli Objet de connexion à la base de données
 */
function getDbConnection() {
    global $servername, $username, $password, $database;
    
    // Créer une connexion à la base de données
    $conn = new mysqli($servername, $username, $password, $database);
    
    // Vérifier la connexion
    if ($conn->connect_error) {
        die("Échec de la connexion : " . $conn->connect_error);
    }
    
    // Définir l'encodage de la connexion en UTF-8
    if (!$conn->set_charset("utf8")) {
        die("Erreur lors du chargement du jeu de caractères utf8 : " . $conn->error);
    }
    
    return $conn;
}
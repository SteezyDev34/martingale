<?php
// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Préparer la réponse
$response = array("status" => "error", "message" => "Paramètres manquants");

// Vérifie si le paramètre match_id existe dans l'URL
if (isset($_GET['match_id'])) {
    // Récupère le paramètre
    $match_id = $_GET['match_id'];
    
    // Obtenir la connexion à la base de données
    $conn = getDbConnection();
    
    // Préparer la requête SQL pour supprimer le match
    $stmt = $conn->prepare("DELETE FROM matchlisttodo WHERE slug = ?");
    
    if ($stmt) {
        $stmt->bind_param("s", $match_id);
        
        // Exécuter la requête
        if ($stmt->execute()) {
            if ($stmt->affected_rows > 0) {
                $response = array(
                    "status" => "success",
                    "message" => "Match supprimé avec succès"
                );
            } else {
                $response = array(
                    "status" => "error",
                    "message" => "Match non trouvé"
                );
            }
        } else {
            $response = array(
                "status" => "error",
                "message" => "Erreur lors de la suppression : " . $stmt->error
            );
        }
        
        $stmt->close();
    } else {
        $response = array(
            "status" => "error",
            "message" => "Erreur de préparation : " . $conn->error
        );
    }
    
    $conn->close();
}

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner la réponse
echo json_encode($response);
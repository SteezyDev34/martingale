<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();

// Vérifier et valider l'ID
if (isset($_GET['id'])) {
    $id = filter_var($_GET['id'], FILTER_VALIDATE_INT, ["options" => ["min_range" => 1]]);

    if ($id !== false) {
        // Préparer la requête SQL
        $stmt = $conn->prepare("DELETE FROM 0_perte4030 WHERE id = ?");

        if ($stmt) {
            // Lier le paramètre
            $stmt->bind_param("i", $id);

            // Exécuter la requête
            if ($stmt->execute()) {
                if ($stmt->affected_rows > 0) {
                    echo json_encode(["success" => true, "message" => "Enregistrement supprimé avec succès."]);
                } else {
                    echo json_encode(["success" => false, "message" => "Aucun enregistrement trouvé avec cet ID."]);
                }
            } else {
                echo json_encode(["success" => false, "message" => "Erreur lors de la suppression : " . $stmt->error]);
            }

            // Fermer la déclaration
            $stmt->close();
        } else {
            echo json_encode(["success" => false, "message" => "Erreur lors de la préparation de la requête."]);
        }
    } else {
        echo json_encode(["success" => false, "message" => "ID invalide."]);
    }
} else {
    echo json_encode(["success" => false, "message" => "ID non fourni."]);
}

// Fermer la connexion
$conn->close();

<?php

// Inclure le fichier de configuration
require_once __DIR__ . '/../src/Database.php';

$db = new Database();
$pdo = $db->getPdo();

// Vérifier et valider l'ID
if (isset($_GET['id'])) {
    $id = filter_var($_GET['id'], FILTER_VALIDATE_INT, ["options" => ["min_range" => 1]]);

    if ($id !== false) {
        // Préparer la requête SQL
        $stmt = $pdo->prepare("DELETE FROM 0_perte4015 WHERE id = :id");

        if ($stmt) {
            // Exécuter la requête
            if ($stmt->execute([':id' => $id])) {
                if ($stmt->rowCount() > 0) {
                    echo json_encode(["success" => true, "message" => "Enregistrement supprimé avec succès."]);
                } else {
                    echo json_encode(["success" => false, "message" => "Aucun enregistrement trouvé avec cet ID."]);
                }
            } else {
                echo json_encode(["success" => false, "message" => "Erreur lors de la suppression."]);
            }
        } else {
            echo json_encode(["success" => false, "message" => "Erreur lors de la préparation de la requête."]);
        }
    } else {
        echo json_encode(["success" => false, "message" => "ID invalide."]);
    }
} else {
    echo json_encode(["success" => false, "message" => "ID non fourni."]);
}

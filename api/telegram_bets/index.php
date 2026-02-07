<?php
header('Content-Type: text/html; charset=utf-8');

require_once __DIR__ . '/../src/Database.php';
require_once __DIR__ . '/../src/TelegramBetsRepository.php';
require_once __DIR__ . '/../src/TelegramBetsRepository.php';

echo "<h1>API Telegram Bets - Documentation</h1>";

echo "<h2>Endpoints disponibles:</h2>";

echo "<h3>1. Insérer un pari (POST /telegram_bets/insert.php)</h3>";
echo "<p><strong>Données JSON requises:</strong></p>";
echo "<pre>{
  \"date\": \"25/09/2025\",
  \"equipe_1\": \"Al Shabab Riyadh\",
  \"equipe_2\": \"Al Kholood\",
  \"categorie\": \"Temps réglementaire\",
  \"type_de_pari\": \"Total 1\",
  \"selection\": \"Total Individuel 1 Plus de 0.5\",
  \"odds\": \"1.432\",
  \"tipster\": \"marco\",
  \"message_original\": \"Message telegram original (optionnel)\",
  \"sender_username\": \"@username (optionnel)\"
}</pre>";

echo "<h3>2. Récupérer les paris (GET /telegram_bets/get.php)</h3>";
echo "<p><strong>Paramètres optionnels:</strong></p>";
echo "<ul>";
echo "<li><code>processed</code> - true/false pour filtrer par statut traité</li>";
echo "<li><code>tipster</code> - filtrer par nom du tipster</li>";
echo "<li><code>limit</code> - nombre de résultats (défaut: 50)</li>";
echo "<li><code>offset</code> - décalage pour pagination (défaut: 0)</li>";
echo "<li><code>date_from</code> - date de début (format: DD/MM/YYYY)</li>";
echo "<li><code>date_to</code> - date de fin (format: DD/MM/YYYY)</li>";
echo "</ul>";

echo "<h3>3. Mettre à jour un pari (POST /telegram_bets/update.php)</h3>";
echo "<p><strong>Données JSON:</strong></p>";
echo "<pre>{
  \"id\": 123,
  \"processed\": true
}</pre>";

echo "<h3>4. Supprimer un pari (DELETE /telegram_bets/delete.php)</h3>";
echo "<p><strong>Paramètre:</strong></p>";
echo "<ul><li><code>id</code> - ID du pari à supprimer</li></ul>";

echo "<h2>Structure de la base de données:</h2>";
echo "<pre>
CREATE TABLE telegram_bets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_pari VARCHAR(20) NOT NULL,
    equipe_1 VARCHAR(255) NOT NULL,
    equipe_2 VARCHAR(255) NOT NULL,
    categorie VARCHAR(100) NOT NULL,
    type_de_pari VARCHAR(255) NOT NULL,
    selection VARCHAR(500) NOT NULL,
    odds DECIMAL(10,3) NOT NULL,
    tipster VARCHAR(50) NOT NULL,
    message_original TEXT,
    sender_username VARCHAR(100),
    sender_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);
</pre>";
try {
    // Connexion via Database / Repository
    $db = new Database();
    $repo = new TelegramBetsRepository($db);

    // Créer la table si nécessaire
    $db->createTelegramBetsTable();

    // Statistiques
    $stats = $db->getPdo()->query("SELECT 
      COUNT(*) as total,
      COUNT(CASE WHEN processed = 1 THEN 1 END) as processed,
      COUNT(CASE WHEN processed = 0 THEN 1 END) as unprocessed,
      COUNT(DISTINCT tipster) as unique_tipsters
      FROM telegram_bets")->fetch(PDO::FETCH_ASSOC);

    echo "<h2>Statistiques actuelles:</h2>";
    echo "<ul>";
    echo "<li>Total des paris: {$stats['total']}</li>";
    echo "<li>Paris traités: {$stats['processed']}</li>";
    echo "<li>Paris non traités: {$stats['unprocessed']}</li>";
    echo "<li>Nombre de tipsters: {$stats['unique_tipsters']}</li>";
    echo "</ul>";
} catch (Exception $e) {
    echo "<p style='color: red;'>Erreur: " . $e->getMessage() . "</p>";
}

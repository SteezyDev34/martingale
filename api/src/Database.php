<?php
/**
 * Classe Database autonome : lit .env et crée PDO sans dépendre de config.php
 */
class Database
{
    private $pdo;

    public function __construct()
    {
        $envPath = realpath(__DIR__ . '/../.env') ?: (__DIR__ . '/../.env');
        $this->loadEnvFile($envPath);

        $host = getenv('DB_HOST') ?: 'localhost';
        $dbname = getenv('DB_NAME') ?: 'database';
        $user = getenv('DB_USER') ?: 'user';
        $pass = getenv('DB_PASS') ?: '';

        $dsn = "mysql:host={$host};dbname={$dbname};charset=utf8mb4";

        try {
            $this->pdo = new PDO($dsn, $user, $pass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]);
        } catch (PDOException $e) {
            die('Échec de la connexion PDO : ' . $e->getMessage());
        }
    }

    private function loadEnvFile(string $path)
    {
        if (!file_exists($path)) return;

        $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            $line = trim($line);
            if ($line === '' || $line[0] === '#') continue;
            if (strpos($line, '=') === false) continue;
            list($name, $value) = explode('=', $line, 2);
            $name = trim($name);
            $value = trim($value);
            if ((substr($value, 0, 1) === '"' && substr($value, -1) === '"') || (substr($value, 0, 1) === "'" && substr($value, -1) === "'")) {
                $value = substr($value, 1, -1);
            }
            if (getenv($name) === false) {
                putenv("{$name}={$value}");
                $_ENV[$name] = $value;
                $_SERVER[$name] = $value;
            }
        }
    }

    /**
     * Retourne l'instance PDO
     * @return PDO
     */
    public function getPdo()
    {
        return $this->pdo;
    }

    /**
     * Crée la table telegram_bets si nécessaire
     * @return void
     */
    public function createTelegramBetsTable()
    {
        $createTableSQL = "
    CREATE TABLE IF NOT EXISTS telegram_bets (
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
        processed BOOLEAN DEFAULT FALSE,
        INDEX idx_processed (processed),
        INDEX idx_date_pari (date_pari),
        INDEX idx_tipster (tipster)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci";

        $this->pdo->exec($createTableSQL);
    }
}

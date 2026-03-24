<?php

require_once __DIR__ . '/Database.php';

class TelegramBetsRepository
{
    private $pdo;

    public function __construct(Database $db)
    {
        $this->pdo = $db->getPdo();
    }

    public function createTable()
    {
        // Use the helper in config via Database; assume table already created by Database when needed
        // left here for symmetry
        $db = new Database();
        $db->createTelegramBetsTable();
    }

    public function insert(array $data)
    {
        $sql = "INSERT INTO telegram_bets
            ( selection)
            VALUES (:selection)";

        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([
            ':selection' => $data['selection'] ?? null,
        ]);

        return (int)$this->pdo->lastInsertId();
    }

    public function get(array $filters = [], int $limit = 50, int $offset = 0)
    {
        $sql = "SELECT * FROM telegram_bets WHERE 1=1";
        $countSql = "SELECT COUNT(*) FROM telegram_bets WHERE 1=1";
        $params = [];

        if (isset($filters['processed'])) {
            $sql .= " AND processed = :processed";
            $countSql .= " AND processed = :processed";
            $params[':processed'] = $filters['processed'] ? 1 : 0;
        }

        if (!empty($filters['tipster'])) {
            $sql .= " AND tipster = :tipster";
            $countSql .= " AND tipster = :tipster";
            $params[':tipster'] = $filters['tipster'];
        }

        if (!empty($filters['date_from'])) {
            $sql .= " AND date_pari >= :date_from";
            $countSql .= " AND date_pari >= :date_from";
            $params[':date_from'] = $filters['date_from'];
        }

        if (!empty($filters['date_to'])) {
            $sql .= " AND date_pari <= :date_to";
            $countSql .= " AND date_pari <= :date_to";
            $params[':date_to'] = $filters['date_to'];
        }

        $sql .= " ORDER BY created_at DESC LIMIT :limit OFFSET :offset";

        $stmt = $this->pdo->prepare($sql);
        foreach ($params as $k => $v) {
            $stmt->bindValue($k, $v);
        }
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
        $stmt->execute();
        $data = $stmt->fetchAll();

        $countStmt = $this->pdo->prepare($countSql);
        foreach ($params as $k => $v) {
            $countStmt->bindValue($k, $v);
        }
        $countStmt->execute();
        $total = (int)$countStmt->fetchColumn();

        return ['data' => $data, 'total' => $total, 'limit' => $limit, 'offset' => $offset];
    }

    public function updateProcessed(int $id, int $processed)
    {
        $sql = "UPDATE telegram_bets SET processed = :processed WHERE id = :id";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([':processed' => $processed ? $processed : 0, ':id' => $id]);
        return $stmt->rowCount();
    }

    public function delete(int $id)
    {
        $sql = "DELETE FROM telegram_bets WHERE id = :id";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([':id' => $id]);
        return $stmt->rowCount();
    }
}

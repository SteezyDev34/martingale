<?php

/**
 * Petite couche de compatibilité mysqli -> PDO pour migration progressive.
 * Fournit une fonction getDbConnection() qui retourne un objet avec
 * une API minimale utilisée dans le projet (query, prepare, set_charset, close).
 */
require_once __DIR__ . '/Database.php';

class MysqliResultCompat
{
    private $rows;
    private $index = 0;
    public $num_rows;

    public function __construct(array $rows)
    {
        $this->rows = $rows;
        $this->num_rows = count($rows);
    }

    public function fetch_assoc()
    {
        if ($this->index >= $this->num_rows) return null;
        return $this->rows[$this->index++];
    }
}

class MysqliStmtCompat
{
    private $pdoStmt;
    private $boundParams = [];
    public $error = '';
    public $num_rows = 0;
    private $storedResult = null;

    public function __construct(PDOStatement $pdoStmt)
    {
        $this->pdoStmt = $pdoStmt;
    }

    // Accept references like bind_param('i', $var)
    public function bind_param($types /*, &...$vars */)
    {
        $args = func_get_args();
        array_shift($args); // remove types
        $this->boundParams = $args;
        return true;
    }

    public function execute($params = null)
    {
        if ($params !== null) {
            $ok = $this->pdoStmt->execute($params);
            if (!$ok) {
                $err = $this->pdoStmt->errorInfo();
                $this->error = isset($err[2]) ? $err[2] : '';
            } else {
                $this->error = '';
            }
            return $ok;
        }
        // Use bound params
        $vals = [];
        foreach ($this->boundParams as $p) {
            $vals[] = $p;
        }
        $ok = $this->pdoStmt->execute($vals);
        if (!$ok) {
            $err = $this->pdoStmt->errorInfo();
            $this->error = isset($err[2]) ? $err[2] : '';
        } else {
            $this->error = '';
        }
        return $ok;
    }

    public function get_result()
    {
        $rows = $this->pdoStmt->fetchAll(PDO::FETCH_ASSOC);
        return new MysqliResultCompat($rows);
    }

    public function store_result()
    {
        $res = $this->get_result();
        $this->storedResult = $res;
        $this->num_rows = $res->num_rows;
        return true;
    }

    public function close()
    {
        $this->pdoStmt = null;
    }

    public function affected_rows()
    {
        return $this->pdoStmt->rowCount();
    }
}

class MysqliCompat
{
    private $pdo;
    public $error = '';

    public function __construct()
    {
        $db = new Database();
        $this->pdo = $db->getPdo();
    }

    public function set_charset($cs)
    {
        // PDO DSN sets charset; nothing to do
        return true;
    }

    public function query($sql)
    {
        $stmt = $this->pdo->query($sql);
        if ($stmt === false) {
            $err = $this->pdo->errorInfo();
            $this->error = isset($err[2]) ? $err[2] : '';
            return false;
        }

        // Si la requête ne retourne pas de colonnes, ce n'est pas un SELECT
        // (ex: DELETE/UPDATE/INSERT). Pour compatibilité mysqli, retourner true.
        if ($stmt->columnCount() === 0) {
            $this->error = '';
            return true;
        }

        $this->error = '';
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        return new MysqliResultCompat($rows);
    }

    public function prepare($sql)
    {
        $stmt = $this->pdo->prepare($sql);
        if (!$stmt) {
            $err = $this->pdo->errorInfo();
            $this->error = isset($err[2]) ? $err[2] : '';
            return false;
        }
        $this->error = '';
        return new MysqliStmtCompat($stmt);
    }

    public function real_escape_string($str)
    {
        // PDO prepared statements should be used; fallback basic escape
        return addslashes($str);
    }

    public function close()
    {
        $this->pdo = null;
    }
}

function getDbConnection()
{
    return new MysqliCompat();
}

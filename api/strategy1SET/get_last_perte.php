<?php
// Inclure le fichier de configuration
require_once __DIR__ . '/../config.php';

// Obtenir la connexion à la base de données
$conn = getDbConnection();

if (isset($_GET['infos']) || isset($_GET['info'])) {
    $sql = "SELECT * FROM 0_perte1SET ORDER BY id DESC LIMIT 1";
    $result = $conn->query($sql);

    $data = array();
    if ($result && $result->num_rows > 0) {
        $data[] = $result->fetch_assoc();
    }

    // Fermer la connexion
    $conn->close();
    // Définir le type de contenu comme JSON
    header('Content-Type: application/json');

    // Retourner les données en JSON (ou null si aucune ligne trouvée)
    echo json_encode($data);
    exit;
}
$mtt_recup = 0;
// Vérifier si le paramètre "mtt_recup" est fourni
if (isset($_GET['mtt_recup']) && !empty($_GET['mtt_recup'])) {
    $mtt_recup = floatval($_GET['mtt_recup']);
}

// Fonction récursive pour traiter les pertes
function traiterPertes($conn, $mtt_restant, $mtt_initial)
{
    if ($mtt_restant <= 0) {
        return array(
            'pertes_traitees' => array(),
            'mtt_restant' => 0,
            'mtt_utilise' => $mtt_initial
        );
    }

    $sql = "SELECT * FROM 0_perte1SET ORDER BY perte DESC LIMIT 1";
    $result = $conn->query($sql);

    if (!$result || $result->num_rows === 0) {
        return array(
            'pertes_traitees' => array(),
            'mtt_restant' => $mtt_restant,
            'mtt_utilise' => $mtt_initial - $mtt_restant
        );
    }

    $perte = $result->fetch_assoc();
    $pertes_traitees = array();

    if ($perte['perte'] <= $mtt_restant) {
        // La perte peut être entièrement couverte
        $mtt_utilise = $perte['perte'];
        $sql = "DELETE FROM 0_perte1SET WHERE id = {$perte['id']}";
        $conn->query($sql);

        // Récupérer les pertes suivantes avec le montant restant
        $resultat_suivant = traiterPertes($conn, $mtt_restant - $mtt_utilise, $mtt_initial);

        $perte['mtt_recupere'] = $mtt_utilise;
        $pertes_traitees[] = $perte;

        return array(
            'pertes_traitees' => array_merge($pertes_traitees, $resultat_suivant['pertes_traitees']),
            'mtt_restant' => $resultat_suivant['mtt_restant'],
            'mtt_utilise' => $resultat_suivant['mtt_utilise']
        );
    } else {
        // La perte est partiellement couverte
        $nouvelle_perte = $perte['perte'] - $mtt_restant;
        $sql = "UPDATE 0_perte1SET SET perte = {$nouvelle_perte} WHERE id = {$perte['id']}";
        $conn->query($sql);

        $perte['mtt_recupere'] = $mtt_restant;
        $pertes_traitees[] = $perte;

        return array(
            'pertes_traitees' => $pertes_traitees,
            'mtt_restant' => 0,
            'mtt_utilise' => $mtt_initial
        );
    }
}

// Traiter les pertes avec le montant à récupérer
$resultat = traiterPertes($conn, $mtt_recup, $mtt_recup);

// Fermer la connexion
$conn->close();

// Définir le type de contenu comme JSON
header('Content-Type: application/json');

// Retourner les données en JSON avec le montant restant
echo json_encode([array(
    'pertes_traitees' => $resultat['pertes_traitees'],
    'mtt_restant' => $resultat['mtt_restant'],
    'perte' => $resultat['mtt_utilise']
)]);

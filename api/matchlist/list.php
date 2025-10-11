<?php
// Page front pour afficher la liste des matchs triés par probabilité
// Toutes les chaînes et commentaires sont en français.
?>
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Matchlist — Vue Front</title>
    <style>
      /* Style basique pour une table lisible */
      body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #f7f7fa; color: #222; }
      header { background: #20232a; color: #fff; padding: 16px 20px; }
      header h1 { margin: 0; font-size: 18px; }
      main { padding: 20px; }
      .toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
      .toolbar button { padding: 8px 12px; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; }
      .toolbar button:hover { background: #f0f0f3; }
      .status { margin-left: auto; font-size: 12px; color: #555; }
      table { width: 100%; border-collapse: collapse; background: #fff; }
      thead th { text-align: left; background: #fafafa; border-bottom: 1px solid #e5e7eb; padding: 10px; font-weight: 600; }
      tbody td { border-top: 1px solid #f0f0f0; padding: 10px; vertical-align: top; }
      .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
      .pill.league { background: #eef2ff; color: #3730a3; border: 1px solid #e0e7ff; }
      .proba { font-weight: 600; }
      .proba.high { color: #0f766e; }     /* verte pour haute proba */
      .proba.medium { color: #b45309; }   /* orange pour moyenne proba */
      .proba.low { color: #b91c1c; }      /* rouge pour faible proba */
      .error { color: #b91c1c; background: #fee2e2; border: 1px solid #fecaca; padding: 10px; border-radius: 8px; }
      footer { margin-top: 20px; font-size: 12px; color: #666; }
      @media (max-width: 640px) { thead { display: none; } tbody tr { display: block; margin-bottom: 12px; } tbody td { display: flex; justify-content: space-between; } }
    </style>
  </head>
  <body>
    <header>
      <h1>Liste des matchs triés par probabilité</h1>
    </header>
    <main>
      <div class="toolbar">
        <button id="sortDesc">Trier par proba décroissante</button>
        <button id="sortAsc">Trier par proba croissante</button>
        <span class="status" id="status">Prêt</span>
      </div>

      <div id="error" class="error" style="display:none"></div>

      <table aria-label="Liste des matchs">
        <thead>
          <tr>
            <th>Match</th>
            <th>Ligue</th>
            <th>Date</th>
            <th>Probabilité</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>

      <footer>
        Source API: <code>/matchlist/get.php</code> — tri côté serveur et client.
      </footer>
    </main>

    <script>
      // Fonction utilitaire: déterminer la classe de couleur selon la probabilité
      // Commentaire: Retourne 'high' | 'medium' | 'low' selon les seuils.
      function classeProba(prob) {
        if (prob >= 0.7) return 'high';
        if (prob >= 0.4) return 'medium';
        return 'low';
      }

      // Fonction utilitaire: formater la date si nécessaire
      // Commentaire: Si c'est un timestamp, on tente une conversion lisible; sinon, on renvoie tel quel.
      function formaterDate(val) {
        // Heuristique simple
        if (!val) return '';
        // Si numérique plausible, convertir
        if (!isNaN(Number(val))) {
          const d = new Date(Number(val) * (Number(val) > 1e12 ? 1 : 1000)); // ms vs s
          if (!isNaN(d.getTime())) {
            return d.toLocaleString('fr-FR');
          }
        }
        return String(val);
      }

      // Fonction: afficher une erreur utilisateur
      // Commentaire: Montre un bloc erreur avec le message fourni.
      function afficherErreur(msg) {
        const el = document.getElementById('error');
        el.textContent = msg;
        el.style.display = 'block';
      }

      // Fonction: effacer l'erreur affichée
      // Commentaire: Cache le bloc erreur.
      function effacerErreur() {
        const el = document.getElementById('error');
        el.textContent = '';
        el.style.display = 'none';
      }

      // Fonction: rendre les lignes du tableau à partir des données
      // Commentaire: Construit les <tr> avec les champs match, ligue, date, probabilité.
      function rendreTable(data) {
        const tbody = document.getElementById('tbody');
        tbody.innerHTML = '';
        for (const m of data) {
          const tr = document.createElement('tr');
          const tdMatch = document.createElement('td');
          const tdLeague = document.createElement('td');
          const tdDate = document.createElement('td');
          const tdProba = document.createElement('td');

          tdMatch.textContent = m.players || m.match_id || '';
          tdLeague.innerHTML = `<span class="pill league">${m.league || ''}</span>`;
          tdDate.textContent = formaterDate(m.match_date);

          const c = classeProba(Number(m.probability));
          tdProba.innerHTML = `<span class="proba ${c}">${(Number(m.probability) * 100).toFixed(1)}%</span>`;

          tr.appendChild(tdMatch);
          tr.appendChild(tdLeague);
          tr.appendChild(tdDate);
          tr.appendChild(tdProba);
          tbody.appendChild(tr);
        }
      }

      // Fonction: récupérer les matchs depuis l'API avec tri côté serveur
      // Commentaire: Appelle /matchlist/get.php?sort=asc|desc et met à jour la table.
      async function chargerMatches(sort = 'desc') {
        effacerErreur();
        document.getElementById('status').textContent = 'Chargement…';
        try {
          const resp = await fetch(`get.php?sort=${encodeURIComponent(sort)}`);
          if (!resp.ok) throw new Error(`Statut HTTP ${resp.status}`);
          const json = await resp.json();
          if (json.status !== 'success') {
            throw new Error(json.message || 'Réponse API invalide');
          }
          // Double sécurité: appliquer un tri client selon la proba
          const data = Array.isArray(json.data) ? json.data.slice() : [];
          data.sort((a, b) => sort === 'asc' ? Number(a.probability) - Number(b.probability) : Number(b.probability) - Number(a.probability));
          rendreTable(data);
          document.getElementById('status').textContent = `Chargé (${data.length} matchs) — tri ${sort.toUpperCase()}`;
        } catch (e) {
          afficherErreur(`Échec de chargement: ${e.message}`);
          document.getElementById('status').textContent = 'Erreur';
        }
      }

      // Initialisation: brancher les boutons et charger en décroissant
      // Commentaire: Ajoute les écouteurs d’événements et déclenche le premier chargement.
      window.addEventListener('DOMContentLoaded', () => {
        document.getElementById('sortDesc').addEventListener('click', () => chargerMatches('desc'));
        document.getElementById('sortAsc').addEventListener('click', () => chargerMatches('asc'));
        chargerMatches('desc');
      });
    </script>
  </body>
</html>
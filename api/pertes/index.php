<?php
// Interface front pour afficher et modifier les pertes des tables 0_perte et 0_perte1SET
// Toutes les chaînes et commentaires sont en français.
?>
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Gestion des pertes</title>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #f7f7fa; color: #222; }
      header { background: #20232a; color: #fff; padding: 16px 20px; }
      header h1 { margin: 0; font-size: 18px; }
      main { padding: 20px; }
      .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
      .tab { padding: 8px 12px; border-radius: 6px; border: 1px solid #ccc; background: #fff; cursor: pointer; }
      .tab.active { background: #111827; color: #fff; border-color: #111827; }
      .status { margin-left: 8px; font-size: 12px; color: #555; }
      .error { color: #b91c1c; background: #fee2e2; border: 1px solid #fecaca; padding: 10px; border-radius: 8px; margin-bottom: 12px; }
      table { width: 100%; border-collapse: collapse; background: #fff; }
      thead th { text-align: left; background: #fafafa; border-bottom: 1px solid #e5e7eb; padding: 10px; font-weight: 600; }
      tbody td { border-top: 1px solid #f0f0f0; padding: 10px; vertical-align: middle; }
      input[type="number"] { width: 120px; padding: 6px; }
      button.save { padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; margin-right: 8px; }
      button.save:hover { background: #f0f0f3; }
      button.save.danger { color: #b91c1c; border-color: #fecaca; }
      button.save.danger:hover { background: #fee2e2; }
      .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
      .pill.league { background: #eef2ff; color: #3730a3; border: 1px solid #e0e7ff; }
      footer { margin-top: 20px; font-size: 12px; color: #666; }
      @media (max-width: 720px) { thead { display: none; } tbody tr { display: block; margin-bottom: 12px; } tbody td { display: flex; justify-content: space-between; } }
    </style>
  </head>
  <body>
    <header>
      <h1>Gestion des pertes</h1>
    </header>
    <main>
      <div class="tabs">
        <button id="tabNormal" class="tab active" data-type="normal">Pertes normales (table 0_perte)</button>
        <button id="tab1Set" class="tab" data-type="1set">Pertes 1 Set (table 0_perte1SET)</button>
        <span class="status" id="status">Prêt</span>
      </div>

      <div id="error" class="error" style="display:none"></div>

      <!-- Formulaire d'ajout pour pertes normales -->
      <section aria-label="Ajouter une perte normale" id="sectionAddNormal">
        <h3>Ajouter une perte (0_perte)</h3>
        <div class="form-row">
          <label>WantWin
            <input type="number" id="normalWantWin" step="0.01" placeholder="0" />
          </label>
          <label>Mise
            <input type="number" id="normalMise" step="0.01" placeholder="0" />
          </label>
          <label>Perte
            <input type="number" id="normalPerte" step="0.01" placeholder="0" />
          </label>
          <button class="save" id="btnAddNormal">Ajouter</button>
        </div>
      </section>

      <section id="sectionNormal" aria-label="Pertes normales">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>WantWin</th>
              <th>Mise</th>
              <th>Perte</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="tbodyNormal"></tbody>
        </table>
      </section>

      <!-- Formulaire d'ajout pour pertes 1 Set -->
      <section aria-label="Ajouter une perte 1 Set" style="display:none" id="sectionAdd1Set">
        <h3>Ajouter une perte (0_perte1SET)</h3>
        <div class="form-row">
          <label>WantWin
            <input type="number" id="setWantWin" step="0.01" placeholder="0" />
          </label>
          <label>Mise
            <input type="number" id="setMise" step="0.01" placeholder="0" />
          </label>
          <label>Ligue
            <input type="text" id="setLigue" placeholder="Ligue" />
          </label>
          <label>Perte
            <input type="number" id="setPerte" step="0.01" placeholder="0" />
          </label>
          <button class="save" id="btnAdd1Set">Ajouter</button>
        </div>
      </section>

      <section id="section1Set" aria-label="Pertes 1 Set" style="display:none">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>WantWin</th>
              <th>Mise</th>
              <th>Ligue</th>
              <th>Créé le</th>
              <th>Perte</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="tbody1Set"></tbody>
        </table>
      </section>

      <footer>
        API: <code>pertes/get.php</code> et <code>pertes/update.php</code> — édition en ligne du champ <strong>perte</strong>.
      </footer>
    </main>

    <script>
      // Fonction: afficher un message d'erreur
      // Commentaire: Affiche un message dans le bloc erreur et met le statut à Erreur.
      function afficherErreur(msg) {
        const el = document.getElementById('error');
        el.textContent = msg;
        el.style.display = 'block';
        document.getElementById('status').textContent = 'Erreur';
      }

      // Fonction: effacer le message d'erreur
      // Commentaire: Cache le bloc erreur et remet le statut à prêt.
      function effacerErreur() {
        const el = document.getElementById('error');
        el.textContent = '';
        el.style.display = 'none';
        document.getElementById('status').textContent = 'Prêt';
      }

      // Fonction: basculer l'onglet affiché
      // Commentaire: Active l'onglet choisi et affiche la section correspondante.
      function activerOnglet(type) {
        document.getElementById('tabNormal').classList.toggle('active', type === 'normal');
        document.getElementById('tab1Set').classList.toggle('active', type === '1set');
        document.getElementById('sectionNormal').style.display = (type === 'normal') ? '' : 'none';
        document.getElementById('section1Set').style.display = (type === '1set') ? '' : 'none';
      }

      // Fonction: charger les données depuis l'API
      // Commentaire: Appelle pertes/get.php avec le type (normal|1set) et rend le tableau.
      async function charger(type) {
        effacerErreur();
        document.getElementById('status').textContent = 'Chargement…';
        try {
          const resp = await fetch(`get.php?type=${encodeURIComponent(type)}`);
          if (!resp.ok) throw new Error(`Statut HTTP ${resp.status}`);
          const json = await resp.json();
          if (json.status !== 'success') throw new Error(json.message || 'Réponse API invalide');
          if (type === 'normal') rendreNormal(json.data || []);
          else rendre1Set(json.data || []);
          document.getElementById('status').textContent = `Chargé (${(json.data||[]).length} lignes)`;
        } catch (e) {
          afficherErreur(`Échec de chargement: ${e.message}`);
        }
      }

      // Fonction: rendre le tableau pour pertes normales
      // Commentaire: Construit chaque ligne avec input de perte et bouton Enregistrer.
      function rendreNormal(rows) {
        const tbody = document.getElementById('tbodyNormal');
        tbody.innerHTML = '';
        if (!rows || rows.length === 0) {
          const tr = document.createElement('tr');
          const td = document.createElement('td');
          td.colSpan = 5;
          td.textContent = "Aucune ligne — utilisez le formulaire ci-dessus pour ajouter une perte.";
          tr.appendChild(td);
          tbody.appendChild(tr);
          return;
        }
        for (const r of rows) {
          const tr = document.createElement('tr');
          const tdId = document.createElement('td'); tdId.textContent = r.id;
          const tdWantWin = document.createElement('td'); tdWantWin.textContent = r.wantwin;
          const tdMise = document.createElement('td'); tdMise.textContent = r.mise;
          const tdPerte = document.createElement('td');
          const input = document.createElement('input'); input.type = 'number'; input.step = '0.01'; input.value = r.perte;
          tdPerte.appendChild(input);
          const tdAction = document.createElement('td');
          const btn = document.createElement('button'); btn.className = 'save'; btn.textContent = 'Enregistrer';
          btn.addEventListener('click', () => enregistrer('normal', r.id, Number(input.value), btn));
          const btnDel = document.createElement('button'); btnDel.className = 'save danger'; btnDel.textContent = 'Supprimer';
          btnDel.addEventListener('click', () => supprimer('normal', r.id, btnDel));
          tdAction.appendChild(btn);
          tdAction.appendChild(btnDel);
          tr.appendChild(tdId); tr.appendChild(tdWantWin); tr.appendChild(tdMise); tr.appendChild(tdPerte); tr.appendChild(tdAction);
          tbody.appendChild(tr);
        }
      }

      // Fonction: rendre le tableau pour pertes 1 Set
      // Commentaire: Construit chaque ligne avec colonnes supplémentaires et édition de perte.
      function rendre1Set(rows) {
        const tbody = document.getElementById('tbody1Set');
        tbody.innerHTML = '';
        if (!rows || rows.length === 0) {
          const tr = document.createElement('tr');
          const td = document.createElement('td');
          td.colSpan = 7;
          td.textContent = "Aucune ligne — utilisez le formulaire ci-dessus pour ajouter une perte.";
          tr.appendChild(td);
          tbody.appendChild(tr);
          return;
        }
        for (const r of rows) {
          const tr = document.createElement('tr');
          const tdId = document.createElement('td'); tdId.textContent = r.id;
          const tdWantWin = document.createElement('td'); tdWantWin.textContent = r.wantwin;
          const tdMise = document.createElement('td'); tdMise.textContent = r.mise;
          const tdLeague = document.createElement('td'); tdLeague.innerHTML = `<span class="pill league">${r.ligue || ''}</span>`;
          const tdCreated = document.createElement('td'); tdCreated.textContent = r.created_at || '';
          const tdPerte = document.createElement('td');
          const input = document.createElement('input'); input.type = 'number'; input.step = '0.01'; input.value = r.perte;
          tdPerte.appendChild(input);
          const tdAction = document.createElement('td');
          const btn = document.createElement('button'); btn.className = 'save'; btn.textContent = 'Enregistrer';
          btn.addEventListener('click', () => enregistrer('1set', r.id, Number(input.value), btn));
          const btnDel = document.createElement('button'); btnDel.className = 'save danger'; btnDel.textContent = 'Supprimer';
          btnDel.addEventListener('click', () => supprimer('1set', r.id, btnDel));
          tdAction.appendChild(btn);
          tdAction.appendChild(btnDel);
          tr.appendChild(tdId); tr.appendChild(tdWantWin); tr.appendChild(tdMise); tr.appendChild(tdLeague); tr.appendChild(tdCreated); tr.appendChild(tdPerte); tr.appendChild(tdAction);
          tbody.appendChild(tr);
        }
      }

      // Fonction: envoyer la mise à jour de perte
      // Commentaire: POST JSON vers pertes/update.php pour sauvegarder la nouvelle valeur.
      async function enregistrer(type, id, perte, bouton) {
        effacerErreur();
        const oldText = bouton.textContent; bouton.textContent = '…'; bouton.disabled = true;
        try {
          const resp = await fetch('update.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, id, perte })
          });
          if (!resp.ok) throw new Error(`Statut HTTP ${resp.status}`);
          const json = await resp.json();
          if (json.status !== 'success') throw new Error(json.message || 'Échec enregistrement');
          bouton.textContent = 'OK';
          setTimeout(() => { bouton.textContent = oldText; bouton.disabled = false; }, 600);
        } catch (e) {
          bouton.textContent = oldText; bouton.disabled = false;
          afficherErreur(`Échec d'enregistrement: ${e.message}`);
        }
      }

      // Fonction: ajouter une nouvelle perte
      // Commentaire: POST JSON vers pertes/insert.php, puis recharge le tableau du type actif.
      async function ajouter(type, payload, bouton) {
        effacerErreur();
        const oldText = bouton.textContent; bouton.textContent = '…'; bouton.disabled = true;
        try {
          const resp = await fetch('insert.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, ...payload })
          });
          if (!resp.ok) throw new Error(`Statut HTTP ${resp.status}`);
          const json = await resp.json();
          if (json.status !== 'success') throw new Error(json.message || 'Échec ajout');
          bouton.textContent = 'OK';
          setTimeout(() => { bouton.textContent = 'Ajouter'; bouton.disabled = false; }, 600);
          // Recharger la vue courante
          charger(type);
        } catch (e) {
          bouton.textContent = 'Ajouter'; bouton.disabled = false;
          afficherErreur(`Échec d'ajout: ${e.message}`);
        }
      }

      // Fonction: supprimer une ligne de perte
      // Commentaire: Demande confirmation, POST JSON vers pertes/delete.php, recharge le tableau.
      async function supprimer(type, id, bouton) {
        effacerErreur();
        if (!confirm('Confirmer la suppression de cette ligne ?')) return;
        const oldText = bouton.textContent; bouton.textContent = '…'; bouton.disabled = true;
        try {
          const resp = await fetch('delete.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, id })
          });
          if (!resp.ok) throw new Error(`Statut HTTP ${resp.status}`);
          const json = await resp.json();
          if (json.status !== 'success') throw new Error(json.message || 'Échec suppression');
          bouton.textContent = 'OK';
          setTimeout(() => { bouton.textContent = 'Supprimer'; bouton.disabled = false; }, 600);
          charger(type);
        } catch (e) {
          bouton.textContent = 'Supprimer'; bouton.disabled = false;
          afficherErreur(`Échec de suppression: ${e.message}`);
        }
      }

      // Initialisation: brancher les onglets et charger la vue par défaut
      // Commentaire: Active l'onglet Normal et charge ses données.
      window.addEventListener('DOMContentLoaded', () => {
        document.getElementById('tabNormal').addEventListener('click', () => { activerOnglet('normal'); charger('normal'); });
        document.getElementById('tab1Set').addEventListener('click', () => { activerOnglet('1set'); charger('1set'); });
        // Boutons d'ajout
        document.getElementById('btnAddNormal').addEventListener('click', () => {
          const payload = {
            wantwin: Number(document.getElementById('normalWantWin').value || 0),
            mise: Number(document.getElementById('normalMise').value || 0),
            perte: Number(document.getElementById('normalPerte').value || 0),
          };
          ajouter('normal', payload, document.getElementById('btnAddNormal'));
        });
        document.getElementById('btnAdd1Set').addEventListener('click', () => {
          const payload = {
            wantwin: Number(document.getElementById('setWantWin').value || 0),
            mise: Number(document.getElementById('setMise').value || 0),
            ligue: String(document.getElementById('setLigue').value || ''),
            perte: Number(document.getElementById('setPerte').value || 0),
          };
          ajouter('1set', payload, document.getElementById('btnAdd1Set'));
        });
        // Initialisation par défaut
        activerOnglet('normal');
        charger('normal');
        // Afficher le formulaire 1 Set quand l'onglet est actif
        const toggleAddForms = () => {
          const typeActive = document.getElementById('tab1Set').classList.contains('active') ? '1set' : 'normal';
          document.getElementById('sectionAdd1Set').style.display = (typeActive === '1set') ? '' : 'none';
          document.getElementById('sectionAddNormal').style.display = (typeActive === 'normal') ? '' : 'none';
        };
        document.getElementById('tabNormal').addEventListener('click', toggleAddForms);
        document.getElementById('tab1Set').addEventListener('click', toggleAddForms);
        toggleAddForms();
      });
    </script>
  </body>
</html>
<?php
// Page d’accueil: boutons vers les interfaces Pertes et Matchlist
?>
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Accueil</title>
    <style>
      :root { color-scheme: light dark; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 0; display: grid; place-items: center; min-height: 100vh; background: #f7f7fb; }
      .card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); width: 92%; max-width: 640px; }
      h1 { margin: 0 0 16px; font-size: 20px; }
      p { margin: 0 0 20px; color: #6b7280; }
      .actions { display: flex; gap: 12px; flex-wrap: wrap; }
      a.btn { display: inline-block; padding: 12px 18px; border-radius: 10px; text-decoration: none; border: 1px solid #e5e7eb; background: #fff; color: #111827; }
      a.btn:hover { background: #f3f4f6; }
      .btn.primary { background: #111827; color: #fff; border-color: #111827; }
      .btn.primary:hover { background: #000; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>Accueil</h1>
      <p>Choisissez une interface :</p>
      <div class="actions">
        <a class="btn primary" href="pertes/index.php">Ouvrir Pertes</a>
        <a class="btn" href="matchlist/list.php">Ouvrir Matchlist</a>
      </div>
    </div>
  </body>
</html>
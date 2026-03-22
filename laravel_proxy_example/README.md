# Example Internal Proxy for SofaScore

Place these files into your Laravel project to expose a simple internal proxy endpoint
that `getprobas` can call via `PROXY_URL` (e.g. `http://api.auxotracker/internal/proxy?u=<url>`).

Steps:

1. Copier `InternalProxyController.php` dans `app/Http/Controllers/` de votre projet Laravel.
2. Ajouter la route (voir `routes_snippet.txt`) dans `routes/web.php` ou `routes/api.php`.
3. Redémarrer le container Laravel `api.auxotracker`.
4. Vérifier en appelant depuis le host ou un autre container:

```bash
curl "http://api.auxotracker/internal/proxy?u=https://www.sofascore.com/api/v1/sport/tennis/scheduled-events/2026-03-07"
```

Sécurité et recommandations:
- Ne laissez ce proxy ouvert publiquement: restreignez l'accès via le réseau Docker (utiliser `shared_network`) ou via auth middleware.
- Validez et restreignez les hôtes autorisés (liste `allowed_hosts` dans le controller).
- Ajoutez un mécanisme de cache / rate-limit pour éviter d'épuiser la source.

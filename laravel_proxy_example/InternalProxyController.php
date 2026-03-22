<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class InternalProxyController extends Controller
{
    /**
     * Proxy GET simple qui récupère l'URL passée en paramètre `u`
     * Usage: /internal/proxy?u=https://www.sofascore.com/...
     */
    public function proxy(Request $request)
    {
        $u = $request->query('u');
        if (!$u) {
            return response('Missing parameter u', 400);
        }

        // Valider l'URL cible (très important pour sécurité)
        $allowed_hosts = ['www.sofascore.com', 'api.sofascore.com', 'sofascorerelated.example'];
        $host = parse_url($u, PHP_URL_HOST);
        if (!$host || !in_array($host, $allowed_hosts, true)) {
            return response('Host not allowed', 403);
        }

        // Forward request en conservant quelques headers utiles
        $headers = [
            'User-Agent' => $request->header('User-Agent', 'Mozilla/5.0'),
            'Accept' => 'application/json, text/plain, */*',
            'Referer' => 'https://www.sofascore.com',
        ];

        // Optionnel: ajouter timeout et retry si besoin
        $resp = Http::withHeaders($headers)
            ->timeout(20)
            ->get($u);

        // Copier certains headers de réponse si nécessaire
        $response = response($resp->body(), $resp->status());
        // Ne pas exposer tous les headers sensibles
        $forward_headers = ['Content-Type', 'Cache-Control', 'Expires'];
        foreach ($forward_headers as $h) {
            if ($resp->header($h)) {
                $response->header($h, $resp->header($h));
            }
        }

        return $response;
    }
}

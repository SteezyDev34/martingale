# -*- coding: utf-8 -*-
"""
OneXBetBridge — pipeline partagé "recherche de match → sélection de marché(s)"
pour 1xBet via l'extension Chrome (websocket_server.ExtensionBridge).

Utilisé par Functions/PlacerPari.py (watcher Telegram) et
Functions/Bookmakers/XBetScraper.py (router loop), pour ne pas dupliquer
la logique de recherche/sélection.

Ne place PAS la mise et ne valide PAS le pari : ça reste à l'appelant via
bridge.place_bet(mise=...) puis bridge.validate_bet(), pour rester symétrique
avec l'interface fetch_odds/run des autres scrapers.
"""

import time

from Functions.getTextFromImageGPT import compare_match_name, compare_selection


def _bridge():
    from websocket_server import bridge
    return bridge


def _search_and_open_match(equipe1, equipe2, sport_id=None, cached_url=None):
    """
    Recherche le match sur 1xBet et navigue vers sa page. Retourne l'URL ouverte,
    ou None si introuvable.

    cached_url (optionnel) : si fourni (ex: trouvé par un précédent appel de
    find_and_prepare_bet pour le même pari — fetch_odds puis placement),
    navigue directement dessus sans repasser par la recherche. Ajouté le
    2026-10-16 : fetch_odds et le placement réel font chacun leur propre
    recherche indépendante pour le même match, à quelques secondes d'intervalle
    — la deuxième échouait parfois (match_not_found) alors que la première
    venait de réussir, probablement un effet de l'état laissé par la première
    recherche sur la page. Réutiliser l'URL déjà connue évite complètement
    cette deuxième recherche redondante et peu fiable.

    NB (2026-08-26) : cliquer le bouton recherche NAVIGUE vers une page dédiée
    /search-events (ce n'est plus une modal en overlay) — cette navigation détruit
    le contexte JS en cours d'exécution si on essaie de tout faire en un seul appel
    (le fait plantait/bloquait indéfiniment). D'où les deux étapes séparées ici,
    avec une pause pour laisser le content script se réinjecter sur la nouvelle page.
    """
    b = _bridge()

    if cached_url:
        b.navigate(cached_url)
        return cached_url

    click_result = b.click_search_button()
    if not click_result.get('success'):
        return None
    time.sleep(2)

    result = b.search_on_results_page(equipe1, equipe2)
    if result.get('found'):
        # Bug trouve le 2026-10-16 : ce chemin (match trouve directement, sans
        # passer par la liste de candidats ci-dessous) ne naviguait jamais vers
        # la page du match -- selectMarketByText tournait donc sur la page de
        # recherche elle-meme, d'ou "selection_not_found" systematique malgre
        # un search_on_results_page reussi.
        url = result.get('url')
        if url:
            b.navigate(url)
            return url
        return None

    candidates = result.get('candidates') or []
    for cand in candidates:
        team1, team2, url = cand.get('team1'), cand.get('team2'), cand.get('url')
        if not (team1 and team2 and url):
            continue
        if compare_match_name(f"{team1} - {team2}", f"{equipe1} vs {equipe2}", sport_id):
            b.navigate(url)
            return url

    return None


def _select_leg(leg):
    """Sélectionne un marché unique, avec fallback IA si le texte exact n'est pas trouvé."""
    b = _bridge()
    result = b.select_market(leg['categorie'], leg['type_de_pari'], leg['selection'])
    if result.get('success'):
        return result

    candidates = result.get('candidates') or []
    if candidates:
        matched = compare_selection(leg.get('match_name', ''), leg['selection'], '[' + ','.join(candidates) + ']')
        if matched and matched != 'false':
            return b.select_market(leg['categorie'], leg['type_de_pari'], matched)

    return result


def find_and_prepare_bet(matches, cached_url=None):
    """
    Recherche le(s) match(es) et sélectionne le(s) marché(s) correspondants.
    matches: liste de legs {equipe_1, equipe_2, categorie, type_de_pari, selection, sport}
             (tous sur le même match pour un pari combiné/constructor).
    cached_url (optionnel) : voir _search_and_open_match -- évite une recherche
    redondante si l'URL du match est déjà connue (ex: fetch_odds déjà fait).

    Retourne {'success': True, 'cote': float, 'match_url': str} ou
    {'success': False, 'error': str}. match_url est renvoyé même en cas
    d'échec de sélection du marché (match trouvé mais pas le marché), pour
    permettre à l'appelant de le mettre en cache pour un appel suivant.
    """
    if not matches:
        return {'success': False, 'error': 'empty_matches'}

    first = matches[0]
    equipe1, equipe2 = first.get('equipe_1'), first.get('equipe_2')
    sport_id = first.get('sport')

    match_url = _search_and_open_match(equipe1, equipe2, sport_id, cached_url=cached_url)
    if not match_url:
        return {'success': False, 'error': 'match_not_found'}

    b = _bridge()

    if len(matches) == 1:
        leg = matches[0]
        leg = {**leg, 'match_name': f"{equipe1} vs {equipe2}"}
        result = _select_leg(leg)
        if not result.get('success'):
            return {'success': False, 'error': result.get('error', 'market_not_found'),
                    'match_url': match_url, 'candidates': result.get('candidates') or []}
        return {'success': True, 'cote': result.get('cote'), 'match_url': match_url}

    legs = [
        {
            'categorie': m.get('categorie'),
            'type_de_pari': m.get('type_de_pari'),
            'selection': m.get('selection'),
        }
        for m in matches
    ]
    result = b.select_combined_markets(legs)
    if not result.get('success'):
        # Le JS renvoie {error:'leg_failed', leg, results} -- `results` porte les
        # candidates (textes de marché réels vus) jambe par jambe.
        leg_results = result.get('results') or []
        candidates = []
        for r in leg_results:
            if isinstance(r, dict) and r.get('candidates'):
                candidates.extend(r['candidates'])
        return {'success': False, 'error': result.get('error', 'combined_market_not_found'),
                'match_url': match_url, 'candidates': candidates, 'failed_leg': result.get('leg')}
    return {'success': True, 'cote': None, 'match_url': match_url}

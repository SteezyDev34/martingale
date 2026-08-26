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


def _search_and_open_match(equipe1, equipe2, sport_id=None):
    """
    Recherche le match sur 1xBet et navigue vers sa page. Retourne True/False.

    NB (2026-08-26) : cliquer le bouton recherche NAVIGUE vers une page dédiée
    /search-events (ce n'est plus une modal en overlay) — cette navigation détruit
    le contexte JS en cours d'exécution si on essaie de tout faire en un seul appel
    (le fait plantait/bloquait indéfiniment). D'où les deux étapes séparées ici,
    avec une pause pour laisser le content script se réinjecter sur la nouvelle page.
    """
    b = _bridge()
    click_result = b.click_search_button()
    if not click_result.get('success'):
        return False
    time.sleep(2)

    result = b.search_on_results_page(equipe1, equipe2)
    if result.get('found'):
        return True

    candidates = result.get('candidates') or []
    for cand in candidates:
        team1, team2, url = cand.get('team1'), cand.get('team2'), cand.get('url')
        if not (team1 and team2 and url):
            continue
        if compare_match_name(f"{team1} - {team2}", f"{equipe1} vs {equipe2}", sport_id):
            b.navigate(url)
            return True

    return False


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


def find_and_prepare_bet(matches):
    """
    Recherche le(s) match(es) et sélectionne le(s) marché(s) correspondants.
    matches: liste de legs {equipe_1, equipe_2, categorie, type_de_pari, selection, sport}
             (tous sur le même match pour un pari combiné/constructor).

    Retourne {'success': True, 'cote': float} ou {'success': False, 'error': str}.
    """
    if not matches:
        return {'success': False, 'error': 'empty_matches'}

    first = matches[0]
    equipe1, equipe2 = first.get('equipe_1'), first.get('equipe_2')
    sport_id = first.get('sport')

    if not _search_and_open_match(equipe1, equipe2, sport_id):
        return {'success': False, 'error': 'match_not_found'}

    b = _bridge()

    if len(matches) == 1:
        leg = matches[0]
        leg = {**leg, 'match_name': f"{equipe1} vs {equipe2}"}
        result = _select_leg(leg)
        if not result.get('success'):
            return {'success': False, 'error': result.get('error', 'market_not_found')}
        return {'success': True, 'cote': result.get('cote')}

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
        return {'success': False, 'error': result.get('error', 'combined_market_not_found')}
    return {'success': True, 'cote': None}

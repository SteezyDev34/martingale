from Functions.Functions_telegram import send_telegram
import config


def PlacerCode(code):
    """
    Charge un code coupon 1xBet et place le pari correspondant, via l'extension Chrome (bridge WebSocket).
    """
    from websocket_server import bridge

    config.scriptType = 'LIVE'
    config.site_type = 'new_site'

    bridge.delete_bet()

    result = bridge.load_coupon_code(code)
    if not result.get('success'):
        config.log(f"Erreur lors du chargement du code {code}: {result.get('error')}")
        send_telegram('-1001848207367', f"Erreur lors du placement du code : {code}")
        return False

    from Functions.GetMise import get_recommended_stake
    try:
        stake_data = get_recommended_stake()
        config.mise = round(float(stake_data.get('recommended_stake') or 0), 2) or 0.2
    except Exception as e:
        config.log(f"Mise recommandée indisponible ({e}), fallback 0.2€")
        config.mise = 0.2

    stake_result = bridge.set_stake(config.mise)
    if not stake_result.get('success'):
        send_telegram('-1001848207367', f"Erreur lors du placement du code : {code}")
        return False

    validation = bridge.validate_bet(confirm=True)
    if not validation.get('validated'):
        send_telegram('-1001848207367', f"Erreur lors du placement du code : {code}")
        return False

    return True


if __name__ == "__main__":
    from websocket_server import start_bridge

    start_bridge(wait_timeout=30)
    code = 'V82KD'
    PlacerCode(code)

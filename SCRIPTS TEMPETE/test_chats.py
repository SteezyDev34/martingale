import requests
import urllib3

urllib3.disable_warnings()
session = requests.Session()

BOT_TOKEN = '1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc'

chats = {
    'auxo_bot': '820171667',
    'channel_com2_bot': '-1001699523977',
    'group_AuxoAnalytix': '-1001672474839',
    'groupID': '-540044043',
    'alertGroup': '-1001848207367',
    'freeGroup': '-1001315247334',
    'auxoInvestGroup': '-1001441208953'
}

print('🧪 Test des chat IDs disponibles:\n')

for name, chat_id in chats.items():
    try:
        response = session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={'chat_id': chat_id, 'text': 'test connexion'},
            verify=False,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f'✅ {name} ({chat_id}): OK')
        else:
            print(f'❌ {name} ({chat_id}): Error {response.status_code}')
            
    except Exception as e:
        print(f'❌ {name} ({chat_id}): {str(e)[:50]}')

from telethon import TelegramClient
import asyncio

# Identifiants API Telegram (à adapter si besoin)
api_id = 5493357
api_hash = 'd4b28d840d67f37e8f98df2c9778bb74'

async def main():
    client = TelegramClient('scraper', api_id, api_hash)
    await client.start()
    print("Liste des canaux et groupes Telegram auxquels tu es abonné :\n")
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if hasattr(entity, 'title'):
            print(f"Nom : {entity.title}")
        if hasattr(entity, 'username') and entity.username:
            print(f"Username : @{entity.username}")
        print(f"ID : {entity.id}")
        print(f"Type : {type(entity).__name__}")
        print("---")

if __name__ == "__main__":
    asyncio.run(main())

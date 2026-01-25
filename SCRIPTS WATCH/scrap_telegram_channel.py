from telethon import TelegramClient
import json
import asyncio
import os
from pathlib import Path

# Identifiants API Telegram (à adapter si besoin)
api_id = 5493357
api_hash = 'd4b28d840d67f37e8f98df2c9778bb74'

# ID du canal à scrapper
#channel_id = 1401104509  # Identifiant du canal AdrBetting
#channel_id = 2958458505  # Identifiant du canal AdrBetting
channel_id = '@pesopalstransfers'  # Identifiant du canal AdrBetting --- IGNORE ---
# Liste des mots-clés à rechercher
keywords = [
    "XCCXCXCXCX : "
]

# Dossier pour sauvegarder les médias
MEDIA_FOLDER = "telegram_media"
os.makedirs(MEDIA_FOLDER, exist_ok=True)

async def download_media(client, message, message_folder):
    """
    Télécharge les médias (photos, vidéos, documents) d'un message.
    
    Args:
        client: Client Telegram
        message: Message à traiter
        message_folder: Dossier où sauvegarder les médias
        
    Returns:
        list: Liste des chemins des fichiers téléchargés
    """
    media_files = []
    
    try:
        if message.photo:
            # Télécharger la photo
            filename = f"photo_{message.id}.jpg"
            filepath = os.path.join(message_folder, filename)
            await client.download_media(message.photo, filepath)
            media_files.append(filename)
            print(f"   📷 Photo téléchargée: {filename}")
            
        elif message.video:
            # Télécharger la vidéo
            filename = f"video_{message.id}.mp4"
            filepath = os.path.join(message_folder, filename)
            await client.download_media(message.video, filepath)
            media_files.append(filename)
            print(f"   🎥 Vidéo téléchargée: {filename}")
            
        elif message.document:
            # Télécharger le document (GIF, fichiers, etc.)
            file_ext = "bin"
            if message.document.mime_type:
                if "image" in message.document.mime_type:
                    file_ext = message.document.mime_type.split('/')[-1]
                elif "video" in message.document.mime_type:
                    file_ext = message.document.mime_type.split('/')[-1]
                elif "gif" in message.document.mime_type:
                    file_ext = "gif"
                    
            filename = f"document_{message.id}.{file_ext}"
            filepath = os.path.join(message_folder, filename)
            await client.download_media(message.document, filepath)
            media_files.append(filename)
            print(f"   📄 Document téléchargé: {filename}")
            
        elif message.media:
            # Autres types de médias
            filename = f"media_{message.id}"
            filepath = os.path.join(message_folder, filename)
            await client.download_media(message.media, filepath)
            media_files.append(filename)
            print(f"   📎 Média téléchargé: {filename}")
            
    except Exception as e:
        print(f"   ⚠️  Erreur lors du téléchargement du média: {e}")
    
    return media_files


async def main():
    client = TelegramClient('scraper', api_id, api_hash)
    await client.start()
    messages_to_save = []

    from telethon.tl.types import PeerChannel
    from datetime import datetime, timezone
    
    # Gérer à la fois les username (@channel) et les ID numériques
    if isinstance(channel_id, str) and channel_id.startswith('@'):
        # C'est un username, on le résout directement
        print(f"🔍 Résolution du username: {channel_id}")
        entity = await client.get_entity(channel_id)
    elif isinstance(channel_id, str):
        # C'est peut-être un username sans @
        print(f"🔍 Résolution du username: @{channel_id}")
        entity = await client.get_entity(channel_id)
    else:
        # C'est un ID numérique
        print(f"🔍 Connexion au canal ID: {channel_id}")
        entity = PeerChannel(channel_id)
    
    messages_to_save = []
    count = 0
    media_count = 0
    
    date_limite = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    print(f"✅ Connecté au canal: {getattr(entity, 'title', channel_id)}")
    print(f"📅 Date limite: {date_limite}")
    print(f"🔑 Mots-clés recherchés: {keywords}")
    print("="*60)
    
    try:
        async for message in client.iter_messages(entity):
            if message.date >= date_limite:
                # Vérifier si le message contient du texte ou des médias
                has_text = message.text is not None
                has_media = message.photo or message.video or message.document or message.media
                
                if has_text or has_media:
                    # Vérifier les mots-clés si du texte existe
                    keyword_match = False
                    if has_text:
                        for keyword in keywords:
                            if keyword.lower() not in message.text.lower():
                                keyword_match = True
                                break
                    else:
                        # Si pas de texte mais des médias, on prend quand même
                        keyword_match = True
                    
                    if keyword_match:
                        count += 1
                        print(f"\n📨 Message #{count} (ID: {message.id}) - {message.date}")
                        
                        # Créer un dossier pour ce message
                        message_folder = os.path.join(MEDIA_FOLDER, f"message_{message.id}")
                        os.makedirs(message_folder, exist_ok=True)
                        
                        # Télécharger les médias
                        media_files = []
                        if has_media:
                            media_files = await download_media(client, message, message_folder)
                            if media_files:
                                media_count += len(media_files)
                        
                        # Préparer les données du message
                        message_data = {
                            "id": message.id,
                            "date": str(message.date),
                            "text": message.text if has_text else "",
                            "has_media": has_media,
                            "media_files": media_files,
                            "media_folder": message_folder if media_files else None,
                            "views": message.views if hasattr(message, 'views') else 0,
                            "forwards": message.forwards if hasattr(message, 'forwards') else 0
                        }
                        
                        messages_to_save.append(message_data)
                        
                        # Afficher un aperçu du texte
                        if has_text:
                            preview = message.text[:100] + "..." if len(message.text) > 100 else message.text
                            print(f"   💬 Texte: {preview}")
                        
        print(f"\n{'='*60}")
        print(f"✅ Total messages récupérés: {count}")
        print(f"📸 Total médias téléchargés: {media_count}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des messages : {e}")
        import traceback
        traceback.print_exc()

    # Sauvegarde dans un fichier JSON
    output_file = "messages_filtrés.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(messages_to_save, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 {len(messages_to_save)} messages sauvegardés dans {output_file}")
    print(f"📁 Médias sauvegardés dans le dossier: {MEDIA_FOLDER}")
    
    # Statistiques
    messages_with_media = sum(1 for m in messages_to_save if m['has_media'])
    messages_with_text = sum(1 for m in messages_to_save if m['text'])
    
    print(f"\n📊 Statistiques:")
    print(f"   • Messages avec texte: {messages_with_text}")
    print(f"   • Messages avec médias: {messages_with_media}")
    print(f"   • Total fichiers médias: {media_count}")

if __name__ == "__main__":
    asyncio.run(main())

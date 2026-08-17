"""
Test du bot Telegram pour identifier le problème
"""
import sys
import os

# Configuration du bot Telegram
try:
    from telegram_ssl import TelegramBotSSL
    bot = TelegramBotSSL('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
    print("✅ Bot Telegram SSL configuré")
    use_ssl_bot = True
except ImportError:
    try:
        import telepot
        bot = telepot.Bot('1910869556:AAGy6Xdbf0Uvk-tz8WFzdnPvo14fu4SOLvc')
        print("✅ Bot Telegram standard configuré")
        use_ssl_bot = False
    except ImportError:
        print("❌ Aucun module Telegram disponible")
        sys.exit(1)

freeGroup = "-1001315247334"

def test_simple_message():
    """Test avec un message simple"""
    print("\n1️⃣ Test message simple...")
    try:
        if use_ssl_bot:
            result = bot.send_message(freeGroup, "Test simple")
            print(f"✅ Succès: {result}")
        else:
            bot.sendMessage(freeGroup, "Test simple")
            print("✅ Succès")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_emoji_message():
    """Test avec emojis"""
    print("\n2️⃣ Test avec emojis...")
    try:
        if use_ssl_bot:
            result = bot.send_message(freeGroup, "🖼️ Test emoji 📝")
            print(f"✅ Succès: {result}")
        else:
            bot.sendMessage(freeGroup, "🖼️ Test emoji 📝")
            print("✅ Succès")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_url_message():
    """Test avec URL"""
    print("\n3️⃣ Test avec URL...")
    try:
        msg = "🖼️ Nouvelle image:\nhttps://tempetebetting.com/wp-content/uploads/2025/12/test.jpg"
        if use_ssl_bot:
            result = bot.send_message(freeGroup, msg)
            print(f"✅ Succès: {result}")
        else:
            bot.sendMessage(freeGroup, msg)
            print("✅ Succès")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_long_message():
    """Test avec message long"""
    print("\n4️⃣ Test message long...")
    try:
        msg = "📝 Texte:\n" + "Lorem ipsum " * 100
        if use_ssl_bot:
            result = bot.send_message(freeGroup, msg)
            print(f"✅ Succès: {result}")
        else:
            bot.sendMessage(freeGroup, msg)
            print("✅ Succès")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_multiline_message():
    """Test avec plusieurs lignes"""
    print("\n5️⃣ Test message multi-lignes...")
    try:
        msg = """🖼️ Nouvelle image:
https://tempetebetting.com/wp-content/uploads/2025/12/test.jpg

📝 Texte:
Ligne 1
Ligne 2
Ligne 3"""
        if use_ssl_bot:
            result = bot.send_message(freeGroup, msg)
            print(f"✅ Succès: {result}")
        else:
            bot.sendMessage(freeGroup, msg)
            print("✅ Succès")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_bot_info():
    """Tester les infos du bot"""
    print("\n6️⃣ Test info bot...")
    try:
        if use_ssl_bot:
            # TelegramBotSSL n'a pas de getMe
            print("⚠️  TelegramBotSSL n'a pas de méthode getMe()")
            return True
        else:
            info = bot.getMe()
            print(f"✅ Bot info: {info}")
            return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TEST DU BOT TELEGRAM")
    print("=" * 50)
    
    results = []
    
    results.append(("Simple", test_simple_message()))
    results.append(("Emoji", test_emoji_message()))
    results.append(("URL", test_url_message()))
    results.append(("Long", test_long_message()))
    results.append(("Multi-lignes", test_multiline_message()))
    results.append(("Info", test_bot_info()))
    
    print("\n" + "=" * 50)
    print("RÉSULTATS")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    total = sum(1 for _, success in results if success)
    print(f"\n📊 Total: {total}/{len(results)} tests réussis")

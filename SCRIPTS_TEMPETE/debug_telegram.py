"""
Script de debug pour tester les messages Telegram
"""

def analyze_message(text):
    """Analyse un message pour trouver les caractères problématiques"""
    print(f"\n📊 Analyse du message ({len(text)} caractères)")
    print("=" * 50)
    
    # Compter les caractères par catégorie
    control_chars = []
    printable = 0
    unicode_chars = 0
    
    for i, char in enumerate(text):
        code = ord(char)
        if code < 32 and code not in [9, 10]:  # Caractères de contrôle
            control_chars.append((i, char, code, repr(char)))
        elif 32 <= code <= 126:
            printable += 1
        elif code > 127:
            unicode_chars += 1
    
    print(f"✅ Caractères imprimables: {printable}")
    print(f"🌍 Caractères Unicode: {unicode_chars}")
    print(f"❌ Caractères de contrôle: {len(control_chars)}")
    
    if control_chars:
        print("\n⚠️  Caractères de contrôle trouvés:")
        for pos, char, code, repr_char in control_chars[:10]:  # Premiers 10
            print(f"  Position {pos}: code={code} repr={repr_char}")
    
    # Vérifier la longueur
    if len(text) > 4096:
        print(f"\n⚠️  Message trop long: {len(text)} > 4096")
    else:
        print(f"\n✅ Longueur OK: {len(text)} <= 4096")
    
    # Compter les lignes
    lines = text.count('\n')
    print(f"📝 Nombre de lignes: {lines}")
    
    return len(control_chars) == 0 and len(text) <= 4096


def clean_message_for_telegram(msg):
    """Nettoie un message pour Telegram (copie de la fonction du script)"""
    if not msg:
        return "Message vide"
    
    msg = str(msg).strip()
    
    # Remplacer les caractères de contrôle problématiques
    cleaned_chars = []
    for char in msg:
        code = ord(char)
        if code == 10 or code == 9 or code == 32 or (33 <= code <= 126) or code > 127:
            cleaned_chars.append(char)
        elif code < 32 and code not in [9, 10]:
            continue
    
    msg = ''.join(cleaned_chars)
    msg = msg.replace('\r\n', '\n').replace('\r', '\n')
    
    while '\n\n\n' in msg:
        msg = msg.replace('\n\n\n', '\n\n')
    
    if len(msg) > 4096:
        msg = msg[:4090] + "\n..."
    
    return msg


if __name__ == "__main__":
    # Test avec un message problématique
    test_message = "🖼️ Test\x00\x01\x02 message avec caractères\nde contrôle"
    
    print("MESSAGE ORIGINAL:")
    print(repr(test_message))
    
    analyze_message(test_message)
    
    print("\n" + "=" * 50)
    print("MESSAGE NETTOYÉ:")
    cleaned = clean_message_for_telegram(test_message)
    print(repr(cleaned))
    
    analyze_message(cleaned)

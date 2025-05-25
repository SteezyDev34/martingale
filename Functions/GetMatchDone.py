import chardet


# Détecte l'encodage réel du fichier
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'


# RÉCUPÉRER LES MATCHS EFFECTUÉS
def main(matchlist_file_name):
    file_path = matchlist_file_name + ".txt"
    encoding = detect_encoding(file_path)

    try:
        with open(file_path, "r", encoding=encoding) as f:
            match_list = f.read().splitlines()
    except UnicodeDecodeError as e:
        print(f"Erreur de décodage du fichier '{file_path}': {e}")
        return []

    return match_list

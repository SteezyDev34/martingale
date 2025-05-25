import chardet


def main(action, values, matchlist_file_name):
    if action == "add":
        newmatch = values
        with open(matchlist_file_name + ".txt", "a", encoding="utf-8") as f:
            f.write("\n" + str(newmatch))
    elif action == "del":
        with open(matchlist_file_name + ".txt", "r", encoding="utf-8") as f:
            content = f.read()
        match_list = content.replace("\n" + str(values), "")
        with open(matchlist_file_name + ".txt", "w", encoding="utf-8") as f:
            f.write(match_list)


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'


def todo(action, values, matchlisttodo_file_name):
    file_path = matchlisttodo_file_name + ".txt"

    # Pour toutes les lectures, détecter l'encodage réel
    encoding = detect_encoding(file_path)

    if action == "add":
        try:
            with open(file_path, "r", encoding=encoding) as file:
                existing_matches = file.read().splitlines()
        except UnicodeDecodeError as e:
            print(f"Erreur de lecture : {e}")
            return

        if str(values) in existing_matches:
            print(f"L'élément '{values}' existe déjà dans le fichier.")
        else:
            with open(file_path, "a", encoding="utf-8") as file:  # on écrit en utf-8
                file.write("\n" + str(values))
            print(f"L'élément '{values}' a été ajouté avec succès.")

    elif action == "del":
        try:
            with open(file_path, "r", encoding=encoding) as file:
                existing_matches = file.read().splitlines()
        except UnicodeDecodeError as e:
            print(f"Erreur de lecture : {e}")
            return

        if str(values) in existing_matches:
            updated_matches = [match for match in existing_matches if match != str(values)]
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(updated_matches))
            print(f"L'élément '{values}' a été supprimé avec succès.")
        else:
            print(f"L'élément '{values}' n'existe pas dans le fichier.")

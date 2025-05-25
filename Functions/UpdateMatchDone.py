# UpdateMatchDone
# MISE A JOUR DES MATCHS EFFECTUÉS
import chardet


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
        return result['encoding'] or 'utf-8'


def main(action, values, matchlist_file_name):
    file_path = matchlist_file_name + ".txt"
    encoding = detect_encoding(file_path) if action == "del" else "utf-8"

    if action == "add":
        newmatch = values
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("\n" + str(newmatch))
    elif action == "del":
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
        match_list = content.replace("\n" + str(values), "")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(match_list)


def todo(action, values, matchlisttodo_file_name):
    file_path = matchlisttodo_file_name + ".txt"
    encoding = detect_encoding(file_path)

    if action == "add":
        with open(file_path, "r", encoding=encoding) as file:
            existing_matches = file.read().splitlines()

        if str(values) in existing_matches:
            print(f"L'élément '{values}' existe déjà dans le fichier.")
        else:
            with open(file_path, "a", encoding="utf-8") as file:
                file.write("\n" + str(values))
            print(f"L'élément '{values}' a été ajouté avec succès.")

    elif action == "del":
        with open(file_path, "r", encoding=encoding) as file:
            existing_matches = file.read().splitlines()

        if str(values) in existing_matches:
            updated_matches = [match for match in existing_matches if match != str(values)]
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(updated_matches))
            print(f"L'élément '{values}' a été supprimé avec succès.")
        else:
            print(f"L'élément '{values}' n'existe pas dans le fichier.")

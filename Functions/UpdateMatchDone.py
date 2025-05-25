# UpdateMatchDone
# MISE A JOUR DES MATCHS EFFECTUÉS
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


def todo(action, values, matchlisttodo_file_name):
    file_path = matchlisttodo_file_name + ".txt"

    if action == "add":
        # Lire le contenu existant
        with open(file_path, "r", encoding="utf-8") as file:
            existing_matches = file.read().splitlines()

        # Vérifier si l'élément existe déjà
        if str(values) in existing_matches:
            print(f"L'élément '{values}' existe déjà dans le fichier.")
        else:
            # Ajouter le nouvel élément
            with open(file_path, "a", encoding="utf-8") as file:
                file.write("\n" + str(values))
            print(f"L'élément '{values}' a été ajouté avec succès.")

    elif action == "del":
        # Lire le contenu existant
        with open(file_path, "r", encoding="utf-8") as file:
            existing_matches = file.read().splitlines()

        # Supprimer l'élément s'il existe
        if str(values) in existing_matches:
            updated_matches = [match for match in existing_matches if match != str(values)]
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(updated_matches))
            print(f"L'élément '{values}' a été supprimé avec succès.")
        else:
            print(f"L'élément '{values}' n'existe pas dans le fichier.")

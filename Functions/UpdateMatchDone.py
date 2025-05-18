# UpdateMatchDone
# MISE A JOUR DES MATCHS EFFECTUÉS
def main(action, values, matchlist_file_name):
    if action == "add":
        newmatch = values
        get_matchlist_file = open(matchlist_file_name + ".txt", "a")
        get_matchlist_file.write(
            "\n" + str(newmatch))
        get_matchlist_file.close()
    elif action == "del":
        get_matchlist_file = open(matchlist_file_name + ".txt", "r")
        get_matchlist = get_matchlist_file.read()
        get_matchlist_file.close()
        match_list = get_matchlist.replace("\n" + str(values), "")
        get_matchlist_file = open(matchlist_file_name + ".txt", "w")
        get_matchlist_file.write(match_list)
        get_matchlist_file.close()


def todo(action, values, matchlisttodo_file_name):
    file_path = matchlisttodo_file_name + ".txt"

    if action == "add":
        # Lire le contenu existant
        with open(file_path, "r") as file:
            existing_matches = file.read().splitlines()

        # Vérifier si l'élément existe déjà
        if str(values) in existing_matches:
            print(f"L'élément '{values}' existe déjà dans le fichier.")
        else:
            # Ajouter le nouvel élément
            with open(file_path, "a") as file:
                file.write("\n" + str(values))
            print(f"L'élément '{values}' a été ajouté avec succès.")

    elif action == "del":
        # Lire le contenu existant
        with open(file_path, "r") as file:
            existing_matches = file.read().splitlines()

        # Supprimer l'élément s'il existe
        if str(values) in existing_matches:
            updated_matches = [match for match in existing_matches if match != str(values)]
            with open(file_path, "w") as file:
                file.write("\n".join(updated_matches))
            print(f"L'élément '{values}' a été supprimé avec succès.")
        else:
            print(f"L'élément '{values}' n'existe pas dans le fichier.")

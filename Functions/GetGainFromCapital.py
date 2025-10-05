def max_gain_pour_16_tours(solde_initial, cote=2.4, tours_max=16):
    """
    Calcule le gain net maximum atteignable par victoire
    pour pouvoir tenir jusqu'au nombre de tours défini (ex: 16).
    """
    print(f"Avec un capital de {capital}€ et une cote de {cote},")

    # On cherche par dichotomie (recherche binaire)
    bas, haut = 0.01, solde_initial  # encadrement du gain visé
    precision = 0.01  # arrondi à 1 centime

    def cout_total(gain_souhaite):
        pertes_cumulees = 0
        total_mises = 0
        for _ in range(tours_max):
            mise = (pertes_cumulees + gain_souhaite) / (cote - 1)
            total_mises += mise
            pertes_cumulees += mise
        return total_mises

    # Recherche du maximum possible
    while haut - bas > precision:
        milieu = (bas + haut) / 2
        if cout_total(milieu) <= solde_initial:
            bas = milieu
        else:
            haut = milieu
    gain_max = round(bas, 2)
    print(f"➡️ tu peux viser au maximum {gain_max}€ net par victoire en martingale sur {tours_max} tours.")
    return gain_max
if __name__ == '__main__':
    capital = 11000
    cote = 2.4
    
    gain_max = max_gain_pour_16_tours(capital, cote, 15)

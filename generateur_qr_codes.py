#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de QR Codes 2D - Format 116 DOCE
16 QR codes disposés en carré 4x4

Auteur: Générateur automatisé
Date: 11 novembre 2025
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
from datetime import datetime

def generer_donnees_qr(index):
    """
    Génère les données pour chaque QR code.
    
    Args:
        index (int): Index du QR code (0-15)
    
    Returns:
        str: Données à encoder dans le QR code
    """
    # Format 116 DOCE - Génération des données uniques
    base_data = f"116DOCE{index:02d}"
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    return f"{base_data}-{timestamp}-{index * 17 + 23:04d}"

def creer_qr_code(data, taille=150):
    """
    Crée un QR code individuel.
    
    Args:
        data (str): Données à encoder
        taille (int): Taille du QR code en pixels
    
    Returns:
        PIL.Image: Image du QR code
    """
    qr = qrcode.QRCode(
        version=1,  # Contrôle la taille du QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Créer l'image du QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Redimensionner à la taille souhaitée
    img = img.resize((taille, taille), Image.Resampling.LANCZOS)
    
    return img

def assembler_grille_qr(qr_images, espacement=10):
    """
    Assemble les 16 QR codes en grille 4x4.
    
    Args:
        qr_images (list): Liste des images QR codes
        espacement (int): Espacement entre les QR codes
    
    Returns:
        PIL.Image: Image finale avec la grille 4x4
    """
    if len(qr_images) != 16:
        raise ValueError("Il faut exactement 16 QR codes pour créer une grille 4x4")
    
    # Dimensions de chaque QR code
    qr_size = qr_images[0].size[0]
    
    # Dimensions de l'image finale
    grid_width = 4 * qr_size + 3 * espacement
    grid_height = 4 * qr_size + 3 * espacement
    
    # Créer une nouvelle image blanche
    grid_image = Image.new('RGB', (grid_width, grid_height), 'white')
    
    # Coller chaque QR code à sa position
    for i in range(16):
        row = i // 4
        col = i % 4
        
        x = col * (qr_size + espacement)
        y = row * (qr_size + espacement)
        
        grid_image.paste(qr_images[i], (x, y))
    
    return grid_image

def ajouter_etiquettes(grid_image, qr_data_list, espacement=10):
    """
    Ajoute des étiquettes avec les données sous chaque QR code.
    
    Args:
        grid_image (PIL.Image): Image de la grille
        qr_data_list (list): Liste des données des QR codes
        espacement (int): Espacement utilisé
    
    Returns:
        PIL.Image: Image avec étiquettes
    """
    # Calculer la nouvelle hauteur avec les étiquettes
    label_height = 30
    new_height = grid_image.height + label_height
    
    # Créer une nouvelle image plus grande
    labeled_image = Image.new('RGB', (grid_image.width, new_height), 'white')
    labeled_image.paste(grid_image, (0, 0))
    
    # Préparer le dessin
    draw = ImageDraw.Draw(labeled_image)
    
    try:
        # Essayer d'utiliser une police par défaut
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
    except:
        # Fallback sur la police par défaut
        font = ImageFont.load_default()
    
    # Ajouter les étiquettes
    qr_size = 150
    for i in range(16):
        row = i // 4
        col = i % 4
        
        x = col * (qr_size + espacement) + qr_size // 2
        y = grid_image.height + 5
        
        # Texte centré
        text = qr_data_list[i][:12]  # Limiter la longueur
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        draw.text((x - text_width // 2, y), text, fill='black', font=font)
    
    return labeled_image

def generer_grille_qr_complete():
    """
    Génère la grille complète de 16 QR codes au format 116 DOCE.
    
    Returns:
        PIL.Image: Image finale de la grille 4x4
    """
    print("🔄 Génération des données pour 16 QR codes...")
    
    # Générer les données pour les 16 QR codes
    qr_data_list = []
    for i in range(16):
        data = generer_donnees_qr(i)
        qr_data_list.append(data)
        print(f"   QR {i+1:02d}: {data}")
    
    print("\n🔄 Création des QR codes individuels...")
    
    # Créer les QR codes individuels
    qr_images = []
    for i, data in enumerate(qr_data_list):
        qr_img = creer_qr_code(data)
        qr_images.append(qr_img)
        print(f"   ✅ QR code {i+1:02d} créé")
    
    print("\n🔄 Assemblage de la grille 4x4...")
    
    # Assembler la grille
    grid = assembler_grille_qr(qr_images)
    
    print("\n🔄 Ajout des étiquettes...")
    
    # Ajouter les étiquettes
    final_image = ajouter_etiquettes(grid, qr_data_list)
    
    return final_image, qr_data_list

def sauvegarder_resultats(image, qr_data_list):
    """
    Sauvegarde l'image et les données dans des fichiers.
    
    Args:
        image (PIL.Image): Image de la grille
        qr_data_list (list): Liste des données des QR codes
    """
    # Créer le dossier de sortie s'il n'existe pas
    output_dir = "qr_codes_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Nom de fichier avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sauvegarder l'image
    image_path = f"{output_dir}/grille_qr_116doce_{timestamp}.png"
    image.save(image_path, "PNG", dpi=(300, 300))
    print(f"📁 Image sauvegardée: {image_path}")
    
    # Sauvegarder les données dans un fichier texte
    data_path = f"{output_dir}/donnees_qr_116doce_{timestamp}.txt"
    with open(data_path, 'w', encoding='utf-8') as f:
        f.write("# Données des QR Codes - Format 116 DOCE\n")
        f.write(f"# Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
        f.write("# Grille 4x4 - 16 QR codes\n\n")
        
        for i, data in enumerate(qr_data_list):
            position = f"Ligne {i//4 + 1}, Colonne {i%4 + 1}"
            f.write(f"QR {i+1:02d} ({position}): {data}\n")
    
    print(f"📄 Données sauvegardées: {data_path}")
    
    return image_path, data_path

def afficher_apercu(image):
    """
    Affiche un aperçu de l'image générée.
    
    Args:
        image (PIL.Image): Image à afficher
    """
    plt.figure(figsize=(12, 12))
    plt.imshow(image)
    plt.title("Grille QR Codes 4x4 - Format 116 DOCE", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    # Ajouter une grille pour mieux voir la structure
    ax = plt.gca()
    
    # Calculer les positions de la grille
    qr_size = 150
    espacement = 10
    
    for i in range(5):  # 5 lignes pour 4 cases (0 à 4)
        y = i * (qr_size + espacement) - 0.5
        ax.axhline(y=y, color='red', linewidth=1, alpha=0.3)
    
    for i in range(5):  # 5 colonnes pour 4 cases (0 à 4)
        x = i * (qr_size + espacement) - 0.5
        ax.axvline(x=x, color='red', linewidth=1, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def main():
    """
    Fonction principale pour générer les QR codes.
    """
    print("🚀 Générateur de QR Codes 2D - Format 116 DOCE")
    print("=" * 50)
    print("📋 Configuration:")
    print("   • Format: 116 DOCE")
    print("   • Nombre de QR codes: 16")
    print("   • Disposition: Carré 4x4")
    print("   • Taille individuelle: 150x150 pixels")
    print("=" * 50)
    
    try:
        # Générer la grille complète
        image, qr_data = generer_grille_qr_complete()
        
        # Sauvegarder les résultats
        print("\n💾 Sauvegarde des résultats...")
        image_path, data_path = sauvegarder_resultats(image, qr_data)
        
        # Afficher un aperçu
        print("\n🖼️  Affichage de l'aperçu...")
        afficher_apercu(image)
        
        print("\n✅ Génération terminée avec succès!")
        print(f"📸 Image finale: {image_path}")
        print(f"📝 Fichier de données: {data_path}")
        
        # Résumé des informations
        print("\n📊 Résumé:")
        print(f"   • Résolution finale: {image.width}x{image.height} pixels")
        print(f"   • Format de sortie: PNG haute qualité (300 DPI)")
        print(f"   • Données encodées: 16 codes uniques au format 116 DOCE")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()
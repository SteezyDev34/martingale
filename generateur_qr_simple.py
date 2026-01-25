#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de QR Codes 2D - Format 116 DOCE (Version Simplifiée)
16 QR codes disposés en carré 4x4

Auteur: Générateur automatisé
Date: 11 novembre 2025
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont
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
    grid_width = 4 * qr_size + 3 * espacement + 40  # Marge supplémentaire
    grid_height = 4 * qr_size + 3 * espacement + 100  # Espace pour les étiquettes
    
    # Créer une nouvelle image blanche
    grid_image = Image.new('RGB', (grid_width, grid_height), 'white')
    draw = ImageDraw.Draw(grid_image)
    
    # Ajouter un titre
    try:
        title_font = ImageFont.load_default()
    except:
        title_font = None
    
    title_text = "QR CODES 116 DOCE - GRILLE 4x4"
    if title_font:
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        draw.text(((grid_width - text_width) // 2, 10), title_text, fill='black', font=title_font)
    
    # Coller chaque QR code à sa position
    y_offset = 40  # Décalage pour le titre
    for i in range(16):
        row = i // 4
        col = i % 4
        
        x = col * (qr_size + espacement) + 20
        y = row * (qr_size + espacement) + y_offset
        
        grid_image.paste(qr_images[i], (x, y))
        
        # Ajouter le numéro du QR code sous chaque image
        label_text = f"QR {i+1:02d}"
        if title_font:
            bbox = draw.textbbox((0, 0), label_text, font=title_font)
            text_width = bbox[2] - bbox[0]
            label_x = x + (qr_size - text_width) // 2
            label_y = y + qr_size + 5
            draw.text((label_x, label_y), label_text, fill='black', font=title_font)
    
    return grid_image

def generer_grille_qr_complete():
    """
    Génère la grille complète de 16 QR codes au format 116 DOCE.
    
    Returns:
        tuple: (Image PIL, liste des données)
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
    
    return grid, qr_data_list

def sauvegarder_resultats(image, qr_data_list):
    """
    Sauvegarde l'image et les données dans des fichiers.
    
    Args:
        image (PIL.Image): Image de la grille
        qr_data_list (list): Liste des données des QR codes
    
    Returns:
        tuple: (chemin image, chemin données)
    """
    # Créer le dossier de sortie s'il n'existe pas
    output_dir = "qr_codes_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Nom de fichier avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sauvegarder l'image en haute qualité
    image_path = f"{output_dir}/grille_qr_116doce_{timestamp}.png"
    image.save(image_path, "PNG", dpi=(300, 300), optimize=True)
    print(f"📁 Image sauvegardée: {image_path}")
    
    # Sauvegarder aussi en format JPEG pour une taille plus petite
    jpeg_path = f"{output_dir}/grille_qr_116doce_{timestamp}.jpg"
    rgb_image = image.convert('RGB')
    rgb_image.save(jpeg_path, "JPEG", quality=95, optimize=True)
    print(f"📁 Version JPEG sauvegardée: {jpeg_path}")
    
    # Sauvegarder les données dans un fichier texte
    data_path = f"{output_dir}/donnees_qr_116doce_{timestamp}.txt"
    with open(data_path, 'w', encoding='utf-8') as f:
        f.write("# Données des QR Codes - Format 116 DOCE\n")
        f.write(f"# Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
        f.write("# Grille 4x4 - 16 QR codes\n")
        f.write("# Format: 116DOCE + Index + Timestamp + Code unique\n\n")
        
        f.write("POSITION\t\tDATA\n")
        f.write("-" * 60 + "\n")
        
        for i, data in enumerate(qr_data_list):
            row = i // 4 + 1
            col = i % 4 + 1
            position = f"L{row}C{col}"
            f.write(f"QR {i+1:02d} ({position})\t{data}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("LÉGENDE:\n")
        f.write("L = Ligne (1-4)\n")
        f.write("C = Colonne (1-4)\n")
        f.write("Format des données: 116DOCE[Index]-[Timestamp]-[Code]\n")
    
    print(f"📄 Données sauvegardées: {data_path}")
    
    return image_path, data_path

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
    print("   • Espacement: 10 pixels")
    print("=" * 50)
    
    try:
        # Générer la grille complète
        image, qr_data = generer_grille_qr_complete()
        
        # Sauvegarder les résultats
        print("\n💾 Sauvegarde des résultats...")
        image_path, data_path = sauvegarder_resultats(image, qr_data)
        
        print("\n✅ Génération terminée avec succès!")
        print(f"📸 Image PNG: {image_path}")
        print(f"📸 Image JPEG: {image_path.replace('.png', '.jpg')}")
        print(f"📝 Fichier de données: {data_path}")
        
        # Résumé des informations
        print("\n📊 Résumé:")
        print(f"   • Résolution finale: {image.width}x{image.height} pixels")
        print(f"   • Format de sortie: PNG et JPEG haute qualité")
        print(f"   • Données encodées: 16 codes uniques au format 116 DOCE")
        print(f"   • Structure: Grille 4x4 avec étiquettes")
        
        # Afficher quelques exemples de données
        print("\n📋 Exemples de données générées:")
        for i in range(min(4, len(qr_data))):
            print(f"   • QR {i+1:02d}: {qr_data[i]}")
        if len(qr_data) > 4:
            print(f"   • ... et {len(qr_data)-4} autres")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Script terminé avec succès!")
        print("💡 Vous pouvez maintenant utiliser les fichiers générés.")
    else:
        print("\n⚠️  Le script a rencontré des erreurs.")
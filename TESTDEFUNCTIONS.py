print('START')
import os

#Chargement de Chrome driver
from ChromeDriver.SetDriver1 import driver

#Chargement des variables globales
import config

# Récupérer le nom du script
# Nom du fichier
file_name = os.path.basename(__file__)  # ou directement '40-1.py' pour l'exemple
# Séparer le nom du fichier et l'extension
name_part = os.path.splitext(file_name)[0]
# Séparer les parties du nom
parts = name_part.split('-')


#Chargement des fonctions
from Functions import Functions_15a
from Functions.GetJsonData import DispatchPerte

from Functions.AfficherParis import AfficherParis

AfficherParis(driver)
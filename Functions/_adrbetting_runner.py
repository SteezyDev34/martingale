# -*- coding: utf-8 -*-
"""
Script autonome lancé en subprocess par AdrBettingScraper.scrape_adrbetting_coupons().
Tourne dans son propre processus Python avec son propre event loop — aucun conflit
avec l'event loop Telethon du processus parent.
Imprime sur stdout un JSON array des chemins d'images capturées.
"""
import asyncio
import json
import os
import sys

# Remonter à la racine du projet
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from Functions.AdrBettingScraper import AdrBettingScraper


async def main():
    scraper = AdrBettingScraper()
    coupons = await scraper.scrape_coupons()
    # Dernière ligne stdout = JSON parseable par le processus parent
    # Format : [["filepath", "tipster_name"], ...]
    print(json.dumps([list(item) for item in coupons]))


if __name__ == "__main__":
    asyncio.run(main())

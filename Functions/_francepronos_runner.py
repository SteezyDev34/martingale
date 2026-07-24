# -*- coding: utf-8 -*-
"""
Script autonome lancé en subprocess par FrancePronosScraper.scrape_francepronos().
Imprime sur stdout un JSON array des dicts de pronostics extraits.
"""
import asyncio
import json
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from Functions.FrancePronosScraper import FrancePronosScraper


async def main():
    scraper = FrancePronosScraper()
    pronos = await scraper.scrape_pronos()
    print(json.dumps(pronos))


if __name__ == "__main__":
    asyncio.run(main())

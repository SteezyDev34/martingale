# -*- coding: utf-8 -*-
"""
Utilitaires de simulation de comportement humain pour Playwright.
Mouvements de souris aléatoires, frappe irrégulière, scroll naturel.
"""
import asyncio
import random
import math


async def human_move(page, x: int, y: int):
    """Déplace la souris vers (x, y) en suivant une courbe de Bézier."""
    current = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
    cx, cy = current.get("x", 0), current.get("y", 0)

    steps = random.randint(8, 18)
    # Point de contrôle pour la courbe
    cpx = (cx + x) / 2 + random.randint(-80, 80)
    cpy = (cy + y) / 2 + random.randint(-80, 80)

    for i in range(1, steps + 1):
        t = i / steps
        # Courbe de Bézier quadratique
        bx = (1 - t) ** 2 * cx + 2 * (1 - t) * t * cpx + t ** 2 * x
        by = (1 - t) ** 2 * cy + 2 * (1 - t) * t * cpy + t ** 2 * y
        # Léger bruit
        bx += random.uniform(-2, 2)
        by += random.uniform(-2, 2)
        await page.mouse.move(bx, by)
        await asyncio.sleep(random.uniform(0.008, 0.025))

    await page.mouse.move(x, y)


async def human_click(page, x: int, y: int):
    """Déplace la souris puis clique avec un délai humain."""
    await human_move(page, x, y)
    await asyncio.sleep(random.uniform(0.05, 0.18))
    await page.mouse.down()
    await asyncio.sleep(random.uniform(0.04, 0.12))
    await page.mouse.up()
    await asyncio.sleep(random.uniform(0.08, 0.25))


async def human_click_selector(page, selector: str):
    """Clique sur un sélecteur CSS avec comportement humain."""
    el = await page.wait_for_selector(selector, timeout=10000)
    box = await el.bounding_box()
    if box:
        x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
        y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
        await human_click(page, x, y)
    else:
        await el.click()


async def human_type(page, selector: str, text: str, clear_first: bool = True):
    """
    Tape du texte caractère par caractère avec des délais irréguliers
    simulant une frappe humaine (WPM ~60-90).
    """
    el = await page.wait_for_selector(selector, timeout=10000)
    box = await el.bounding_box()
    if box:
        x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
        y = box["y"] + box["height"] * random.uniform(0.2, 0.8)
        await human_click(page, x, y)
    else:
        await el.click()

    if clear_first:
        await page.keyboard.press("Control+a")
        await asyncio.sleep(random.uniform(0.05, 0.1))
        await page.keyboard.press("Delete")
        await asyncio.sleep(random.uniform(0.05, 0.15))

    for char in text:
        await page.keyboard.type(char)
        # Délai de base 60-90 WPM + variations naturelles
        delay = random.gauss(0.09, 0.04)
        # Pauses occasionnelles (hésitation)
        if random.random() < 0.05:
            delay += random.uniform(0.2, 0.6)
        await asyncio.sleep(max(0.03, delay))


async def human_scroll(page, direction: str = "down", amount: int = None):
    """Scroll naturel avec accélération/décélération."""
    if amount is None:
        amount = random.randint(200, 600)

    steps = random.randint(4, 10)
    for i in range(steps):
        # Accélération en début, décélération en fin
        t = i / steps
        factor = math.sin(t * math.pi)  # courbe en cloche
        chunk = int((amount / steps) * (0.5 + factor))
        delta = chunk if direction == "down" else -chunk
        await page.mouse.wheel(0, delta)
        await asyncio.sleep(random.uniform(0.05, 0.15))


async def human_wait(min_ms: int = 500, max_ms: int = 1500):
    """Pause aléatoire simulant un temps de lecture/réflexion."""
    await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


async def dismiss_modal(page, selectors: list = None):
    """Ferme une popup/modal si présente."""
    default = [
        "button.close", "[aria-label='Close']", "[aria-label='Fermer']",
        ".modal-close", ".close-btn", "button[data-dismiss='modal']",
        ".overlay-close", ".popup-close"
    ]
    for sel in (selectors or default):
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await human_click_selector(page, sel)
                await human_wait(300, 700)
                return True
        except Exception:
            pass
    return False

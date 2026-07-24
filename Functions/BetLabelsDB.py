# -*- coding: utf-8 -*-
"""
Base de données SQLite pour :
1. Mapping labels : label_standard ↔ label_bookmaker par sport et bookmaker
2. Défis actifs : liste des défis/boosts en cours par bookmaker
"""
import os
import sqlite3
from typing import Optional, List, Dict

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "bet_labels.db"
)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée les tables si elles n'existent pas."""
    conn = get_conn()
    c = conn.cursor()

    # Mapping labels bookmaker
    c.execute("""
        CREATE TABLE IF NOT EXISTS bet_labels (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            bookmaker       TEXT NOT NULL,
            sport_id        TEXT NOT NULL,
            label_standard  TEXT NOT NULL,
            label_bookmaker TEXT NOT NULL,
            regex_pattern   TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bookmaker, sport_id, label_standard)
        )
    """)

    # Défis actifs par bookmaker
    c.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bookmaker   TEXT NOT NULL,
            title       TEXT NOT NULL,
            description TEXT,
            condition   TEXT,
            url         TEXT,
            expires_at  TEXT,
            scraped_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# Labels                                                               #
# ------------------------------------------------------------------ #

def get_label(bookmaker: str, sport_id: str, label_standard: str) -> Optional[str]:
    """Retourne le libellé bookmaker pour un label standard donné."""
    conn = get_conn()
    row = conn.execute(
        "SELECT label_bookmaker FROM bet_labels WHERE bookmaker=? AND sport_id=? AND label_standard=?",
        (bookmaker, sport_id, label_standard)
    ).fetchone()
    conn.close()
    return row["label_bookmaker"] if row else None


def upsert_label(bookmaker: str, sport_id: str, label_standard: str, label_bookmaker: str, regex_pattern: str = None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO bet_labels (bookmaker, sport_id, label_standard, label_bookmaker, regex_pattern)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(bookmaker, sport_id, label_standard) DO UPDATE SET
            label_bookmaker=excluded.label_bookmaker,
            regex_pattern=excluded.regex_pattern
    """, (bookmaker, sport_id, label_standard, label_bookmaker, regex_pattern))
    conn.commit()
    conn.close()


def get_all_labels(bookmaker: str, sport_id: str = None) -> List[Dict]:
    conn = get_conn()
    if sport_id:
        rows = conn.execute(
            "SELECT * FROM bet_labels WHERE bookmaker=? AND sport_id=?", (bookmaker, sport_id)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM bet_labels WHERE bookmaker=?", (bookmaker,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------ #
# Défis                                                                #
# ------------------------------------------------------------------ #

def clear_challenges(bookmaker: str):
    """Supprime les défis d'un bookmaker avant de les re-scraper."""
    conn = get_conn()
    conn.execute("DELETE FROM challenges WHERE bookmaker=?", (bookmaker,))
    conn.commit()
    conn.close()


def insert_challenge(bookmaker: str, title: str, description: str = None,
                     condition: str = None, url: str = None, expires_at: str = None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO challenges (bookmaker, title, description, condition, url, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (bookmaker, title, description, condition, url, expires_at))
    conn.commit()
    conn.close()


def get_active_challenges(bookmaker: str = None) -> List[Dict]:
    """Retourne les défis actifs, optionnellement filtrés par bookmaker."""
    conn = get_conn()
    if bookmaker:
        rows = conn.execute(
            "SELECT * FROM challenges WHERE bookmaker=? ORDER BY scraped_at DESC", (bookmaker,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM challenges ORDER BY bookmaker, scraped_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_challenges_for_prompt() -> str:
    """
    Retourne un résumé textuel de tous les défis actifs pour injection dans le prompt GPT.
    Format : 'BOOKMAKER | TITRE | CONDITION'
    """
    challenges = get_active_challenges()
    if not challenges:
        return "Aucun défi actif."
    lines = []
    for c in challenges:
        lines.append(f"{c['bookmaker']} | {c['title']} | {c.get('condition') or c.get('description') or ''}")
    return "\n".join(lines)


# Initialiser la DB au chargement du module
init_db()

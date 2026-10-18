# -*- coding: utf-8 -*-
"""
Outil en ligne de commande pour le skill de revue des paris en erreur.
Lit les traces de Functions/Logs/BetTrace.py (Logs/bet_traces/<date>/<bet_id>/)
et expose 3 sous-commandes pensées pour être appelées par Claude (peu de
tokens, pas besoin de parser le JSONL à la main) :

  list [--all] [--date YYYY-MM-DD]
      Liste les paris dont la DERNIÈRE tentative connue est un échec,
      un par ligne (TSV), en excluant par défaut ceux déjà marqués dans
      l'état de revue (--all pour tout revoir, y compris déjà traités).

  show <date> <bet_id>
      Détail complet d'un pari : contexte (dernière tentative), historique
      des tentatives (une ligne par cycle start->résultat), candidates et
      screenshot de la dernière erreur si présents.

  mark <date> <bet_id> --status resolved|skipped --category <cat> [--note TEXT]
      Enregistre la décision prise ensemble dans l'état de revue, pour ne
      plus re-proposer ce pari la prochaine fois (sauf --all).

  label --bookmaker <nom> --sport <sport_id> --standard "<sélection pivot>" \
        --target "<texte réel bookmaker>" [--pattern "<regex optionnelle>"]
      Enregistre une correspondance de libellé dans Functions/BetLabelsDB.py
      (table bet_labels, déjà lue au placement par Stake/Lollybet/Betclic/
      Winamax via get_label() -- PAS 1xBet, qui garde le pivot comme source
      de vérité). À utiliser pour un `label_mismatch` confirmé sur un de ces
      bookmakers : la sélection pivot (taxonomie 1xBet, choisie par l'IA
      d'extraction AVANT de savoir quel bookmaker sera retenu) reste
      inchangée, seule la traduction pour CE bookmaker est ajoutée/mise à
      jour. Un `label_mismatch` sur 1xBet lui-même se corrige autrement
      (règle de prompt dans getTextFromImageGPT.py, cf. SKILL.md).

  requeue <date> <bet_id>
      Remet un pari Telegram dans la file "non traités" de l'API
      telegram_bets (processed=0) pour qu'il soit retenté au prochain
      process_api_bets() -- utile car le message Telegram déclencheur est
      déjà passé et ne reviendra pas. À utiliser seulement après avoir
      corrigé la vraie cause (label/prompt), jamais pour un match_ended.

Un pari est un "trace_dir" = Logs/bet_traces/<date>/<bet_id>/ ; son
trace.jsonl peut contenir PLUSIEURS cycles start/résultat (le même bet_id est
retenté plusieurs fois par ProcessTelegramBets tant qu'il échoue) — seul le
DERNIER "resultat" fait foi pour savoir si ce pari est, au final, en échec.
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

TRACE_ROOT = os.path.join(config.projectPath, "Logs", "bet_traces")
STATE_FILE = os.path.join(TRACE_ROOT, "_review_state.json")


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state):
    os.makedirs(TRACE_ROOT, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _read_jsonl(path):
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return entries


def _read_context(trace_dir):
    path = os.path.join(trace_dir, "context.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _iter_trace_dirs():
    if not os.path.isdir(TRACE_ROOT):
        return
    for date_str in sorted(os.listdir(TRACE_ROOT)):
        date_dir = os.path.join(TRACE_ROOT, date_str)
        if not os.path.isdir(date_dir):
            continue
        for bet_id in sorted(os.listdir(date_dir), key=lambda x: (len(x), x)):
            bet_dir = os.path.join(date_dir, bet_id)
            if os.path.isdir(bet_dir):
                yield date_str, bet_id, bet_dir


def _last_result(entries):
    """Dernier step 'resultat', ou à défaut dernier step 'failure' (cycle
    interrompu avant d'écrire le résultat final)."""
    last_resultat = None
    last_failure = None
    for e in entries:
        if e.get("label") == "resultat":
            last_resultat = e
        elif e.get("label") == "failure":
            last_failure = e
    return last_resultat, last_failure


def _attempt_count(entries):
    return sum(1 for e in entries if e.get("label") == "start")


def _match_summary(context):
    matches = context.get("matches") or []
    if not matches:
        return {}
    m = matches[-1]
    return {
        "match": f"{m.get('equipe_1', '?')} vs {m.get('equipe_2', '?')}",
        "selection": m.get("selection", ""),
        "categorie": m.get("categorie", ""),
        "type_de_pari": m.get("type_de_pari", ""),
        "intitule": m.get("intitule", ""),
        "sport": m.get("sport", ""),
        "date": m.get("date", ""),
        "tipster": context.get("tipster", ""),
        "odds": m.get("odds"),
    }


def cmd_list(args):
    state = _load_state()
    for date_str, bet_id, bet_dir in _iter_trace_dirs():
        if args.date and date_str != args.date:
            continue
        key = f"{date_str}/{bet_id}"
        if not args.all and key in state:
            continue

        entries = _read_jsonl(os.path.join(bet_dir, "trace.jsonl"))
        if not entries:
            continue
        last_resultat, last_failure = _last_result(entries)

        if last_resultat is not None:
            if last_resultat.get("detail", {}).get("success"):
                continue  # dernière tentative réussie -> rien à revoir
            detail = last_resultat.get("detail", {})
            bookmaker = detail.get("bookmaker")
            error = detail.get("error")
        elif last_failure is not None:
            detail = last_failure.get("detail", {})
            bookmaker = None
            error = detail.get("error")
        else:
            continue  # ni resultat ni failure -> cycle en cours, rien à montrer

        context = _read_context(bet_dir)
        info = _match_summary(context)
        candidates = detail.get("candidates") or []
        reviewed = key in state
        print("\t".join([
            date_str, bet_id,
            info.get("tipster", ""), info.get("match", ""), info.get("selection", ""),
            bookmaker or "-", error or "(vide/legacy)",
            f"{_attempt_count(entries)} tentative(s)",
            f"candidates={len(candidates)}" if candidates else "candidates=0",
            "DEJA_REVU" if reviewed else "",
        ]))


def cmd_show(args):
    bet_dir = os.path.join(TRACE_ROOT, args.date, args.bet_id)
    if not os.path.isdir(bet_dir):
        print(f"Introuvable : {bet_dir}", file=sys.stderr)
        sys.exit(1)

    entries = _read_jsonl(os.path.join(bet_dir, "trace.jsonl"))
    context = _read_context(bet_dir)
    info = _match_summary(context)

    print(f"=== {args.date}/{args.bet_id} ===")
    print(f"Tipster      : {info.get('tipster')}")
    print(f"Match        : {info.get('match')}  ({info.get('date')})")
    print(f"Marché       : {info.get('categorie')} / {info.get('type_de_pari')}")
    print(f"Sélection    : {info.get('selection')}")
    print(f"Intitulé brut: {info.get('intitule')}")
    print(f"Cote ref     : {info.get('odds')}")
    print()
    print(f"Historique ({_attempt_count(entries)} tentative(s)) :")
    for e in entries:
        label = e.get("label")
        if label == "start":
            m = (e.get("detail", {}).get("matches") or [{}])[-1]
            print(f"  [{e['ts']}] START   selection={m.get('selection')!r}")
        elif label == "mise_calculee":
            print(f"  [{e['ts']}] MISE    {e.get('detail')}")
        elif label == "placement_tente":
            print(f"  [{e['ts']}] TENTE   {e.get('detail')}")
        elif label == "failure":
            d = e.get("detail", {})
            print(f"  [{e['ts']}] FAILURE error={d.get('error')!r} screenshot={d.get('screenshot')}")
            if d.get("candidates"):
                print(f"              candidates vus sur la page ({len(d['candidates'])}):")
                for c in d["candidates"]:
                    print(f"                - {c}")
        elif label == "resultat":
            d = e.get("detail", {})
            tag = "OK" if d.get("success") else "ECHEC"
            print(f"  [{e['ts']}] RESULTAT[{tag}] bookmaker={d.get('bookmaker')} error={d.get('error')}")
            if d.get("candidates"):
                print(f"              candidates ({len(d['candidates'])}):")
                for c in d["candidates"]:
                    print(f"                - {c}")

    state = _load_state()
    key = f"{args.date}/{args.bet_id}"
    if key in state:
        print()
        print(f"Déjà revu : {state[key]}")


def cmd_mark(args):
    state = _load_state()
    key = f"{args.date}/{args.bet_id}"
    state[key] = {
        "status": args.status,
        "category": args.category,
        "note": args.note or "",
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save_state(state)
    print(f"OK : {key} -> {state[key]}")


def cmd_requeue(args):
    """
    Remet un pari Telegram (France Pronos, AdrBetting, Tempête, Tennistiqueur,
    Auxo1XBOT...) dans la file "non traités" de l'API telegram_bets, pour que
    ProcessTelegramBets.py le retente au prochain passage -- SANS attendre un
    nouveau message Telegram (qui ne reviendra pas, le message déclencheur est
    déjà passé). N'a de sens qu'après avoir corrigé la vraie cause (label ajouté
    via `label`, règle de prompt ajoutée dans getTextFromImageGPT.py...) --
    jamais pour un `match_ended` (le match est fini, retenter ne sert à rien).
    """
    bet_dir = os.path.join(TRACE_ROOT, args.date, args.bet_id)
    context = _read_context(bet_dir)
    info = _match_summary(context)
    if info:
        print(f"Pari {args.bet_id} ({args.date}) : {info.get('match')} -- {info.get('selection')}")

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from Functions.TelegramBetsAPI import telegram_bets_api

    ok = telegram_bets_api.mark_bet_as_processed(int(args.bet_id), processed=0)
    if ok:
        print(f"OK : pari {args.bet_id} remis en file (processed=0) -- "
              f"sera retenté au prochain process_api_bets()")
    else:
        print(f"ÉCHEC : impossible de remettre le pari {args.bet_id} en file (voir logs)", file=sys.stderr)
        sys.exit(1)


_LABEL_BOOKMAKERS = ["Stake", "Lollybet", "Betclic", "Winamax"]


def cmd_label(args):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from Functions.BetLabelsDB import upsert_label, get_label

    previous = get_label(args.bookmaker, args.sport, args.standard)
    upsert_label(args.bookmaker, args.sport, args.standard, args.target, args.pattern)
    if previous:
        print(f"OK : {args.bookmaker}/sport={args.sport} {args.standard!r} -> {args.target!r} "
              f"(remplace {previous!r})")
    else:
        print(f"OK : {args.bookmaker}/sport={args.sport} {args.standard!r} -> {args.target!r} (nouvelle entrée)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="Liste les paris en échec non encore revus")
    p_list.add_argument("--all", action="store_true", help="Inclure ceux déjà revus")
    p_list.add_argument("--date", help="Filtrer sur une date YYYY-MM-DD")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Détail complet d'un pari")
    p_show.add_argument("date")
    p_show.add_argument("bet_id")
    p_show.set_defaults(func=cmd_show)

    p_mark = sub.add_parser("mark", help="Marque un pari comme revu")
    p_mark.add_argument("date")
    p_mark.add_argument("bet_id")
    p_mark.add_argument("--status", required=True, choices=["resolved", "skipped"])
    p_mark.add_argument("--category", required=True,
                         choices=["match_ended", "label_mismatch", "technical", "unknown"])
    p_mark.add_argument("--note", default="")
    p_mark.set_defaults(func=cmd_mark)

    p_label = sub.add_parser("label", help="Ajoute/MAJ une correspondance de libellé (bet_labels.db)")
    p_label.add_argument("--bookmaker", required=True, choices=_LABEL_BOOKMAKERS,
                          help="1xBet exclu : il garde le pivot comme source de vérité, cf. SKILL.md")
    p_label.add_argument("--sport", required=True, help="sport_id (ex: 1=football, 2=tennis)")
    p_label.add_argument("--standard", required=True, help="Sélection pivot (telle qu'extraite par l'IA)")
    p_label.add_argument("--target", required=True, help="Texte réel vu chez ce bookmaker")
    p_label.add_argument("--pattern", default=None, help="Regex optionnelle (non utilisée par get_label pour l'instant)")
    p_label.set_defaults(func=cmd_label)

    p_requeue = sub.add_parser("requeue", help="Remet un pari Telegram en file pour retentative")
    p_requeue.add_argument("date")
    p_requeue.add_argument("bet_id")
    p_requeue.set_defaults(func=cmd_requeue)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

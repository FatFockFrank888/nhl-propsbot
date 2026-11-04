"""CSV files for the Google Sheet, in the same format as the NBA/football bots' site/csv/.

The sheet imports them with IMPORTDATA() from the GitHub Pages site, so the columns and
labels mirror the existing bots exactly (comma-separated, dot decimals, Swedish headers).
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bot_settings import BotSettings
from .ledger import open_ledgers

BET_COLUMNS = ["Bokförd", "Sport", "Typ", "Avspark", "Match", "Spelare", "Marknad", "Sida", "Linje", "Bolag",
               "Odds", "Stängning", "CLV (%)", "Sannolikhet", "Edge", "Insats (u)", "Status", "Utfall",
               "Resultat (u)"]
SUMMARY_COLUMNS = ["Sport", "Typ", "Spel", "Avgjorda", "Vunna", "Träff %", "Insats (u)", "Resultat (u)",
                   "ROI %", "Snitt-CLV %", "Öppna", "Uppdaterad (UTC)"]

TYPE_LABEL = {"live": "Live", "bokforing": "Bokföring", "skugga": "Skugga", "modelltest": "Modelltest"}
SIDE_LABEL = {"over": "över", "under": "under"}
OUTCOME_LABEL = {"won": "vunnen", "lost": "förlorad", "push": "push", "void": "struken", "open": ""}


def _time(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso


def _num(x: Any, digits: int) -> str:
    return "" if x is None else f"{x:.{digits}f}"


def bet_row(b: dict[str, Any]) -> list[str]:
    settled = b["status"] != "open"
    return [
        _time(b.get("created")), "NHL", TYPE_LABEL.get(b["ledger"], b["ledger"]), _time(b.get("start")),
        b.get("game", ""), b["player"], "Skott på mål", SIDE_LABEL.get(b["side"], b["side"]), f"{b['line']:g}",
        b["book"], _num(b.get("odds"), 2), _num(b.get("close_odds"), 2),
        _num(None if b.get("clv") is None else b["clv"] * 100, 1), _num(b.get("p_fair"), 4), _num(b.get("edge"), 4),
        str(b["units"]), "avgjord" if settled else "öppen", OUTCOME_LABEL.get(b["status"], b["status"]),
        _num(b.get("profit_units"), 2) if settled else "",
    ]


def summary_row(name: str, bets: list[dict[str, Any]], now: str) -> list[str]:
    done = [b for b in bets if b["status"] in ("won", "lost", "push")]
    won = sum(b["status"] == "won" for b in done)
    decisive = sum(b["status"] in ("won", "lost") for b in done)
    staked = sum(b["units"] for b in done)
    profit = sum(b["profit_units"] or 0 for b in done)
    clvs = [b["clv"] for b in bets if b.get("clv") is not None]
    return [
        "NHL", TYPE_LABEL.get(name, name), str(len(bets)), str(len(done)), str(won),
        _num(100 * won / decisive, 1) if decisive else "", str(staked), _num(profit, 2),
        _num(100 * profit / staked, 1) if staked else "", _num(100 * sum(clvs) / len(clvs), 1) if clvs else "",
        str(sum(b["status"] == "open" for b in bets)), now,
    ]


def _write(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def write_sheet_csvs(s: BotSettings, out: Path) -> list[Path]:
    ledgers = open_ledgers(s)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    by_time = lambda b: b.get("created") or ""  # noqa: E731
    live = sorted(ledgers["live"].bets, key=by_time, reverse=True)
    everything = sorted((b for l in ledgers.values() for b in l.bets), key=by_time, reverse=True)
    paths = [out / "live.csv", out / "alla_spel.csv", out / "sammanfattning.csv"]
    _write(paths[0], BET_COLUMNS, [bet_row(b) for b in live])
    _write(paths[1], BET_COLUMNS, [bet_row(b) for b in everything])
    _write(paths[2], SUMMARY_COLUMNS, [summary_row(n, l.bets, now) for n, l in ledgers.items()])
    return paths

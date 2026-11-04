"""Phone notifications via ntfy (free app, no login). Subscribe to the topic in settings.json."""

from __future__ import annotations

import json
import logging
import urllib.request
from datetime import datetime

log = logging.getLogger(__name__)

NTFY = "https://ntfy.sh"


def send(topic: str, title: str, message: str, priority: int = 4, tags: str = "ice_hockey") -> bool:
    if not topic:
        return False
    body = json.dumps(
        {"topic": topic, "title": title, "message": message, "priority": priority, "tags": tags.split(",")},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(NTFY, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15):
            return True
    except Exception as exc:  # noqa: BLE001 - a failed notification must never stop scanning
        log.warning("Could not send notification: %s", exc)
        return False


def format_live_bet(bet: dict, currency: str) -> tuple[str, str]:
    title = f"NHL LIVE: {bet['player']} {bet['side'].capitalize()} {bet['line']:g} SOG @ {bet['odds']:.2f}"
    start = ""
    if bet.get("start"):
        start = " | " + datetime.fromisoformat(bet["start"]).astimezone().strftime("%a %H:%M")
    lines = [
        f"{bet['game']}{start}",
        f"Bet at {bet['book'].upper()} {bet['odds']:.2f} - play down to {bet['play_down_to']:.2f}"
        if bet.get("play_down_to") else f"Bet at {bet['book'].upper()} {bet['odds']:.2f}",
        f"Stake {bet['units']}u = {bet['stake']:.0f} {currency}",
        f"Edge {bet['edge']:.1%} | model {bet['model_edge']:.1%} | proj {bet['proj_sog']:.2f} SOG",
        f"Fair {bet['p_fair']:.1%} | refs: {', '.join(bet['groups'])}",
    ]
    others = {b: o for b, o in (bet.get("alt_prices") or {}).items() if b != bet["book"]}
    if others:
        lines.append("Also: " + ", ".join(f"{b} {o:.2f}" for b, o in others.items()))
    if bet.get("tags"):
        lines.append(" | ".join(bet["tags"]))
    return title, "\n".join(lines)


def format_recap(day: str, live, ledgers: dict, history, s) -> tuple[str, str]:
    from .validate import bet_validation

    yday = [b for b in live.bets if b["us_date"] == day and b["status"] in ("won", "lost", "push", "void")]
    w = sum(b["status"] == "won" for b in yday)
    l = sum(b["status"] == "lost" for b in yday)
    p = sum(b["status"] == "push" for b in yday)
    pnl = sum(b["profit_units"] or 0 for b in yday)
    v = bet_validation(live.bets)
    clv = v["clv"]
    lines = [f"{day}: {w}-{l}-{p}, {pnl:+.1f}u" if yday else f"{day}: no live bets settled"]
    if v["settled"]:
        roi = v["roi_weighted"]
        lines.append(f"Total: {v['settled']} settled, {v['profit_units']:+.1f}u, ROI {roi:+.1%}")
    if clv["n"]:
        t = f", t={clv['t']:.1f}" if clv["t"] is not None else ""
        lines.append(f"Avg CLV {clv['mean']:+.1%} over {clv['n']} bets{t}")
    counts = history.leg_counts()
    graded = counts.get("won", 0) + counts.get("lost", 0)
    lines.append(f"Lines graded: {graded} | review at {v['settled']}/150 live bets")
    return "NHL bot daily recap", "\n".join(lines)

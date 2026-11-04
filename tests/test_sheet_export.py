import csv
from dataclasses import replace

from propsbot.bot_settings import BotSettings
from propsbot.ledger import LEDGERS, Ledger
from propsbot.sheet_export import write_sheet_csvs

# Exact headers of the NBA/football bots' published CSVs (the Google Sheet relies on them).
LIVE_HEADER = "Bokförd,Sport,Typ,Avspark,Match,Spelare,Marknad,Sida,Linje,Bolag,Odds,Stängning,CLV (%),Sannolikhet,Edge,Insats (u),Status,Utfall,Resultat (u)"
SUMMARY_HEADER = "Sport,Typ,Spel,Avgjorda,Vunna,Träff %,Insats (u),Resultat (u),ROI %,Snitt-CLV %,Öppna,Uppdaterad (UTC)"


def test_sheet_csvs_match_other_bots(tmp_path):
    s = replace(BotSettings(), data_dir=str(tmp_path / "data"))
    led = Ledger("live", s.data_path / LEDGERS["live"])
    base = {"game_id": 1, "game": "OTT@BUF", "start": "2026-11-05T00:30:00+00:00", "us_date": "2026-11-04",
            "player_id": 1, "line": 2.5, "side": "over", "book": "unibet", "odds": 2.1, "units": 3,
            "p_fair": 0.52, "edge": 0.092, "close_odds": 1.95, "clv": 0.04, "ledger": "live"}
    led.add({**base, "id": "a", "created": "2026-11-04T18:00:00+00:00", "player": "Tage Thompson",
             "status": "won", "profit_units": 3.3})
    led.add({**base, "id": "b", "created": "2026-11-04T19:00:00+00:00", "player": "Tim Stützle", "side": "under",
             "status": "open", "profit_units": None, "clv": None})
    led.save()

    live, alla, summary = write_sheet_csvs(s, tmp_path / "csv")
    lines = live.read_text(encoding="utf-8").splitlines()
    assert lines[0] == LIVE_HEADER
    rows = list(csv.reader(lines[1:]))
    assert rows[0][5] == "Tim Stützle" and rows[0][7] == "under" and rows[0][16] == "öppen"  # newest first
    assert rows[1][:3] == ["2026-11-04 18:00", "NHL", "Live"] and rows[1][17] == "vunnen" and rows[1][18] == "3.30"
    assert rows[1][12] == "4.0"  # CLV in percent
    s_lines = summary.read_text(encoding="utf-8").splitlines()
    assert s_lines[0] == SUMMARY_HEADER
    live_summary = next(r for r in csv.reader(s_lines[1:]) if r[1] == "Live")
    assert live_summary[2:5] == ["2", "1", "1"] and live_summary[8] == "110.0"
    assert alla.read_text(encoding="utf-8").splitlines()[0] == LIVE_HEADER

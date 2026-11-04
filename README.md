# NHL Shots-on-Goal Props Bot

Projects shots on goal (SOG) for every skater on an NHL slate, prices over/under lines,
compares them with odds at **Unibet, ATG, Svenska Spel, Expekt and BetMGM SE**, and lists +EV bets with
fractional-Kelly stakes.

## Edge bot (recommended): `start.bat` / `python -m propsbot watch`

This follows the NBA bot's design. Each scan (every 8 min, every 55 min between 04 and 06 UTC):

1. **Settle.** Finished bets are settled from the NHL boxscore (`sog`). A player who didn't play is void.
2. **Playable prices.** Kambi's open feed is read for every offering in `kambi_offerings`; this is free. Bets are only placed at `playable_books`. Paf and LeoVegas are read but never bet.
3. **References** (independent groups; the Kambi family is never its own reference):
   - **Bovada** is read on every scan: free, no key, independent of Kambi.
     - Two-sided over/under lines are de-vigged.
     - Before those post, the one-sided "N+ shots" milestone ladder is fitted with a negative binomial, solving for the expected shots and the margin together. That gives a fair two-sided probability at any line a day ahead.
     - Bovada also supplies the continuous closing line used for CLV.
   - **US books** via The Odds API (DraftKings, FanDuel, BetMGM US, Caesars, Fanatics, ESPN Bet, Hard Rock, BetOnline). Each game is fetched once, 40–240 min before puck drop, for 1 credit.
     - A credit is spent only when a pre-check against Bovada and the model already shows a candidate edge, and only within the daily budget: (credits left − reserve) / days left × `odds_api_share`.
     - The key is shared with your other bots, so set `odds_api_share` to match your NBA/football split.
   - **Pinnacle** is the sharp reference, weighted ×2, with negative binomial interpolation to neighbouring lines. It is **off by default**: set `use_pinnacle: true` and your own `pinnacle_api_key`.
   - **Kalshi** is not used. It has no NHL shots-on-goal markets, only goals, points, assists and saves.
4. **Fair probability.** Each reference group is power-method de-vigged; one-sided prices get an assumed 8% margin. The groups are combined in log-odds, then blended with the NHL player model (`model_weight` 0.3).
   - `edge = p_fair × odds − 1`.
   - The model must also show `live_model_min_edge` on its own.
5. **Rules.** These are the same as the NBA bot's. Min edge 5% (+3pp without a sharp or two-sided reference), odds 1.60–6.00, implausible edge > 25%, 18% max deviation from consensus, 3% max odds drop from the high, sharp movement ±2.0/1.5pp after 30 min, fresh odds (180 s), unders only with a two-sided or sharp reference, and one bet per player per game.
6. **Ledgers** in `data/`:

| Ledger | Content | Notified |
| --- | --- | --- |
| `nhl_live.json` | LIVE: edge ≥ 6%, model ≥ 3%, ≥ 2 reference groups, odds 1.60–3.00, in the last lineup. Max 5u per bet, 2 per match, 8 / 25u per US match day | ✅ ntfy |
| `nhl_bokforing.json` | everything that passes the shared rules | ❌ |
| `nhl_skugga.json` | ≥ 2% edge stopped by a rule (with the reasons) | ❌ |
| `nhl_modelltest.json` | the player model's own picks (model edge ≥ 5%) | ❌ |

Every open bet tracks the last pre-match price, so **CLV** is measured. `python -m propsbot report` shows record, ROI, average CLV and the share of bets that beat the close. `python -m propsbot export` writes Excel-ready CSVs (`;` separator, decimal comma).

### Running in the cloud on GitHub Actions (like the NBA and football bots)

`.github/workflows/nhl-bot.yml` runs `python -m propsbot scan`:
- every 10 minutes from 15:00 to 05:00 Swedish time, when props are posted and games are played;
- hourly the rest of the day, to settle bets and send the morning recap.

Each run starts on a fresh machine. It restores the ledgers, line history, Odds API budget and dashboard from the **`bot-data`** branch, scans, and saves them back. Only the latest state is kept, so the repository doesn't grow, and a failed restore never overwrites saved data.

**Setup (no git needed, all on github.com):**
1. **Create a new repository**, e.g. `nhl-propsbot`.
   - **Public** is recommended: Actions minutes are free and unlimited, and your secrets stay hidden.
   - A private repo gets 2,000 free minutes a month, and this schedule uses about 4,000.
2. On the empty repo page, click **uploading an existing file**, open the folder **`github_upload`** in Explorer, select everything inside it (including `.github`), drag it into the page, and click **Commit changes**.
3. Go to **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `NTFY_TOPIC`: your ntfy channel name
   - `PINNACLE_API_KEY`: the Pinnacle guest key (it's in your local `.env`)
   - `ODDS_API_KEY`: the same key your NBA and football bots use
4. Go to **Actions → NHL props bot → Run workflow** to test it. Then check the log for `Kambi NHL events …` and `Pinnacle games …`; a `! pinnacle: HTTP 403` line would mean Pinnacle blocks GitHub's US servers.
5. Stop `start.bat` on your PC, so only one copy runs.

**Dashboard:**
- **On your phone:** Settings → **Pages** → Source "Deploy from a branch" → branch `bot-data`, folder `/ (root)`. The dashboard is then at `https://<your-username>.github.io/<repo>/output/dashboard.html`. That address is public; it contains no secrets.
- **On your PC:** edit the one line in `dashboard_from_github.bat`, then double-click it.

**Good to know:**
- GitHub sometimes starts scheduled runs 5–15 minutes late at busy times.
- On a public repo, GitHub may pause the schedule after 60 days with no commits to the main branch. It emails you first; click "Enable workflow" to resume.
- After changing code or `settings.json`, upload the changed files again. To rebuild `github_upload` from the project, ask Claude or copy the same files again; never include `.env`.

### Running 24/7 without your laptop (own server)

The bot needs one always-on machine. Run it in **one place only**; two copies would send double notifications and keep separate ledgers.

**Location matters.** Pinnacle blocks the US and some other countries but works from Sweden, so use a server in **Stockholm or the Nordics**. `setup_server.sh` checks this for you.

| Option | Cost | Notes |
| --- | --- | --- |
| **Hetzner Cloud CX22**, Helsinki | ~50 SEK/month | Easiest. Finland, close to Sweden. Choose Ubuntu 24.04 |
| **Oracle Cloud Always Free**, Stockholm | free | A free VM in Sweden, but sign-up needs a card and free capacity is sometimes "out of stock" |
| **Raspberry Pi** at home | ~700 SEK once | Swedish IP, ~3 W power, no monthly fee |
| Laptop only in the evenings | free | Bets come mostly 15:00–01:00 Swedish time. Finished games settle on the next start, so you only miss bets while it's off |

**Moving it to a server:**
1. Create the server: Ubuntu 22.04+, smallest size, Swedish/Nordic location. Add your SSH key, or note the password.
2. Put the server's login in `deploy\server.cmd`, e.g. `set SERVER=root@203.0.113.10`.
3. Double-click `deploy\upload.bat`. It copies the code, settings and ledgers.
4. Run the setup once on the server:
   ```bash
   ssh root@203.0.113.10
   cd nhl-propsbot && bash deploy/setup_server.sh
   ```
   This installs Python, sets Swedish time (used for the daily recap), checks that Kambi and Pinnacle are reachable, and installs a service that starts at boot and restarts itself after crashes.
5. Your Odds API key is a Windows environment variable on the laptop, so it isn't copied. Add it on the server:
   ```bash
   echo 'ODDS_API_KEY=your_key' > ~/nhl-propsbot/.env
   sudo systemctl restart nhl-propsbot
   ```
6. Stop `start.bat` on the laptop.

Notifications keep working unchanged, since the topic is in `settings.json`. To see the dashboard, double-click `deploy\dashboard_from_server.bat`: it downloads the latest page and opens it. Live log: `journalctl -u nhl-propsbot -f`.

### Dashboard

Double-click **`dashboard.bat`** (or run `python -m propsbot dashboard`) to open `output\dashboard.html` in your browser. The bot rewrites it after every scan, and an open page reloads itself every 5 minutes. It's a single local file: no server, no account, nothing sent anywhere.

It shows:
- **The verdict:** collecting data / beating the close / losing to the close.
- **Live tiles:** progress to the 150-bet review, profit in units and SEK, ROI with 95% CI, and average CLV with its t-value.
- **Cumulative profit** for the live and data ledgers.
- **The running average CLV** with its 95% band.
- **Bets:** open live bets (with play-down-to prices) and recently settled ones.
- **Ledger comparison**, and CLV/ROI broken down by edge size.
- **Calibration** of every graded line, plus log loss for the model vs the references vs Kambi.

Every chart has hover details and a table view, and the page follows your system's light/dark mode. A warning appears at the top if the last scan is older than 75 minutes, which means the bot isn't running.

### Notifications (ntfy)

1. Install **ntfy** (Android/iPhone).
2. Tap **+** and subscribe to a topic name. Anyone who knows the name can read it, so use something unguessable, e.g. `nhl-props-7f3k2q`.
3. Put the same name in `settings.json` as `ntfy_topic`.
4. Run `python -m propsbot notify-test`. Your phone should ping.
5. Start `start.bat`. The PC must be on and awake while the bot runs.

You get:
- **Live bet** (high priority). It includes:
  - player, line, side, book and odds;
  - **play down to** = the lowest odds that still give the live edge;
  - other Kambi books' prices;
  - stake in units and SEK;
  - edge, model edge and reference sources.
- **Daily recap** (quiet, after 10:00): yesterday's live results, running ROI and CLV with its t-value, the number of graded lines, and progress to the 150-bet review. The recap also works as a heartbeat: if it doesn't arrive, the bot isn't running.
- **Health alert** after 3 failed scans in a row.

### Is it really finding +EV? (`python -m propsbot validate`)

Results alone are too noisy. At odds around 2.00 each bet has a standard deviation of about 1 unit, so a true 5% edge needs ~1,500 bets before ROI is statistically clear. The bot is judged on three levels, fastest first:

1. **CLV of live and data bets.** This compares the odds taken with the de-vigged reference consensus at puck drop (also against Kambi's own closing price, and as raw price movement). Per-bet CLV varies by only a few percent, so a real edge shows up after roughly **50–150 bets**. `validate` prints the mean, 95% CI and t-value, plus a verdict once 30+ bets have a closing price:
   - t ≥ 2: beating the close;
   - t ≤ −2: the edges are not real;
   - otherwise: how many bets are still needed.
2. **The leg log.** Every player/line the bot evaluated is logged (`data/line_history.sqlite`) with its opening, highest-edge and closing prices, then graded against the boxscore. That's hundreds of graded lines per night.
   - `validate` compares log loss for the model, the reference consensus, the blend and Kambi, which shows within days whether the model adds information (if not: lower `model_weight`).
   - It checks that the fair probability is calibrated.
   - It measures CLV and ROI for every "would-have-bet" line, which is much more than the 8 per day the live ledger allows.
3. **ROI with confidence interval** per ledger, plus an **edge-bucket table**. If the edges are real, bigger edges should give bigger CLV and ROI.

The data (`bokforing`), shadow (`skugga`) and model-test ledgers grow far faster than live, so they confirm or refute the rules before live reaches its 150-bet review.

Settings are in `settings.json` (created on first run). Set at least `bankroll` (1u = 0.2% of it) and `ntfy_topic`.

**Diagnostics.** `python -m propsbot kambi-probe` lists, per Kambi book, the SOG criteria found for each upcoming game. Kambi posts NHL player props only some hours before puck drop. If labels show up but nothing parses, `scan --diagnose` saves the raw JSON to `data/diagnos/`.

The commands below are the earlier projection and odds tools; the edge bot uses the same model.

- Pure Python 3.10+ standard library: nothing to install.
- Free NHL data from `api-web.nhle.com` / `api.nhle.com` (no key needed).
- Odds come from a manual CSV you fill in, plus The Odds API (optional).

## Quick start

```bash
python -m propsbot slate
```

The first run downloads game logs (about 30 s for a full slate; cached afterwards). It prints
projections and writes a fill-in odds sheet to `odds/YYYY-MM-DD.csv`.

1. Open `odds/YYYY-MM-DD.csv`.
2. For each line you see at your book, fill in `book`, `line`, `over` and `under`. Use decimal odds; a comma or a dot both work as the decimal separator.
3. Delete or ignore the rest. Rows with no book or no odds are skipped. The `model_mu` / `fair_*` columns are hints and are not read back.
4. Run `python -m propsbot slate` again to get picks.

```
book;player;team;line;over;under
Unibet;Tage Thompson;BUF;3,5;2,10;1,70
Svenska Spel;Rasmus Dahlin;BUF;2,5;2,15;1,65
ATG;Macklin Celebrini;SJS;2,5;1,62;2,25
```

The book names accepted are `Unibet`, `ATG`, `Svenska Spel` / `svenskaspel` / `Oddset`.
The `team` column is optional; it only helps when two players share a name.

## Where the odds come from

| Source | What it is used for |
| --- | --- |
| `odds/<date>.csv` (manual) | Prices at your books, which are the only books that get picks |
| The Odds API, `unibet_se`, `atg_se`, `svenskaspel_se` | Used automatically if they ever carry NHL SOG props (today they do not: The Odds API's player props are mostly US-only) |
| The Odds API, US books (`draftkings`, `fanduel`, ...) | **Market reference only.** Their de-vigged consensus is the "Market%" each pick is compared against |

Set `ODDS_API_KEY` in `.env` to enable The Odds API. Each run costs about one request
per game; the remaining quota is printed. A manual CSV row overrides an API quote for the same book.

## Model

For each skater:

1. **Shot rate.** SOG per minute over the last 25 games (topped up from last season early in the year). Recent games are weighted more (10-game half-life), and the rate is shrunk toward a forward or defense prior.
2. **Ice time.** A recency-weighted average of the last 10 games, ignoring games under 5 minutes (injuries).
3. **Matchup.** The opponent's shots allowed per game relative to league average, shrunk for small samples and capped at ±15%. Home ice adds 2% (away subtracts 2%).
4. **Distribution.** A negative binomial with mean = rate × TOI × matchup, which handles 0.5/1.5/2.5 lines and pushes on whole-number lines.

A bet is a **pick** when all of these hold:
- the player was in his team's last lineup;
- he has at least `MIN_GAMES` games of history;
- the odds are within `MIN_ODDS`–`MAX_ODDS`;
- EV ≥ `MIN_EV` and edge ≥ `MIN_EDGE`.

Edge is the model's probability minus the de-vigged market probability. Without a reference book, the market probability comes from your own books' two-way price ("market: single" / "bet_books").

Stake = bankroll × min(`KELLY_FRACTION` × Kelly, `MAX_STAKE_PCT`).

### Backtest

```bash
python -m propsbot backtest --season 20252026 --teams BUF,TOR,FLA,EDM
```

This is a walk-forward test: every game is predicted only from earlier games. It reports Brier score,
log loss and calibration against a naive last-10 average, plus the fitted dispersion to put
in `DISPERSION`. On 9,039 player-games from 2025-26 (8 teams) the model beat the naive baseline on
every line and was well calibrated through the middle of the range. Above about 60% it is a little
optimistic on overs, so treat very confident overs with care.

## Commands

| Command | Description |
| --- | --- |
| `python -m propsbot slate` | today's slate |
| `... slate --date 2026-11-05 --teams BUF,OTT` | specific date / games |
| `... slate --player "Thompson"` | one player |
| `... slate --show-all` | also show evaluated bets that did not qualify |
| `... slate --no-api` | manual CSV only (saves API quota) |
| `... slate --min-ev 0.05 --bankroll 5000` | override thresholds |
| `python -m propsbot backtest` | backtest the last completed season |
| `python -m propsbot clear-cache` | drop cached API responses |
| `python -m pytest` | run the tests |

Outputs go to `output/`:
- `projections_<date>.csv`
- `evaluations_<date>.csv`
- `picks_<date>.json`

All settings are in `.env.example`; copy it to `.env`.

## Caveats

- Lineups are inferred: a player counts as active if he played the team's last game. Check confirmed lineups and starting goalies before betting.
- Unibet, ATG and Svenska Spel rules on players who don't dress (void vs. loss) are the book's. The bot assumes the player plays.
- This is a statistical tool, not financial advice. Bet only what you can afford to lose. Stödlinjen: 020-81 91 00.

## Layout

```
propsbot/
  cli.py          commands and output wiring
  config.py       settings from .env
  http.py         JSON client with retries + disk cache
  nhl_api.py      schedule, rosters, game logs, team defense
  projections.py  shot-rate / TOI / matchup math
  slate.py        builds projections for a date
  model.py        negative binomial line probabilities
  odds.py         Odds API client, manual CSV loader, template writer
  pricing.py      odds conversion, de-vig, EV, Kelly
  edges.py        matches odds to players and selects picks
  report.py       tables, CSV, JSON
  backtest.py     walk-forward evaluation
tests/            unit tests (no network)
```

# ⚽ Football Transfer & Financial Fair Play (FFP) Intelligence Dashboard

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-brightgreen?style=for-the-badge&logo=github)](https://readuanulfaridfahim.github.io/football-transfers-ffp/)
[![Repository](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/ReaduanulFaridFahim/football-transfers-ffp)

🌐 **Live Hosted Dashboard**: [https://readuanulfaridfahim.github.io/football-transfers-ffp/](https://readuanulfaridfahim.github.io/football-transfers-ffp/)

This project connects to and explores the Transfermarkt dataset from Kaggle:
**[davidcariboo/player-scores](https://www.kaggle.com/datasets/davidcariboo/player-scores)**

---

## 📁 Available Dataset Files (in `data/`)

| File | Description |
| :--- | :--- |
| `transfers.csv` | Historical and recent transfer records, fees, origin/destination clubs |
| `players.csv` | Player profiles, positions, market values, nationalities, contracts |
| `clubs.csv` | Club details, domestic competitions, squad size, stadium info |
| `competitions.csv` | Leagues and tournaments across Europe and worldwide |
| `player_valuations.csv` | Market value historical progression over time |
| `games.csv` | Match schedules, results, home/away scores |
| `game_events.csv` | Goals, assists, substitutions, yellow/red cards |
| `game_lineups.csv` | Starting lineups and squad lists for matches |
| `club_games.csv` | Club match statistics per game |
| `appearances.csv` | Player match appearances, minutes played, goals, assists |
| `countries.csv` | Country metadata and continents |
| `national_teams.csv` | National football teams |

---

## ⚖️ Financial Fair Play (FFP) & Spending Regulation

Under UEFA FFP and Premier League PSR (Profitability & Sustainability Rules), transfer spending is monitored based on **Net Transfer Spend** (Money spent buying players minus money earned selling players = Net Deficit):

1. **20-Year Cumulative Deficit Benchmark**:
   - Clubs with over **€1.0 Billion net transfer loss** are flagged with `[BREACH RISK]`.
2. **Single-Season Transfer Window Rule**:
   - Transfer seasons with over **€100 Million net transfer deficit** are flagged as `[EXCEEDED LIMIT]`.
3. **The Manchester City Dossier (Why They Got Banned & The 115 Charges)**:
   - **2020 UEFA Champions League Ban**: 2-year European ban & €30M fine for disguising owner funding as sponsorship revenue (Etihad/Etisalat). Later overturned by CAS due to a 5-year statute of limitations ("time-barred"), but a €10M non-cooperation fine was upheld.
   - **2023 Premier League 115 Charges**: 115 alleged financial breaches spanning 9 seasons (2009/10–2017/18) where statute of limitations does *not* apply:
     - 54 charges: Inaccurate financial reporting & inflated commercial income.
     - 14 charges: Hidden manager/player pay (e.g. secret shadow contracts for Roberto Mancini).
     - 5 charges: Breaching UEFA FFP regulations.
     - 7 charges: Breaching Premier League PSR deficit limits.
     - 35 charges: Failing to cooperate with the Premier League's investigation.
   - **Transfer Market Connection**: Over **€1.03 Billion** spent during the charged era alone on stars like De Bruyne, Sterling, Mahrez, Laporte, Walker, and Stones.

---

## 🚀 How to Run

### Run the Analysis:
```powershell
.\.venv\Scripts\python.exe football_transfers.py
```
or the dedicated FFP script:
```powershell
.\.venv\Scripts\python.exe financial_fair_play_analysis.py
```

### Python Code Example:
```python
from football_transfers import get_20yr_top_spenders, get_single_season_rule_breaks

# 1. Top spenders in the last 20 years with custom regulatory limit (e.g. €1B):
top_spenders = get_20yr_top_spenders(
    start_year=2005,
    regulatory_net_limit_eur=1_000_000_000.0,
    top_n=20
)
print(top_spenders)

# 2. Single-season transfer window regulatory breaches (e.g. €100M limit):
rule_breaks = get_single_season_rule_breaks(
    start_year=2005,
    single_season_net_limit_eur=100_000_000.0,
    top_n=15
)
print(rule_breaks)
```

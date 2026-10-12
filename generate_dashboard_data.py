"""
Dashboard Data Generator
========================
Processes Transfermarkt datasets and extracts aggregated JSON for the interactive web dashboard.
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def run_export():
    print("Loading data...")
    transfers = pd.read_csv(DATA_DIR / "transfers.csv", low_memory=False)
    clubs = pd.read_csv(DATA_DIR / "clubs.csv", low_memory=False)
    competitions = pd.read_csv(DATA_DIR / "competitions.csv", low_memory=False)

    # 1. Clean transfers
    transfers["transfer_date"] = pd.to_datetime(transfers["transfer_date"], errors="coerce")
    transfers["transfer_fee"] = pd.to_numeric(transfers["transfer_fee"], errors="coerce").fillna(0)
    transfers["transfer_year"] = transfers["transfer_date"].dt.year
    transfers["player_name"] = transfers["player_name"].fillna("Unknown Player")

    # 2. League lookup
    comp_map = dict(zip(competitions["competition_id"], competitions["name"]))
    comp_country = dict(zip(competitions["competition_id"], competitions["country_name"]))
    
    # Map club_name or club_id to league
    club_league = {}
    club_country = {}
    for _, r in clubs.iterrows():
        c_id = r["domestic_competition_id"]
        c_name = str(r["name"])
        c_code = str(r["club_code"]) if pd.notna(r["club_code"]) else ""
        league = comp_map.get(c_id, "Other / Unknown")
        country = comp_country.get(c_id, "Other")
        club_league[c_name] = league
        club_country[c_name] = country
        if c_code:
            club_league[c_code] = league
            club_country[c_code] = country

    # Custom pretty league names
    def clean_league_name(name):
        n = str(name).lower()
        if "premier-league" in n or n == "gb1": return "Premier League (England)"
        if "laliga" in n or "primera-division" in n or n == "es1": return "LaLiga (Spain)"
        if "serie-a" in n or n == "it1": return "Serie A (Italy)"
        if "bundesliga" in n or n == "l1": return "Bundesliga (Germany)"
        if "ligue-1" in n or n == "fr1": return "Ligue 1 (France)"
        if "saudi" in n or "pro-league" in n: return "Saudi Pro League"
        if "liga-portugal" in n or "primeira" in n: return "Liga Portugal"
        if "eredivisie" in n: return "Eredivisie (Netherlands)"
        return "Other Leagues"

    # Known club shortcuts
    popular_leagues = {
        "Chelsea": "Premier League (England)",
        "Man City": "Premier League (England)",
        "Man Utd": "Premier League (England)",
        "Arsenal": "Premier League (England)",
        "Liverpool": "Premier League (England)",
        "Tottenham": "Premier League (England)",
        "Newcastle": "Premier League (England)",
        "West Ham": "Premier League (England)",
        "Aston Villa": "Premier League (England)",
        "Brighton": "Premier League (England)",
        "Real Madrid": "LaLiga (Spain)",
        "Barcelona": "LaLiga (Spain)",
        "Atltico": "LaLiga (Spain)",
        "Atlético": "LaLiga (Spain)",
        "Juventus": "Serie A (Italy)",
        "AC Milan": "Serie A (Italy)",
        "Inter": "Serie A (Italy)",
        "Napoli": "Serie A (Italy)",
        "Roma": "Serie A (Italy)",
        "Bayern Munich": "Bundesliga (Germany)",
        "Dortmund": "Bundesliga (Germany)",
        "Leipzig": "Bundesliga (Germany)",
        "PSG": "Ligue 1 (France)",
        "Monaco": "Ligue 1 (France)",
        "Marseille": "Ligue 1 (France)",
        "Lyon": "Ligue 1 (France)",
        "Al-Hilal": "Saudi Pro League",
        "Al-Nassr": "Saudi Pro League",
        "Al-Ahli": "Saudi Pro League",
        "Al-Ittihad": "Saudi Pro League",
        "Benfica": "Liga Portugal",
        "Porto": "Liga Portugal",
        "Sporting CP": "Liga Portugal",
        "Ajax": "Eredivisie (Netherlands)",
    }

    def get_club_league(c_name):
        if c_name in popular_leagues:
            return popular_leagues[c_name]
        raw = club_league.get(c_name, "")
        if raw:
            return clean_league_name(raw)
        return "Other Leagues"

    # 3. Market Totals by Season (2005-2026)
    s_mask = (transfers["transfer_year"] >= 2005) & (transfers["transfer_year"] <= 2026)
    seasons_order = [
        "05/06", "06/07", "07/08", "08/09", "09/10",
        "10/11", "11/12", "12/13", "13/14", "14/15",
        "15/16", "16/17", "17/18", "18/19", "19/20",
        "20/21", "21/22", "22/23", "23/24", "24/25", "25/26"
    ]
    market_seasons = []
    for s in seasons_order:
        s_df = transfers[transfers["transfer_season"] == s]
        total_spent = float(s_df["transfer_fee"].sum())
        count = int((s_df["transfer_fee"] > 0).sum())
        market_seasons.append({
            "season": s,
            "total_spent_eur": total_spent,
            "transfers_count": count
        })

    # 4. Function to generate club rankings for a given year window
    def build_rankings(start_yr, end_yr, top_k=40):
        t_win = transfers[(transfers["transfer_year"] >= start_yr) & (transfers["transfer_year"] <= end_yr)]
        sp = t_win[t_win["to_club_name"].notna()].groupby("to_club_name")["transfer_fee"].sum().rename("spent")
        inc = t_win[t_win["from_club_name"].notna()].groupby("from_club_name")["transfer_fee"].sum().rename("income")
        m = pd.concat([sp, inc], axis=1).fillna(0)
        m["net_spend"] = m["spent"] - m["income"]
        m = m.sort_values("spent", ascending=False).head(top_k)

        # Club season breakdown for charts
        clubs_list = []
        for c_name, row in m.iterrows():
            c_league = get_club_league(c_name)
            # Season trajectory
            c_in = t_win[t_win["to_club_name"] == c_name].groupby("transfer_season")["transfer_fee"].sum()
            c_out = t_win[t_win["from_club_name"] == c_name].groupby("transfer_season")["transfer_fee"].sum()
            s_map = {}
            for s in seasons_order:
                s_sp = float(c_in.get(s, 0.0))
                s_inc = float(c_out.get(s, 0.0))
                s_map[s] = {
                    "spent": s_sp,
                    "income": s_inc,
                    "net_spend": s_sp - s_inc
                }

            clubs_list.append({
                "club": c_name,
                "league": c_league,
                "spent": float(row["spent"]),
                "income": float(row["income"]),
                "net_spend": float(row["net_spend"]),
                "seasons": s_map
            })
        return clubs_list

    print("Computing 20y, 10y, 5y windows...")
    rankings_20y = build_rankings(2005, 2026, 40)
    rankings_10y = build_rankings(2015, 2026, 40)
    rankings_5y = build_rankings(2020, 2026, 40)

    # 5. Single Season Violations (top 60)
    t_recent = transfers[transfers["transfer_year"] >= 2005]
    s_sp = t_recent[t_recent["to_club_name"].notna()].groupby(["to_club_name", "transfer_season"])["transfer_fee"].sum().rename("spent")
    s_inc = t_recent[t_recent["from_club_name"].notna()].groupby(["from_club_name", "transfer_season"])["transfer_fee"].sum().rename("income")
    s_all = pd.concat([s_sp, s_inc], axis=1).fillna(0)
    s_all["net_spend"] = s_all["spent"] - s_all["income"]
    s_all = s_all.reset_index().rename(columns={"level_0": "club_name"})
    s_top_violations = s_all[s_all["net_spend"] > 0].sort_values("net_spend", ascending=False).head(50)

    violations_list = []
    for _, r in s_top_violations.iterrows():
        violations_list.append({
            "club": str(r["club_name"]),
            "season": str(r["transfer_season"]),
            "league": get_club_league(str(r["club_name"])),
            "spent": float(r["spent"]),
            "income": float(r["income"]),
            "net_spend": float(r["net_spend"])
        })

    # 6. Top 50 Transfers of all time
    top_t = transfers.dropna(subset=["transfer_fee"]).sort_values("transfer_fee", ascending=False).head(50)
    transfers_list = []
    for _, r in top_t.iterrows():
        transfers_list.append({
            "player_name": str(r["player_name"]),
            "fee": float(r["transfer_fee"]),
            "market_value": float(r["market_value_in_eur"]) if pd.notna(r["market_value_in_eur"]) else None,
            "transfer_date": str(r["transfer_date"])[:10] if pd.notna(r["transfer_date"]) else "",
            "transfer_season": str(r["transfer_season"]) if pd.notna(r["transfer_season"]) else "",
            "from_club": str(r["from_club_name"]),
            "to_club": str(r["to_club_name"])
        })

    # 7. Manchester City Case Study Data
    mc_win = transfers[(transfers["transfer_year"] >= 2008) & (transfers["transfer_year"] <= 2018) & (transfers["to_club_name"] == "Man City")]
    mc_top_t = mc_win.sort_values("transfer_fee", ascending=False).head(12)
    mc_transfers = []
    for _, r in mc_top_t.iterrows():
        mc_transfers.append({
            "player": str(r["player_name"]),
            "season": str(r["transfer_season"]),
            "fee": float(r["transfer_fee"]),
            "from": str(r["from_club_name"])
        })

    mancity_case = {
        "title": "Manchester City FFP Case: Why They Got Banned & The 115 Charges",
        "club": "Manchester City",
        "total_spent_20y": 2478430000.0,
        "total_income_20y": 981300000.0,
        "net_deficit_20y": 1497130000.0,
        "investigated_era_spend": float(mc_win["transfer_fee"].sum()),
        "investigated_seasons": "2009/10 to 2017/18 (9 Seasons)",
        "uefa_ban": {
            "year": "2020",
            "sanction": "2-Year Champions League Ban + €30M Fine",
            "authority": "UEFA Club Financial Control Body (CFCB)",
            "allegation": "Disguising owner equity funding as commercial sponsorship income from Abu Dhabi entities (e.g. Etihad, Etisalat) to bypass UEFA FFP deficit rules.",
            "cas_appeal_result": "OVERTURNED by Court of Arbitration for Sport (CAS) in July 2020.",
            "cas_reason": "CAS ruled that UEFA's allegations were 'time-barred' under UEFA's 5-year statute of limitations rule. However, CAS upheld a €10M fine for obstructing and failing to cooperate with UEFA's investigation."
        },
        "pl_charges_breakdown": [
            {
                "category": "Inaccurate Financial Accounts & Inflated Revenue",
                "count": 54,
                "period": "2009/10 to 2017/18",
                "description": "Allegations that sponsorship money supposedly from UAE companies was actually paid directly by club owners (ADUG), artificially inflating revenue so the club could spend lavishly on transfers without reporting FFP losses."
            },
            {
                "category": "Secret & Undisclosed Remuneration",
                "count": 14,
                "period": "2009/10 to 2015/16",
                "description": "Failure to disclose full payments to managers and players. Allegations include former manager Roberto Mancini receiving a secret second salary through Abu Dhabi club Al Jazira, and secret player image rights contracts."
            },
            {
                "category": "Breaches of UEFA FFP Regulations",
                "count": 5,
                "period": "2013/14 to 2017/18",
                "description": "Failing to comply with UEFA's Club Licensing and Financial Fair Play regulations submitted through the Premier League."
            },
            {
                "category": "Breaches of Premier League PSR Rules",
                "count": 7,
                "period": "2015/16 to 2017/18",
                "description": "Breaching Premier League Profitability & Sustainability Rules (PSR) allowing maximum losses of £105M over a 3-year monitoring period."
            },
            {
                "category": "Failure to Cooperate with Investigations",
                "count": 35,
                "period": "2018/19 to 2022/23",
                "description": "Refusing to provide documents, delaying proceedings, and failing to cooperate in good faith with the Premier League's multi-year independent investigation."
            }
        ],
        "potential_sanctions": [
            {"type": "Historic Points Deduction", "severity": "Extreme", "detail": "Massive deduction (e.g. 30 to 100+ points), potentially causing immediate relegation."},
            {"type": "Expulsion / Relegation", "severity": "Ultimate", "detail": "Expulsion from the Premier League and forced relegation to lower tiers of English football."},
            {"type": "Retroactive Title Stripping", "severity": "High", "detail": "Stripping Premier League titles won during the investigated period (2012, 2014, 2018)."},
            {"type": "Transfer Ban & Fines", "severity": "High", "detail": "Multi-window transfer ban prohibiting new player signings and astronomical fines."}
        ],
        "key_transfers": mc_transfers
    }

    output_data = {
        "meta": {
            "title": "Football Transfer Market & Financial Fair Play Intelligence",
            "dataset_url": "https://www.kaggle.com/datasets/davidcariboo/player-scores",
            "source": "Transfermarkt",
            "last_updated": "2026",
            "seasons_list": seasons_order
        },
        "market_seasons": market_seasons,
        "rankings_20y": rankings_20y,
        "rankings_10y": rankings_10y,
        "rankings_5y": rankings_5y,
        "violations": violations_list,
        "top_transfers": transfers_list,
        "mancity_case": mancity_case
    }

    out_file = BASE_DIR / "dashboard_data.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    # Also update data.js
    data_js_file = BASE_DIR / "data.js"
    with open(data_js_file, "w", encoding="utf-8") as f:
        f.write("window.EMBEDDED_DASHBOARD_DATA = " + json.dumps(output_data) + ";")

    print(f"Data exported successfully to {out_file} and {data_js_file}")

if __name__ == "__main__":
    run_export()


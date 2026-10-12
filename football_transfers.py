"""
Football Transfer & Financial Fair Play (FFP) Analysis
======================================================
Dataset: https://www.kaggle.com/datasets/davidcariboo/player-scores
Data source: Transfermarkt via kagglehub / local data directory

Available tables:
- appearances.csv, club_games.csv, clubs.csv, competitions.csv, countries.csv
- game_events.csv, game_lineups.csv, games.csv, national_teams.csv
- player_valuations.csv, players.csv, transfers.csv
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import kagglehub

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 1. Determine Data Directory
BASE_DIR = Path(__file__).resolve().parent
LOCAL_DATA_DIR = BASE_DIR / "data"

def get_dataset_path() -> Path:
    """
    Returns the path to the dataset files.
    Prefers the local workspace 'data' folder, otherwise fetches/connects via kagglehub.
    """
    if LOCAL_DATA_DIR.exists() and (LOCAL_DATA_DIR / "transfers.csv").exists():
        return LOCAL_DATA_DIR
    
    print("Fetching dataset via kagglehub...")
    cached_path = kagglehub.dataset_download("davidcariboo/player-scores")
    return Path(cached_path)

DATASET_DIR = get_dataset_path()

def list_tables() -> list[str]:
    """Lists all available CSV tables in the dataset."""
    return sorted([f.stem for f in DATASET_DIR.glob("*.csv")])

def load_table(name: str, nrows: int | None = None) -> pd.DataFrame:
    """
    Load a table by name (e.g. 'transfers', 'players', 'clubs').
    """
    file_path = DATASET_DIR / f"{name}.csv"
    if not file_path.exists():
        available = list_tables()
        raise FileNotFoundError(f"Table '{name}' not found. Available tables: {available}")
    
    return pd.read_csv(file_path, nrows=nrows, low_memory=False)

def get_top_transfers(n: int = 10) -> pd.DataFrame:
    """Returns the top N transfers by transfer fee in EUR."""
    transfers = load_table("transfers")
    transfers["transfer_fee"] = pd.to_numeric(transfers["transfer_fee"], errors="coerce")
    top = transfers.dropna(subset=["transfer_fee"]).sort_values(by="transfer_fee", ascending=False).head(n)
    return top[["player_name", "transfer_date", "from_club_name", "to_club_name", "transfer_fee", "market_value_in_eur"]]

def get_most_valuable_players(n: int = 10) -> pd.DataFrame:
    """Returns the top N most valuable players by market value in EUR."""
    players = load_table("players")
    players["market_value_in_eur"] = pd.to_numeric(players["market_value_in_eur"], errors="coerce")
    top = players.dropna(subset=["market_value_in_eur"]).sort_values(by="market_value_in_eur", ascending=False).head(n)
    return top[["name", "current_club_name", "position", "country_of_citizenship", "market_value_in_eur", "highest_market_value_in_eur"]]

def search_player_transfers(player_name: str) -> pd.DataFrame:
    """Search transfer history for a specific player."""
    transfers = load_table("transfers")
    matches = transfers[transfers["player_name"].str.contains(player_name, case=False, na=False)]
    return matches[["player_name", "transfer_season", "transfer_date", "from_club_name", "to_club_name", "transfer_fee"]].sort_values("transfer_date", ascending=False)

# =====================================================================
# FINANCIAL FAIR PLAY & FINANCIAL REGULATION MONITORING
# =====================================================================

def get_20yr_top_spenders(
    start_year: int = 2005,
    end_year: int = 2026,
    regulatory_net_limit_eur: float = 1_000_000_000.0,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Finds which teams spent the most money in the transfer market over the last 20 years,
    and flags clubs that breached the regulatory limit on net deficit (spend - income).
    """
    df = load_table("transfers")
    df["transfer_date"] = pd.to_datetime(df["transfer_date"], errors="coerce")
    df["transfer_fee"] = pd.to_numeric(df["transfer_fee"], errors="coerce").fillna(0)
    df["transfer_year"] = df["transfer_date"].dt.year

    mask = (df["transfer_year"] >= start_year) & (df["transfer_year"] <= end_year)
    df_window = df[mask]

    # Gross Spend (buying club = to_club_name)
    spend = df_window[df_window["to_club_name"].notna()].groupby("to_club_name")["transfer_fee"].sum().rename("total_spent")
    # Income from sales (selling club = from_club_name)
    income = df_window[df_window["from_club_name"].notna()].groupby("from_club_name")["transfer_fee"].sum().rename("total_income")

    summary = pd.concat([spend, income], axis=1).fillna(0)
    summary["net_spend"] = summary["total_spent"] - summary["total_income"]
    summary = summary.sort_values(by="total_spent", ascending=False).head(top_n)

    summary["breach"] = summary["net_spend"] > regulatory_net_limit_eur
    summary["over_limit"] = np.maximum(0, summary["net_spend"] - regulatory_net_limit_eur)

    display_df = pd.DataFrame({
        "Club": summary.index,
        "Total Spent (EUR M)": (summary["total_spent"] / 1e6).round(1),
        "Total Income (EUR M)": (summary["total_income"] / 1e6).round(1),
        "Net Deficit (EUR M)": (summary["net_spend"] / 1e6).round(1),
        "Limit (EUR M)": (regulatory_net_limit_eur / 1e6),
        "Status": summary["breach"].apply(lambda x: "[BREACH RISK]" if x else "[COMPLIANT]"),
        "Over Limit by (EUR M)": (summary["over_limit"] / 1e6).round(1),
    }).reset_index(drop=True)

    return display_df

def get_single_season_rule_breaks(
    start_year: int = 2005,
    single_season_net_limit_eur: float = 100_000_000.0,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Finds single-season transfer windows where a club's net loss exceeded
    the regulatory limit (default: EUR 100 Million).
    """
    df = load_table("transfers")
    df["transfer_date"] = pd.to_datetime(df["transfer_date"], errors="coerce")
    df["transfer_fee"] = pd.to_numeric(df["transfer_fee"], errors="coerce").fillna(0)
    df["transfer_year"] = df["transfer_date"].dt.year

    df_window = df[df["transfer_year"] >= start_year]

    s_spend = df_window[df_window["to_club_name"].notna()].groupby(["to_club_name", "transfer_season"])["transfer_fee"].sum().rename("spend")
    s_income = df_window[df_window["from_club_name"].notna()].groupby(["from_club_name", "transfer_season"])["transfer_fee"].sum().rename("income")

    seasons = pd.concat([s_spend, s_income], axis=1).fillna(0)
    seasons["net_spend"] = seasons["spend"] - seasons["income"]
    seasons = seasons.reset_index().rename(columns={"level_0": "club_name"})

    breaches = seasons[seasons["net_spend"] > single_season_net_limit_eur].copy()
    breaches = breaches.sort_values(by="net_spend", ascending=False).head(top_n)

    result_df = pd.DataFrame({
        "Club": breaches["club_name"],
        "Season": breaches["transfer_season"],
        "Spent (EUR M)": (breaches["spend"] / 1e6).round(1),
        "Income (EUR M)": (breaches["income"] / 1e6).round(1),
        "Net Deficit (EUR M)": (breaches["net_spend"] / 1e6).round(1),
        "Season Limit (EUR M)": (single_season_net_limit_eur / 1e6),
        "Deficit Over Limit (EUR M)": ((breaches["net_spend"] - single_season_net_limit_eur) / 1e6).round(1),
        "Rule Alert": "[EXCEEDED LIMIT]",
    }).reset_index(drop=True)

    return result_df

if __name__ == "__main__":
    print(f"Dataset location: {DATASET_DIR}\n")

    print("=" * 80)
    print(" 1. TOP 20 BIGGEST SPENDERS IN LAST 20 YEARS (2005 - 2025)")
    print(" Regulatory Benchmark: Max Allowable 20-Year Net Deficit = EUR 1,000M (EUR 1.0B)")
    print("=" * 80)
    top_spenders = get_20yr_top_spenders(regulatory_net_limit_eur=1_000_000_000.0, top_n=20)
    print(top_spenders.to_string(index=True))

    print("\n" + "=" * 80)
    print(" 2. TRANSFER WINDOW RULE BREAKS: BIGGEST SINGLE-SEASON NET DEFICITS")
    print(" Regulatory Benchmark: Single-Season Net Deficit Limit = EUR 100M")
    print("=" * 80)
    season_breaks = get_single_season_rule_breaks(single_season_net_limit_eur=100_000_000.0, top_n=15)
    print(season_breaks.to_string(index=True))

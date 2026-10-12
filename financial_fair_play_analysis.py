"""
Financial Fair Play (FFP) & Transfer Market Spending Analysis
=============================================================
Dataset: Transfermarkt (https://www.kaggle.com/datasets/davidcariboo/player-scores)

This script analyzes:
1. Which football clubs spent the most money in the transfer market in the last 20 years.
2. Net transfer spending (Gross Spend - Income from sales = Deficit).
3. Financial Fair Play / Regulatory threshold breaches (both 20-year cumulative & single-season transfer windows).
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Path configurations
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TRANSFERS_CSV = DATA_DIR / "transfers.csv"


def load_transfers_data() -> pd.DataFrame:
    """Loads transfers.csv with cleaned dates and numerical fees."""
    if not TRANSFERS_CSV.exists():
        raise FileNotFoundError(
            f"Could not find {TRANSFERS_CSV}. Please ensure dataset is downloaded in the data/ folder."
        )

    print("Loading transfer records...")
    df = pd.read_csv(TRANSFERS_CSV, low_memory=False)
    df["transfer_date"] = pd.to_datetime(df["transfer_date"], errors="coerce")
    df["transfer_fee"] = pd.to_numeric(df["transfer_fee"], errors="coerce").fillna(0)
    df["transfer_year"] = df["transfer_date"].dt.year
    return df


def get_20yr_top_spenders(
    df: pd.DataFrame,
    start_year: int = 2005,
    end_year: int = 2026,
    regulatory_net_limit_eur: float = 1_000_000_000.0,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Finds the clubs that spent the most money in the transfer market over the last 20 years,
    and checks them against a financial regulatory limit (allowable net deficit).

    Parameters:
    - start_year: Start year for 20-year window (default: 2005)
    - end_year: End year (default: 2026)
    - regulatory_net_limit_eur: Allowed net spend threshold before financial rule alert (default: €1.0 Billion)
    - top_n: Number of top clubs to display (default: 20)
    """
    # Filter 20-year range
    mask = (df["transfer_year"] >= start_year) & (df["transfer_year"] <= end_year)
    df_window = df[mask]

    # Gross Spend: buying club is 'to_club_name'
    spend = (
        df_window[df_window["to_club_name"].notna()]
        .groupby("to_club_name")["transfer_fee"]
        .sum()
        .rename("total_spent")
    )

    # Income from sales: selling club is 'from_club_name'
    income = (
        df_window[df_window["from_club_name"].notna()]
        .groupby("from_club_name")["transfer_fee"]
        .sum()
        .rename("total_income")
    )

    # Combine spend and income
    summary = pd.concat([spend, income], axis=1).fillna(0)
    summary["net_spend"] = summary["total_spent"] - summary["total_income"]

    # Sort by total money spent (gross spend)
    summary = summary.sort_values(by="total_spent", ascending=False).head(top_n)

    # Apply Financial Regulatory Rule
    summary["regulatory_limit"] = regulatory_net_limit_eur
    summary["breach"] = summary["net_spend"] > regulatory_net_limit_eur
    summary["over_limit"] = np.maximum(
        0, summary["net_spend"] - regulatory_net_limit_eur
    )

    # Format for clean display
    display_df = pd.DataFrame(
        {
            "Club": summary.index,
            "Total Spent (€M)": (summary["total_spent"] / 1e6).round(1),
            "Total Income (€M)": (summary["total_income"] / 1e6).round(1),
            "Net Deficit (€M)": (summary["net_spend"] / 1e6).round(1),
            "Limit (€M)": (regulatory_net_limit_eur / 1e6),
            "Status": summary["breach"].apply(
                lambda x: "[BREACH RISK]" if x else "[COMPLIANT]"
            ),
            "Over Limit by (€M)": (summary["over_limit"] / 1e6).round(1),
        }
    ).reset_index(drop=True)

    return display_df


def get_single_season_rule_breaks(
    df: pd.DataFrame,
    start_year: int = 2005,
    single_season_net_limit_eur: float = 100_000_000.0,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Detects single-season transfer windows where a club's net loss (spend - income)
    exceeded UEFA Financial Fair Play / domestic regulation safety limits (e.g. > €100M in one season).
    """
    df_window = df[df["transfer_year"] >= start_year]

    # Calculate spend and income per club per season
    s_spend = (
        df_window[df_window["to_club_name"].notna()]
        .groupby(["to_club_name", "transfer_season"])["transfer_fee"]
        .sum()
        .rename("spend")
    )

    s_income = (
        df_window[df_window["from_club_name"].notna()]
        .groupby(["from_club_name", "transfer_season"])["transfer_fee"]
        .sum()
        .rename("income")
    )

    seasons = pd.concat([s_spend, s_income], axis=1).fillna(0)
    seasons["net_spend"] = seasons["spend"] - seasons["income"]
    seasons = seasons.reset_index().rename(columns={"level_0": "club_name"})

    # Filter for seasons where net spend exceeds the limit
    breaches = seasons[seasons["net_spend"] > single_season_net_limit_eur].copy()
    breaches = breaches.sort_values(by="net_spend", ascending=False).head(top_n)

    result_df = pd.DataFrame(
        {
            "Club": breaches["club_name"],
            "Season": breaches["transfer_season"],
            "Spent (€M)": (breaches["spend"] / 1e6).round(1),
            "Income (€M)": (breaches["income"] / 1e6).round(1),
            "Net Deficit (€M)": (breaches["net_spend"] / 1e6).round(1),
            "Season Limit (€M)": (single_season_net_limit_eur / 1e6),
            "Deficit Over Limit (€M)": (
                (breaches["net_spend"] - single_season_net_limit_eur) / 1e6
            ).round(1),
            "Rule Alert": "[EXCEEDED LIMIT]",
        }
    ).reset_index(drop=True)

    return result_df


if __name__ == "__main__":
    df = load_transfers_data()

    print("\n" + "=" * 90)
    print(" FINANCIAL FAIR PLAY ANALYSIS: TOP 20 SPENDERS IN THE LAST 20 YEARS (2005 - 2025)")
    print(" Regulatory Benchmark: Max Allowable Cumulative Net Deficit = €1,000 Million (€1.0B)")
    print("=" * 90)

    top_20 = get_20yr_top_spenders(
        df,
        start_year=2005,
        regulatory_net_limit_eur=1_000_000_000.0,  # €1 Billion Net Deficit Benchmark
        top_n=20,
    )
    print(top_20.to_string(index=True))

    print("\n" + "=" * 90)
    print(" TRANSFER WINDOW RULE BREAK DETECTOR: TOP SINGLE-SEASON NET DEFICITS")
    print(" Regulatory Benchmark: Single-Season Net Deficit Limit = €100 Million (€100M)")
    print("=" * 90)

    season_breaks = get_single_season_rule_breaks(
        df,
        start_year=2005,
        single_season_net_limit_eur=100_000_000.0,  # €100 Million per season benchmark
        top_n=15,
    )
    print(season_breaks.to_string(index=True))

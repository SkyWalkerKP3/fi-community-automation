"""
Fetches weekly market data for the FI Community report.
Usage: python scripts/fetch_market_data.py --output output/DATE_market_data.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
PORTFOLIO_CONFIG = ROOT / "resources" / "portfolio_config.json"


def pct(val):
    return round(float(val), 2) if val is not None else None


def fetch_index(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="5d")
    if hist.empty or len(hist) < 2:
        return {"ticker": ticker_symbol, "week_change_pct": None, "current": None}
    current = hist["Close"].iloc[-1]
    prev = hist["Close"].iloc[0]
    change_pct = pct(((current - prev) / prev) * 100)
    return {
        "ticker": ticker_symbol,
        "current": round(float(current), 2),
        "week_change_pct": change_pct,
        "direction": "up" if change_pct and change_pct >= 0 else "down",
    }


def fetch_stock(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="5d")
    info = {}
    try:
        info = ticker.info or {}
    except Exception:
        pass

    if hist.empty or len(hist) < 2:
        return {
            "ticker": ticker_symbol,
            "name": info.get("longName", ticker_symbol),
            "current_price": None,
            "week_change_pct": None,
            "direction": None,
        }

    current = hist["Close"].iloc[-1]
    prev = hist["Close"].iloc[0]
    change_pct = pct(((current - prev) / prev) * 100)

    return {
        "ticker": ticker_symbol,
        "name": info.get("longName", ticker_symbol),
        "current_price": round(float(current), 2),
        "week_change_pct": change_pct,
        "direction": "up" if change_pct and change_pct >= 0 else "down",
        "sector": info.get("sector", ""),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    with open(PORTFOLIO_CONFIG) as f:
        config = json.load(f)

    print("Fetching index data...")
    sp500 = fetch_index("^GSPC")
    nasdaq = fetch_index("^IXIC")
    dow = fetch_index("^DJI")

    print("Fetching holdings data...")
    holdings = []
    for ticker in config.get("club_holdings", []):
        print(f"  {ticker}...")
        holdings.append(fetch_stock(ticker))

    print("Fetching watchlist data...")
    watchlist = []
    for ticker in config.get("watchlist", []):
        print(f"  {ticker}...")
        watchlist.append(fetch_stock(ticker))

    output = {
        "fetched_at": datetime.now().isoformat(),
        "week_ending": datetime.now().strftime("%Y-%m-%d"),
        "indices": {
            "sp500": sp500,
            "nasdaq": nasdaq,
            "dow": dow,
        },
        "holdings": holdings,
        "watchlist": watchlist,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nMarket data saved to: {out_path}")
    print(f"  S&P 500:  {sp500['week_change_pct']:+.2f}%" if sp500['week_change_pct'] else "  S&P 500: N/A")
    print(f"  Nasdaq:   {nasdaq['week_change_pct']:+.2f}%" if nasdaq['week_change_pct'] else "  Nasdaq: N/A")
    print(f"  Dow:      {dow['week_change_pct']:+.2f}%" if dow['week_change_pct'] else "  Dow: N/A")


if __name__ == "__main__":
    main()

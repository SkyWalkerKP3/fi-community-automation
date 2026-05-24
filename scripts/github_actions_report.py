#!/usr/bin/env python3
"""GitHub Actions pipeline — FI Community weekly report.
Uses Anthropic SDK with web search to research, synthesize, and generate the PDF.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).parent.parent
DATE = date.today().strftime("%Y-%m-%d")
MONTH_YEAR = date.today().strftime("%B %Y")
OUTPUT_DIR = PROJECT_ROOT / "output"


def run_market_data():
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / f"{DATE}_market_data.json"
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "fetch_market_data.py"),
         "--output", str(out)],
        check=True,
    )
    return json.loads(out.read_text())


def research_and_synthesize(market_data: dict) -> dict:
    client = anthropic.Anthropic()

    portfolio = json.loads((PROJECT_ROOT / "resources" / "portfolio_config.json").read_text())
    holdings = portfolio["club_holdings"]    # MSTR, NFLX, NVDA, VOO
    watchlist = portfolio["watchlist"]        # MSFT, META, QQQ, DIA
    schema = (PROJECT_ROOT / "scripts" / "test_report_data.json").read_text()

    ticker_list = ", ".join(holdings + watchlist)
    cc_tickers  = ", ".join(holdings)

    prompt = f"""Today is {DATE} ({MONTH_YEAR}). Generate the complete FI Community Weekly Intelligence Report.

## Market data (live, already fetched via yfinance):
{json.dumps(market_data, indent=2)}

## Research tasks — use web_search for each:
1. "major business economic news this week {MONTH_YEAR}" → top 3 stories (Reuters, WSJ, Bloomberg, CNBC)
2. "stock market weekly recap {DATE[:7]}" → market narrative, key sector drivers
3. "Black investment club strategies 2026 HBCU finance club" → 2–3 clubs with specific strategies
4. "BetterInvesting NAIC investment club top strategies tools" → frameworks & templates
5. "best passive income opportunities {MONTH_YEAR}" → 3–4 opportunities with concrete return figures
6. "Federal Reserve interest rate decision {MONTH_YEAR}" + "CPI inflation news this week" → macro impact
7. "financial content creator growth 2026 Black finance Instagram TikTok" → 2–3 growth tactics
8. For EACH of {ticker_list}: "[TICKER] stock news analysis {MONTH_YEAR}" → key news, analyst sentiment, price levels, earnings dates
9. For EACH of {cc_tickers}: "[TICKER] covered call implied volatility options {MONTH_YEAR}" → IV level (low/normal/elevated), upcoming earnings dates/catalysts, range-bound vs trending

## Synthesis rules:
- Holdings recommendation must be exactly: BUY, HOLD, or SELL
- key_insights: exactly 3 bullets, each ≤15 words, action-oriented
- covered_calls.plays[].viable = false if any earnings date is within 3 weeks of {DATE}
- Covered call strike: 3–8% OTM (3–5% if range-bound/low-IV; 5–8% if trending/high-IV)
- DTE target: 25–45 days
- annualized_yield_pct = (estimated_premium / current_price) * (365 / days_to_expiry) * 100
- max_profit_per_contract = ((recommended_strike - current_price) + estimated_premium) * 100
- breakeven_price = current_price - estimated_premium
- NEVER recommend selling covered calls within 3 weeks of earnings

## Schema to follow exactly:
{schema}

Replace ALL placeholder/example values with real, researched data for {DATE}.

Return ONLY the JSON object — no markdown code fences, no explanation, no preamble."""

    messages = [{"role": "user", "content": prompt}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=16000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    text = block.text.strip()
                    text = re.sub(r"^```(?:json)?\s*", "", text)
                    text = re.sub(r"\s*```$", "", text.strip())
                    return json.loads(text.strip())
            raise ValueError("No text block in final response")

        # Handle tool_use round (built-in web_search is server-executed; acknowledge and continue)
        messages.append({"role": "assistant", "content": response.content})
        tool_results = [
            {"type": "tool_result", "tool_use_id": blk.id, "content": ""}
            for blk in response.content
            if blk.type == "tool_use"
        ]
        if not tool_results:
            raise ValueError(f"Unexpected stop_reason with no tool_use: {response.stop_reason}")
        messages.append({"role": "user", "content": tool_results})


def generate_pdf(report_data: dict) -> Path:
    data_path = OUTPUT_DIR / f"{DATE}_report_data.json"
    pdf_path  = OUTPUT_DIR / f"{DATE}_weekly-report.pdf"

    data_path.write_text(json.dumps(report_data, indent=2))

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_pdf.py"),
         "--data",   str(data_path),
         "--brand",  str(PROJECT_ROOT / "resources" / "brand_config.json"),
         "--output", str(pdf_path)],
        check=True,
    )
    return pdf_path


def main():
    print(f"=== FI Community Weekly Report — {DATE} ===")

    print("[1/3] Fetching market data...")
    market_data = run_market_data()
    print(f"      Holdings: {len(market_data.get('holdings', []))}, Watchlist: {len(market_data.get('watchlist', []))}")

    print("[2/3] Researching and synthesizing with Claude (web search enabled)...")
    report_data = research_and_synthesize(market_data)
    sections = list(report_data.get("sections", {}).keys())
    print(f"      Sections: {', '.join(sections)}")

    print("[3/3] Generating PDF...")
    pdf_path = generate_pdf(report_data)
    size_kb = round(pdf_path.stat().st_size / 1024)
    print(f"      SUCCESS: {pdf_path.name} ({size_kb} KB)")
    print(f"=== Report complete ===")


if __name__ == "__main__":
    main()

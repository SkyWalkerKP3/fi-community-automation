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
import httpx
import time

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


SYSTEM_PERSONA = """You are an expert investor and financial advisor with decades of experience advising Fortune 50 companies. You have excelled across multiple advanced investment strategies including options (covered calls, spreads, LEAPS), futures, equity analysis, and portfolio risk management. You understand both institutional and retail investment perspectives and communicate complex financial concepts in a clear, actionable way suited to an investment club audience. Every recommendation you make is grounded in current market data, recent news, and the club's specific holdings, cost basis, and risk profile."""


def load_holdings_lots() -> dict:
    lots_path = PROJECT_ROOT / "resources" / "holdings_lots.json"
    if lots_path.exists():
        return json.loads(lots_path.read_text())
    return {}


def research_and_synthesize(market_data: dict) -> dict:
    client = anthropic.Anthropic(timeout=httpx.Timeout(600.0, connect=10.0))

    portfolio = json.loads((PROJECT_ROOT / "resources" / "portfolio_config.json").read_text())
    holdings = portfolio["club_holdings"]    # MSTR, NFLX, NVDA, VOO
    watchlist = portfolio["watchlist"]        # MSFT, META, QQQ, DIA
    schema = (PROJECT_ROOT / "scripts" / "test_report_data.json").read_text()
    lots = load_holdings_lots()

    ticker_list = ", ".join(holdings + watchlist)
    cc_tickers  = ", ".join(holdings)

    lots_context = ""
    if lots:
        lots_context = f"\n## Club's actual position data (cost basis & lots):\n{json.dumps(lots, indent=2)}\n\nUse cost basis when evaluating unrealized P/L, covered call strikes vs. breakeven, and BUY/HOLD/SELL recommendations.\n"

    prompt = f"""Today is {DATE} ({MONTH_YEAR}). Generate the complete FI Community Weekly Intelligence Report.
{lots_context}
## Market data (live, already fetched via yfinance):
{json.dumps(market_data, indent=2)}

## Research tasks — use web_search for ALL of the following:

### MACROECONOMIC & MARKET
1. "major business economic news this week {MONTH_YEAR}" → top 3 stories (Reuters, WSJ, Bloomberg, CNBC)
2. "stock market weekly recap {DATE[:7]}" → market narrative, sector rotation, key drivers
3. "Federal Reserve interest rate CPI inflation jobs report {MONTH_YEAR}" → Fed stance, inflation trajectory, employment data; note short-term equity impact AND long-term rate environment outlook

### POLITICAL, GEOPOLITICAL & SOCIOECONOMIC
4. "US government policy legislation economic market impact {MONTH_YEAR}" → executive actions, congressional bills, regulatory changes; identify sector winners/losers short-term and structural shifts long-term
5. "geopolitical risk trade tariffs supply chain global markets {MONTH_YEAR}" → trade tensions, sanctions, global conflicts affecting markets; flight-to-safety moves short-term, supply chain reshoring trends long-term
6. "Black investors wealth gap retail investor socioeconomic trends consumer spending {MONTH_YEAR}" → demographic wealth-building patterns, consumer behavior shifts; which sectors benefit from rising Black wealth and Gen Z investing long-term
7. "technology AI regulation policy crypto Bitcoin legislation {MONTH_YEAR}" → any regulation affecting MSTR/Bitcoin, NVDA/AI, NFLX/streaming; flag caps on growth or buying opportunities

### INVESTMENT CLUB & OPPORTUNITIES
8. "Black investment club HBCU finance club strategies 2026" → 2–3 clubs with specific strategies and results
9. "BetterInvesting NAIC investment club strategies tools" → frameworks and templates
10. "best passive income side hustle opportunities {MONTH_YEAR}" → 3–4 opportunities with concrete return figures
11. "financial content creator growth Black finance Instagram TikTok 2026" → 2–3 growth tactics with expected results

### COMMUNITY BUILDING
12. "Atlanta Black entrepreneurship finance real estate community events {MONTH_YEAR}" + "Atlanta Black business networking investing events {MONTH_YEAR}" + "Invest Atlanta SCORE Atlanta Black chamber events {MONTH_YEAR}" → 4–6 upcoming events in Atlanta covering community building, real estate, finance/banking, and entrepreneurship. For each event: name, date, time, venue, cost, 1–2 sentence description, why FI Community should attend (networking value, partner potential, member recruitment). Flag events within 2 weeks as time_sensitive.

### PER-TICKER DEEP RESEARCH
13. For EACH of {ticker_list}:
    - "[TICKER] stock fundamental technical analysis {MONTH_YEAR}" → earnings growth, revenue, P/E, support/resistance, moving averages, RSI, volume
    - "[TICKER] analyst price target rating {MONTH_YEAR}" → short-term (3-month) and long-term (12-month) price targets
    - How do current political/macro/regulatory developments affect THIS company specifically?
14. For EACH of {cc_tickers}: "[TICKER] options implied volatility covered call {MONTH_YEAR}" → IV level (low/normal/elevated), earnings dates, catalysts, range-bound vs trending

## Synthesis rules:

### RECOMMENDATION FORMAT (apply to every holding):
Each holding must have ALL of the following:
- `recommendation`: BUY, HOLD, or SELL
- `short_term_strategy`: specific action for 0–8 weeks — what to do NOW based on technicals, near-term catalysts, and this week's news. Include price targets or entry/exit levels.
- `long_term_strategy`: thesis for 6–24 months — fundamentals, how political/regulatory/socioeconomic trends support or threaten the position, whether to accumulate or reduce over time.
- `rationale`: 2–3 sentences connecting this week's political, macro, and news context to why both strategies make sense RIGHT NOW.
- `cost_basis_note`: compare current price to the club's avg cost basis — note if the position is profitable, underwater, or near breakeven, and how that affects the recommended action.

### POLITICAL/SOCIOECONOMIC INTEGRATION:
- Weave political, geopolitical, and socioeconomic context INTO every recommendation — not as a separate section
- Every BUY/SELL/HOLD must reference at least one macro or political factor driving it
- The week_narrative must describe the political and macro environment, not just price moves

### COVERED CALLS:
- viable = false if earnings within 3 weeks of {DATE}
- Strike: 3–8% OTM (3–5% range-bound/low-IV; 5–8% trending/high-IV)
- DTE: 25–45 days
- annualized_yield_pct = (estimated_premium / current_price) * (365 / days_to_expiry) * 100
- max_profit_per_contract = ((recommended_strike - current_price) + estimated_premium) * 100
- breakeven_price = current_price - estimated_premium
- NEVER recommend covered calls within 3 weeks of earnings
- Define every options term the first time it appears: strike price, premium, DTE (Days to Expiration), OTM (Out of the Money), IV (Implied Volatility), annualized yield

### PLAIN LANGUAGE & ACCESSIBILITY (apply throughout every section):
- Write for a mixed audience: assume some readers are brand-new investors who have never read a financial report
- Spell out every acronym on first use with a brief plain-language definition in parentheses. Examples:
    • "P/E ratio (Price-to-Earnings — how much investors pay per $1 of company profit; lower = cheaper)"
    • "RSI (Relative Strength Index — a momentum gauge from 0–100; above 70 suggests overbought, below 30 suggests oversold)"
    • "CPI (Consumer Price Index — the government's main measure of inflation; how much everyday goods cost)"
    • "FOMC (Federal Open Market Committee — the Fed's rate-setting body)"
    • "DCA (Dollar-Cost Averaging — investing a fixed amount on a regular schedule regardless of price)"
- For every Federal Reserve / interest rate reference, add one sentence explaining the real-world effect: what rising or falling rates mean for borrowing, stock valuations, and our specific holdings
- For every political or policy development, spell out the cause-and-effect chain: [What happened] → [Why markets care] → [How it affects our portfolio]
- For every socioeconomic trend (wealth gap, consumer spending, demographic shifts), explain why it matters to a retail investor and which of our holdings benefit or face risk
- Avoid standalone jargon sentences — pair every technical term with a plain-language equivalent on the same line
- The week_narrative must open with 1–2 sentences a non-investor could read and immediately understand what happened this week and why it matters to them personally

### GENERAL:
- key_insights: exactly 3 bullets, each ≤15 words, action-oriented
- Every opportunity must have a concrete how_to_start
- Every content angle must include a hook sentence and platform

## Schema to follow exactly:
{schema}

Replace ALL placeholder/example values with real, researched data for {DATE}.
Return ONLY the JSON object — no markdown code fences, no explanation, no preamble."""

    messages = [{"role": "user", "content": prompt}]
    max_retries = 3

    for attempt in range(max_retries):
        try:
            while True:
                with client.messages.stream(
                    model="claude-opus-4-8",
                    max_tokens=32000,
                    system=SYSTEM_PERSONA,
                    tools=[{"type": "web_search_20260209", "name": "web_search"}],
                    messages=messages,
                ) as stream:
                    response = stream.get_final_message()

                if response.stop_reason == "end_turn":
                    # Collect all text blocks — JSON may be inside a code fence mid-block
                    text_blocks = [b.text.strip() for b in response.content if hasattr(b, "text") and b.text and b.text.strip()]
                    full_text = "\n".join(text_blocks)
                    (OUTPUT_DIR / f"{DATE}_raw_response.txt").write_text(full_text, encoding="utf-8")
                    # Strip <cite index="..."> tags injected by web search — their attribute
                    # quotes break JSON parsing when embedded inside JSON string values
                    full_text = re.sub(r'</?cite[^>]*>', '', full_text)
                    # Strategy 1: extract from ```json ... ``` fence anywhere in the response
                    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", full_text, re.DOTALL)
                    if fence_match:
                        return json.loads(fence_match.group(1))
                    # Strategy 2: find first { and parse from there, ignoring trailing text
                    brace_pos = full_text.find("{")
                    if brace_pos != -1:
                        candidate = full_text[brace_pos:]
                        obj, _ = json.JSONDecoder().raw_decode(candidate)
                        return obj
                    raise ValueError(f"No JSON found in {len(text_blocks)} text block(s)")

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

        except (httpx.ReadError, httpx.RemoteProtocolError, anthropic.APIConnectionError) as e:
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"      Connection dropped ({e.__class__.__name__}), retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                messages = [{"role": "user", "content": prompt}]  # reset to fresh start
                time.sleep(wait)
            else:
                raise


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

# FI Community — Weekly Intelligence Report Workflow

**Trigger:** Runs every Monday at 7:00 AM (scheduled agent), or manually: "Generate this week's FI Community report"

---

## Before You Begin

- Confirm today's date (used for all output filenames as `YYYY-MM-DD`)
- All paths are relative to the project root: `c:\Users\Kai\Documents\AI Automation\`
- Brand config: `resources/brand_config.json`
- Portfolio config: `resources/portfolio_config.json`

---

## Step 1 — Fetch Market Data

Run the market data script:
```
python scripts/fetch_market_data.py --output output/DATE_market_data.json
```

Wait for confirmation that the file was created. If it fails, check that `yfinance` is installed (`pip install yfinance`) and try again. Do not proceed until this file exists.

---

## Step 2 — Research (8 Web Searches)

Run these searches in order. For each, extract the 3 most relevant findings and note the source.

1. **Business & economic news** — Search: `major business news this week [MONTH YEAR]`
   - Target: Reuters, WSJ, Bloomberg, CNBC
   - Capture: top 3 stories with 1-sentence summary each

2. **Stock market week-in-review** — Search: `stock market weekly recap [DATE RANGE]`
   - Capture: market narrative, key drivers up/down, sector rotation notes

3. **Black investment clubs & HBCU finance clubs** — Search: `Black investment club strategies 2025 2026` + `HBCU investment club best practices`
   - Capture: 2–3 specific clubs with strategies, tools they use, standout results

4. **BetterInvesting / NAIC network** — Search: `BetterInvesting NAIC investment club top strategies tools`
   - Capture: specific frameworks, templates, or tools recommended by NAIC

5. **Side hustle & passive income opportunities** — Search: `best passive income opportunities [MONTH YEAR]` + `side income ideas this week`
   - Capture: 3–4 specific opportunities with concrete return figures

6. **Macro / Fed / rates news** — Search: `Federal Reserve interest rate decision [MONTH YEAR]` + `inflation CPI news this week`
   - Capture: what happened, what it means for savers and investors, time-sensitive opportunities

7. **Financial content creator growth** — Search: `financial literacy content creator growth strategy 2026` + `Black finance creator Instagram TikTok growth`
   - Capture: 2–3 specific tactics with expected results

8. **Per-ticker analysis** — For each ticker in `resources/portfolio_config.json` (club_holdings + watchlist):
   - Search: `[TICKER] stock analysis this week [MONTH YEAR]`
   - Capture: key news, analyst sentiment, price levels to watch

---

## Step 3 — Synthesize Into 4 Sections

Using the market data from Step 1 and research from Step 2, construct the full report data. Follow this schema exactly.

### Rules for synthesis:
- `key_insights`: exactly 3 bullets, each ≤15 words, action-oriented
- Every opportunity must have a concrete `how_to_start` — no vague suggestions
- Every content angle must include a `hook` sentence and `platform`
- All recommendations must be tied to specific events from this week's research
- Holdings `recommendation` must be one of: `BUY`, `HOLD`, or `SELL`
- Holdings `direction` must be one of: `up` or `down`

### Section 1 — Portfolio (`sections.portfolio`)
- Pull `week_change_pct`, `current_price`, and `direction` from `output/DATE_market_data.json`
- Write a 2–3 sentence `week_narrative` summarizing the market environment
- For each holding: assign recommendation + rationale tied to this week's news
- For each watchlist ticker: explain why it's being watched and what to look for

### Section 2 — Benchmarking (`sections.benchmarking`)
- List 2–3 clubs researched with strategy, tool, and key takeaway
- Convert research into 2–3 `strategies_to_adopt` with difficulty (Low/Medium/High), impact (Low/Medium/High), and 3 concrete steps each

### Section 3 — Side Income (`sections.side_income`)
- List 3–4 specific opportunities this week with type, effort, return, and how_to_start
- List 2 `news_hooks`: the triggering event → the opportunity → the specific action
- Flag any `time_sensitive: true` opportunities (act this week or miss it)

### Section 4 — Content Strategy (`sections.content_strategy`)
- Write 3 content angles tied to this week's news events
- Include 2–3 audience growth moves with effort level and expected reach
- Include 2 monetization ideas tied to current market conditions

---

## Step 4 — Write report_data.json

Construct the complete JSON object following the schema in `scripts/test_report_data.json` as reference. Merge market data from Step 1 with synthesized content from Step 3.

Save to: `output/DATE_report_data.json`

---

## Step 5 — Generate PDF

Run:
```
python scripts/generate_pdf.py \
  --data output/DATE_report_data.json \
  --brand resources/brand_config.json \
  --output output/DATE_weekly-report.pdf
```

If it fails with a WeasyPrint error, add `--debug` flag to get the HTML output, inspect it, and retry. If GTK is not installed, set `"pdf_engine": "xhtml2pdf"` in `resources/brand_config.json` and rerun.

---

## Step 6 — Verify & Report

1. Confirm `output/DATE_weekly-report.pdf` exists
2. Check file size is > 50 KB
3. Report to user: "Weekly report generated: `output/DATE_weekly-report.pdf` (X KB)"

If the file is missing or too small, run with `--debug` and check the HTML output.

---

## Output Files (all saved to `output/`)

| File | Contents |
|---|---|
| `DATE_market_data.json` | Raw market data from yfinance |
| `DATE_report_data.json` | Structured report content (audit trail) |
| `DATE_weekly-report.pdf` | Final branded PDF — the deliverable |

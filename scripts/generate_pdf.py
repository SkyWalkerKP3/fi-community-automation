"""
FI Community Weekly Intelligence Report — PDF Generator
Usage:
  python scripts/generate_pdf.py \
    --data output/2026-04-28_report_data.json \
    --brand resources/brand_config.json \
    --output output/2026-04-28_weekly-report.pdf

Fallback (no GTK): set "pdf_engine": "xhtml2pdf" in brand_config.json
"""

import argparse
import base64
import json
import sys
from pathlib import Path

from jinja2 import Template

ROOT = Path(__file__).parent.parent


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def logo_as_data_uri(logo_path: Path) -> str:
    if not logo_path.exists():
        return ""
    ext = logo_path.suffix.lower().lstrip(".")
    mime = "image/png" if ext == "png" else f"image/{ext}"
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{encoded}"


def arrow(direction):
    return "▲" if direction == "up" else "▼"


def sign_color(pct, brand):
    if pct is None:
        return brand["colors"]["text_muted"]
    return brand["colors"]["buy_green"] if pct >= 0 else brand["colors"]["sell_red"]


def fmt_pct(val):
    if val is None:
        return "—"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.2f}%"


# ── HTML Template ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<style>
  @page {
    size: letter;
    margin: 0;
    @bottom-center {
      content: element(page-footer);
    }
  }

  :root {
    --bg-dark:      {{ c.bg_dark }};
    --bg-surface:   {{ c.bg_surface }};
    --bg-deep:      {{ c.bg_deep }};
    --accent:       {{ c.accent }};
    --accent-dim:   {{ c.accent_dim }};
    --text-primary: {{ c.text_primary }};
    --text-body:    {{ c.text_body }};
    --text-muted:   {{ c.text_muted }};
    --text-light:   {{ c.text_on_light }};
    --bg-light:     {{ c.bg_light }};
    --buy:          {{ c.buy_green }};
    --sell:         {{ c.sell_red }};
    --hold:         {{ c.accent }};
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: Helvetica, Arial, sans-serif;
    background: var(--bg-dark);
    color: var(--text-body);
    font-size: 11pt;
    line-height: 1.55;
  }

  /* ── Running footer ── */
  #page-footer {
    position: running(page-footer);
    width: 100%;
    height: 30px;
    background: var(--bg-deep);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  #page-footer span {
    color: var(--accent);
    font-size: 7.5pt;
    font-weight: bold;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  /* ── Page breaks ── */
  .page { page-break-after: always; }
  .page:last-child { page-break-after: avoid; }

  /* ── COVER PAGE ── */
  .cover {
    background: var(--bg-dark);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0 48px 48px;
  }
  .cover-hero {
    width: 100%;
    background: var(--bg-dark);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 64px 48px 40px;
    border-bottom: 3px solid var(--accent);
  }
  .cover-logo {
    height: 90px;
    margin-bottom: 24px;
  }
  .cover-title {
    font-size: 28pt;
    font-weight: bold;
    color: var(--accent);
    text-align: center;
    letter-spacing: 0.04em;
    line-height: 1.2;
    margin-bottom: 10px;
  }
  .cover-subtitle {
    font-size: 11pt;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 4px;
  }
  .cover-date {
    font-size: 10pt;
    color: var(--text-muted);
    text-align: center;
    margin-top: 6px;
  }
  .cover-rule {
    width: 60px;
    height: 3px;
    background: var(--accent);
    margin: 16px auto;
    border-radius: 2px;
  }

  .cover-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-top: 40px;
    width: 100%;
  }
  .cover-card {
    flex: 1 1 calc(50% - 10px);
    background: var(--bg-surface);
    border-radius: 10px;
    border-top: 3px solid var(--accent);
    padding: 22px 24px;
    min-width: 200px;
  }
  .cover-card-title {
    font-size: 12pt;
    font-weight: bold;
    color: var(--accent);
    margin-bottom: 10px;
    letter-spacing: 0.03em;
  }
  .cover-card-bullet {
    font-size: 9.5pt;
    color: var(--text-body);
    margin-bottom: 6px;
    padding-left: 14px;
    position: relative;
  }
  .cover-card-bullet::before {
    content: "›";
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: bold;
  }

  /* ── SECTION PAGES ── */
  .section-page {
    background: var(--bg-dark);
    min-height: 100vh;
    padding: 0;
  }

  /* Page header (every section page) */
  .page-header {
    background: var(--bg-surface);
    height: 48px;
    display: flex;
    align-items: center;
    padding: 0 36px;
    border-bottom: 2px solid var(--bg-deep);
  }
  .page-header-logo {
    height: 22px;
  }
  .page-header-title {
    flex: 1;
    text-align: center;
    font-size: 8.5pt;
    color: var(--text-muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: bold;
  }
  .page-header-num {
    font-size: 8.5pt;
    color: var(--text-muted);
    letter-spacing: 0.06em;
  }

  /* Section hero band */
  .section-hero {
    background: var(--bg-surface);
    padding: 24px 36px 20px;
    border-left: 5px solid var(--accent);
    margin-bottom: 24px;
  }
  .section-hero-title {
    font-size: 22pt;
    font-weight: bold;
    color: var(--accent);
    line-height: 1.1;
    margin-bottom: 4px;
  }
  .section-hero-sub {
    font-size: 10pt;
    color: var(--text-muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  /* Content wrapper */
  .section-content {
    padding: 0 36px 36px;
  }

  /* ── Market Summary Band ── */
  .market-band {
    background: var(--bg-deep);
    border-radius: 10px;
    display: flex;
    gap: 2px;
    margin-bottom: 22px;
    overflow: hidden;
  }
  .market-stat {
    flex: 1;
    padding: 18px 16px;
    text-align: center;
    background: var(--bg-surface);
  }
  .market-stat:first-child { border-radius: 10px 0 0 10px; }
  .market-stat:last-child  { border-radius: 0 10px 10px 0; }
  .market-stat-num {
    font-size: 22pt;
    font-weight: bold;
    line-height: 1;
    margin-bottom: 4px;
  }
  .market-stat-label {
    font-size: 7.5pt;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  .up   { color: {{ c.buy_green }}; }
  .down { color: {{ c.sell_red }}; }
  .neutral { color: var(--text-muted); }

  /* ── Holdings Table ── */
  .holdings-table {
    width: 100%;
    border-collapse: collapse;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 22px;
    font-size: 9.5pt;
  }
  .holdings-table th {
    background: var(--bg-deep);
    color: var(--text-primary);
    font-size: 8pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 11px 14px;
    text-align: left;
  }
  .holdings-table td {
    padding: 11px 14px;
    border-bottom: 1px solid var(--bg-deep);
    vertical-align: middle;
  }
  .holdings-table tr:nth-child(even) td { background: var(--bg-surface); }
  .holdings-table tr:nth-child(odd) td  { background: var(--bg-dark); }
  .holdings-table .ticker-cell {
    font-weight: bold;
    color: var(--text-primary);
    font-size: 10pt;
  }
  .holdings-table .name-cell {
    color: var(--text-muted);
    font-size: 8.5pt;
  }

  /* ── Badges ── */
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 7.5pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .badge-buy  { background: {{ c.buy_green }}; color: #fff; }
  .badge-hold { background: {{ c.accent }}; color: {{ c.bg_dark }}; }
  .badge-sell { background: {{ c.sell_red }}; color: #fff; }

  /* ── Cards ── */
  .card {
    background: var(--bg-surface);
    border-radius: 10px;
    border-top: 2px solid var(--accent);
    padding: 18px 20px;
    margin-bottom: 16px;
  }
  .card-title {
    font-size: 11pt;
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: 6px;
  }
  .card-sub {
    font-size: 8.5pt;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 10px;
  }
  .card-body {
    font-size: 9.5pt;
    color: var(--text-body);
    line-height: 1.6;
  }

  /* Left-bar accent card (opportunities) */
  .card-accent {
    background: var(--bg-surface);
    border-radius: 10px;
    border-left: 4px solid var(--accent);
    padding: 18px 20px;
    margin-bottom: 16px;
  }

  /* ── Grid ── */
  .grid-2 {
    display: flex;
    gap: 18px;
    margin-bottom: 16px;
  }
  .grid-2 > * { flex: 1; }

  /* ── Key Insights Box ── */
  .insights-box {
    background: var(--bg-deep);
    border-radius: 10px;
    padding: 18px 20px;
    margin-top: 20px;
  }
  .insights-title {
    font-size: 8.5pt;
    font-weight: bold;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
  }
  .insight-item {
    font-size: 9.5pt;
    color: var(--text-body);
    padding-left: 18px;
    position: relative;
    margin-bottom: 8px;
    line-height: 1.5;
  }
  .insight-item::before {
    content: "›";
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: bold;
    font-size: 11pt;
    line-height: 1.2;
  }

  /* ── Pill tags ── */
  .tag {
    display: inline-block;
    background: var(--bg-deep);
    color: var(--text-body);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 7pt;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-right: 4px;
    margin-bottom: 4px;
  }

  /* ── Difficulty dots ── */
  .dot {
    display: inline-block;
    width: 9px; height: 9px;
    border-radius: 50%;
    margin-right: 3px;
    vertical-align: middle;
  }
  .dot-low    { background: {{ c.buy_green }}; }
  .dot-medium { background: {{ c.accent }}; }
  .dot-high   { background: {{ c.sell_red }}; }

  /* ── Watchlist cards ── */
  .watchlist-grid {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }
  .watchlist-card {
    flex: 1;
    min-width: 160px;
    background: var(--bg-surface);
    border-radius: 8px;
    border-left: 3px solid var(--accent-dim);
    padding: 14px 16px;
  }
  .watchlist-ticker {
    font-size: 13pt;
    font-weight: bold;
    color: var(--text-primary);
  }
  .watchlist-name {
    font-size: 7.5pt;
    color: var(--text-muted);
    margin-bottom: 8px;
  }
  .watchlist-body {
    font-size: 8.5pt;
    color: var(--text-body);
    line-height: 1.5;
  }

  /* ── Narrative text ── */
  .narrative {
    font-size: 9.5pt;
    color: var(--text-body);
    line-height: 1.65;
    margin-bottom: 18px;
    padding: 16px 20px;
    background: var(--bg-surface);
    border-radius: 8px;
    border-left: 3px solid var(--bg-deep);
  }

  /* ── Step list ── */
  .step-list {
    list-style: none;
    padding: 0;
    margin: 8px 0 0;
  }
  .step-list li {
    font-size: 9pt;
    color: var(--text-body);
    padding: 5px 0 5px 22px;
    position: relative;
    border-bottom: 1px solid var(--bg-deep);
    line-height: 1.5;
  }
  .step-list li:last-child { border-bottom: none; }
  .step-list li::before {
    content: counter(step);
    counter-increment: step;
    position: absolute;
    left: 0;
    width: 16px;
    height: 16px;
    background: var(--accent);
    color: var(--bg-dark);
    border-radius: 50%;
    font-size: 7pt;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    top: 6px;
  }
  .step-list { counter-reset: step; }

  /* ── Section label ── */
  .section-label {
    font-size: 8pt;
    font-weight: bold;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
    padding-left: 14px;
    border-left: 3px solid var(--accent);
  }

  /* ── News hook ── */
  .hook-card {
    background: var(--bg-deep);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
  }
  .hook-event {
    font-size: 8.5pt;
    color: var(--accent);
    font-weight: bold;
    margin-bottom: 4px;
  }
  .hook-opp {
    font-size: 9pt;
    color: var(--text-body);
    margin-bottom: 4px;
  }
  .hook-action {
    font-size: 8.5pt;
    color: var(--text-muted);
    font-style: italic;
  }

  /* ── Covered Call section ── */
  .cc-play {
    background: var(--bg-surface);
    border-radius: 10px;
    border-left: 4px solid var(--accent);
    padding: 16px 18px;
    margin-bottom: 14px;
  }
  .cc-play.cc-skip {
    border-left-color: {{ c.sell_red }};
    opacity: 0.75;
  }
  .cc-play-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 10px;
  }
  .cc-ticker {
    font-size: 16pt;
    font-weight: bold;
    color: var(--text-primary);
    min-width: 60px;
  }
  .cc-badge-sell {
    background: {{ c.buy_green }};
    color: #fff;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 7.5pt;
    font-weight: bold;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .cc-badge-skip {
    background: {{ c.sell_red }};
    color: #fff;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 7.5pt;
    font-weight: bold;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .cc-viability {
    flex: 1;
    font-size: 8.5pt;
    color: var(--text-body);
    line-height: 1.5;
  }
  .cc-stats {
    width: 100%;
    margin-bottom: 10px;
  }
  .cc-stats table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 6px 0;
  }
  .cc-stats td {
    background: var(--bg-deep);
    border-radius: 6px;
    padding: 8px 6px;
    text-align: center;
    vertical-align: middle;
    width: 16%;
  }
  .cc-stat {
    background: var(--bg-deep);
    border-radius: 6px;
    padding: 8px 12px;
    text-align: center;
    display: inline-block;
    width: 15%;
    margin-right: 1%;
    vertical-align: top;
  }
  .cc-stat-val {
    font-size: 13pt;
    font-weight: bold;
    color: var(--accent);
    line-height: 1.1;
  }
  .cc-stat-lbl {
    font-size: 7pt;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-top: 2px;
  }
  .cc-detail {
    font-size: 8.5pt;
    color: var(--text-body);
    line-height: 1.55;
    padding-top: 8px;
    border-top: 1px solid var(--bg-deep);
  }
  .cc-skip-body {
    font-size: 8.5pt;
    color: var(--text-muted);
    line-height: 1.55;
  }
  .cc-skip-watch {
    font-size: 8.5pt;
    color: var(--accent);
    margin-top: 6px;
    font-style: italic;
  }
  .cc-catalyst-warning {
    background: #3a1a1a;
    border: 1px solid {{ c.sell_red }};
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 8pt;
    color: {{ c.sell_red }};
    font-weight: bold;
    margin-top: 6px;
  }
  .cc-primer {
    background: var(--bg-deep);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 20px;
    font-size: 9pt;
    color: var(--text-body);
    line-height: 1.6;
    border-left: 3px solid var(--accent-dim);
  }
  .cc-primer-label {
    font-size: 7.5pt;
    font-weight: bold;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
  }
  .cover-cards-5 {
    margin-top: 32px;
    width: 100%;
  }
  .cover-cards-5 .cover-card {
    display: inline-block;
    width: 48%;
    margin-right: 2%;
    margin-bottom: 14px;
    vertical-align: top;
  }
  .cover-cards-5 .cover-card-full {
    display: block;
    width: 99%;
  }

</style>
</head>
<body>

<!-- ════════════════════════════════════════════════
     PAGE 1 — COVER
════════════════════════════════════════════════ -->
<div class="page cover">
  <div class="cover-hero">
    {% if logo_uri %}
    <img class="cover-logo" src="{{ logo_uri }}" alt="FI Community logo"/>
    {% endif %}
    <div class="cover-title">Weekly Intelligence Report</div>
    <div class="cover-rule"></div>
    <div class="cover-subtitle">{{ brand.brand_name }} &nbsp;·&nbsp; {{ brand.tagline }}</div>
    <div class="cover-date">{{ data.week_label }}</div>
  </div>

  <div class="cover-cards-5">
    <!-- Card 1: Portfolio -->
    <div class="cover-card">
      <div class="cover-card-title">📈 Investment Club Portfolio</div>
      {% for insight in data.sections.portfolio.key_insights[:2] %}
      <div class="cover-card-bullet">{{ insight }}</div>
      {% endfor %}
    </div>
    <!-- Card 2: Benchmarking -->
    <div class="cover-card">
      <div class="cover-card-title">🏆 Club Benchmarking</div>
      {% for insight in data.sections.benchmarking.key_insights[:2] %}
      <div class="cover-card-bullet">{{ insight }}</div>
      {% endfor %}
    </div>
    <!-- Card 3: Side Income -->
    <div class="cover-card">
      <div class="cover-card-title">💼 Side Income & Business Moves</div>
      {% for insight in data.sections.side_income.key_insights[:2] %}
      <div class="cover-card-bullet">{{ insight }}</div>
      {% endfor %}
    </div>
    <!-- Card 4: Content Strategy -->
    <div class="cover-card">
      <div class="cover-card-title">📣 Content & Brand Strategy</div>
      {% for insight in data.sections.content_strategy.key_insights[:2] %}
      <div class="cover-card-bullet">{{ insight }}</div>
      {% endfor %}
    </div>
    <!-- Card 5: Covered Calls — full width -->
    {% if data.sections.covered_calls is defined %}
    <div class="cover-card cover-card-full">
      <div class="cover-card-title">📊 Covered Call Strategy</div>
      {% for insight in data.sections.covered_calls.key_insights[:2] %}
      <div class="cover-card-bullet">{{ insight }}</div>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</div>

<!-- ════════════════════════════════════════════════
     PAGE 2 — INVESTMENT CLUB PORTFOLIO
════════════════════════════════════════════════ -->
{% set port = data.sections.portfolio %}
<div class="page section-page">
  <div class="page-header">
    {% if logo_light_uri %}
    <img class="page-header-logo" src="{{ logo_light_uri }}" alt="FI"/>
    {% endif %}
    <div class="page-header-title">{{ port.title }}</div>
    <div class="page-header-num">Page 2 of 6</div>
  </div>

  <div class="section-hero">
    <div class="section-hero-title">{{ port.title }}</div>
    <div class="section-hero-sub">{{ port.subtitle }}</div>
  </div>

  <div class="section-content">

    <!-- Market Summary Band -->
    {% set ms = port.market_summary %}
    <div class="market-band">
      <div class="market-stat">
        <div class="market-stat-num {{ 'up' if ms.sp500.direction == 'up' else 'down' }}">
          {{ arrow(ms.sp500.direction) }} {{ fmt_pct(ms.sp500.week_change_pct) }}
        </div>
        <div class="market-stat-label">S&amp;P 500</div>
      </div>
      <div class="market-stat">
        <div class="market-stat-num {{ 'up' if ms.nasdaq.direction == 'up' else 'down' }}">
          {{ arrow(ms.nasdaq.direction) }} {{ fmt_pct(ms.nasdaq.week_change_pct) }}
        </div>
        <div class="market-stat-label">Nasdaq</div>
      </div>
      <div class="market-stat">
        <div class="market-stat-num {{ 'up' if ms.dow.direction == 'up' else 'down' }}">
          {{ arrow(ms.dow.direction) }} {{ fmt_pct(ms.dow.week_change_pct) }}
        </div>
        <div class="market-stat-label">Dow Jones</div>
      </div>
    </div>

    <!-- Week Narrative -->
    <div class="narrative">{{ port.week_narrative }}</div>

    <!-- Holdings Table -->
    <div class="section-label">Club Holdings</div>
    <table class="holdings-table">
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Name</th>
          <th>Price</th>
          <th>Week Change</th>
          <th>Signal</th>
          <th>Rationale</th>
        </tr>
      </thead>
      <tbody>
        {% for h in port.holdings %}
        <tr>
          <td class="ticker-cell">{{ h.ticker }}</td>
          <td class="name-cell">{{ h.name }}</td>
          <td style="color: var(--text-primary); font-weight: bold;">${{ h.current_price }}</td>
          <td style="color: {{ sign_color(h.week_change_pct, brand) }}; font-weight: bold;">
            {{ arrow(h.direction) }} {{ fmt_pct(h.week_change_pct) }}
          </td>
          <td>
            {% if h.recommendation == 'BUY' %}
            <span class="badge badge-buy">BUY</span>
            {% elif h.recommendation == 'SELL' %}
            <span class="badge badge-sell">SELL</span>
            {% else %}
            <span class="badge badge-hold">HOLD</span>
            {% endif %}
          </td>
          <td style="font-size: 8.5pt; color: var(--text-body);">{{ h.rationale }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>

    <!-- Watchlist -->
    <div class="section-label">Watchlist</div>
    <div class="watchlist-grid">
      {% for w in port.watchlist %}
      <div class="watchlist-card">
        <div class="watchlist-ticker">
          {{ w.ticker }}
          <span style="font-size: 9pt; color: {{ sign_color(w.week_change_pct, brand) }}; font-weight: normal; margin-left: 8px;">
            {{ arrow(w.direction) }} {{ fmt_pct(w.week_change_pct) }}
          </span>
        </div>
        <div class="watchlist-name">{{ w.name }}</div>
        <div class="watchlist-body">{{ w.rationale }}</div>
      </div>
      {% endfor %}
    </div>

    <!-- Key Insights -->
    <div class="insights-box">
      <div class="insights-title">Key Insights This Week</div>
      {% for insight in port.key_insights %}
      <div class="insight-item">{{ insight }}</div>
      {% endfor %}
    </div>

  </div>
</div>

<!-- ════════════════════════════════════════════════
     PAGE 3 — CLUB BENCHMARKING
════════════════════════════════════════════════ -->
{% set bench = data.sections.benchmarking %}
<div class="page section-page">
  <div class="page-header">
    {% if logo_light_uri %}
    <img class="page-header-logo" src="{{ logo_light_uri }}" alt="FI"/>
    {% endif %}
    <div class="page-header-title">{{ bench.title }}</div>
    <div class="page-header-num">Page 3 of 6</div>
  </div>

  <div class="section-hero">
    <div class="section-hero-title">{{ bench.title }}</div>
    <div class="section-hero-sub">{{ bench.subtitle }}</div>
  </div>

  <div class="section-content">

    <div class="section-label">Clubs Researched This Week</div>
    {% for club in bench.clubs_researched %}
    <div class="card">
      <div class="card-title">{{ club.name }}</div>
      <div style="font-size: 9pt; color: var(--text-body); margin-bottom: 8px;">
        <strong style="color: var(--accent);">Strategy:</strong> {{ club.strategy }}
      </div>
      <div style="font-size: 9pt; color: var(--text-body); margin-bottom: 8px;">
        <strong style="color: var(--accent);">Tools:</strong> {{ club.tool }}
      </div>
      <div style="font-size: 9pt; color: var(--text-primary); background: var(--bg-deep); padding: 8px 12px; border-radius: 6px;">
        <strong>Takeaway:</strong> {{ club.takeaway }}
      </div>
    </div>
    {% endfor %}

    <div class="section-label" style="margin-top: 20px;">Strategies to Adopt</div>
    {% for strat in bench.strategies_to_adopt %}
    <div class="card-accent" style="margin-bottom: 16px;">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
        <div class="card-title" style="flex: 1;">{{ strat.strategy }}</div>
        <div style="text-align: right; font-size: 8pt; color: var(--text-muted);">
          Difficulty:&nbsp;
          <span class="dot dot-{{ strat.difficulty | lower }}"></span>
          {{ strat.difficulty }}&nbsp;&nbsp;
          Impact:&nbsp;
          <span class="dot dot-{{ strat.impact | lower }}"></span>
          {{ strat.impact }}
        </div>
      </div>
      <ol class="step-list">
        {% for step in strat.steps %}
        <li>{{ step }}</li>
        {% endfor %}
      </ol>
    </div>
    {% endfor %}

    <div class="insights-box">
      <div class="insights-title">Key Insights This Week</div>
      {% for insight in bench.key_insights %}
      <div class="insight-item">{{ insight }}</div>
      {% endfor %}
    </div>

  </div>
</div>

<!-- ════════════════════════════════════════════════
     PAGE 4 — SIDE INCOME & BUSINESS MOVES
════════════════════════════════════════════════ -->
{% set income = data.sections.side_income %}
<div class="page section-page">
  <div class="page-header">
    {% if logo_light_uri %}
    <img class="page-header-logo" src="{{ logo_light_uri }}" alt="FI"/>
    {% endif %}
    <div class="page-header-title">{{ income.title }}</div>
    <div class="page-header-num">Page 4 of 6</div>
  </div>

  <div class="section-hero">
    <div class="section-hero-title">{{ income.title }}</div>
    <div class="section-hero-sub">{{ income.subtitle }}</div>
  </div>

  <div class="section-content">

    <div class="section-label">Opportunities This Week</div>
    {% for opp in income.opportunities %}
    <div class="card-accent">
      <div style="display: flex; align-items: flex-start; gap: 16px; margin-bottom: 10px;">
        <div style="flex: 1;">
          <div class="card-title">{{ opp.name }}</div>
          <div style="margin-top: 4px;">
            <span class="tag">{{ opp.type }}</span>
            <span class="tag">Effort: {{ opp.effort }}</span>
            {% if opp.time_sensitive %}<span class="tag" style="background: {{ c.sell_red }}; color: #fff;">Time Sensitive</span>{% endif %}
          </div>
        </div>
        <div style="text-align: right; flex-shrink: 0;">
          <div style="font-size: 14pt; font-weight: bold; color: {{ c.buy_green }};">{{ opp.potential_return }}</div>
          <div style="font-size: 7.5pt; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.07em;">Potential Return</div>
        </div>
      </div>
      <div style="background: var(--bg-deep); border-radius: 6px; padding: 10px 14px; font-size: 9pt; color: var(--text-body); line-height: 1.6;">
        <strong style="color: var(--accent);">How to start:</strong> {{ opp.how_to_start }}
      </div>
    </div>
    {% endfor %}

    <div class="section-label" style="margin-top: 20px;">News Hooks → Action Items</div>
    {% for hook in income.news_hooks %}
    <div class="hook-card">
      <div class="hook-event">📰 {{ hook.event }}</div>
      <div class="hook-opp">{{ hook.opportunity }}</div>
      <div class="hook-action">Action: {{ hook.action }}</div>
    </div>
    {% endfor %}

    <div class="insights-box">
      <div class="insights-title">Key Insights This Week</div>
      {% for insight in income.key_insights %}
      <div class="insight-item">{{ insight }}</div>
      {% endfor %}
    </div>

  </div>
</div>

<!-- ════════════════════════════════════════════════
     PAGE 5 — CONTENT & BRAND STRATEGY
════════════════════════════════════════════════ -->
{% set content = data.sections.content_strategy %}
<div class="section-page">
  <div class="page-header">
    {% if logo_light_uri %}
    <img class="page-header-logo" src="{{ logo_light_uri }}" alt="FI"/>
    {% endif %}
    <div class="page-header-title">{{ content.title }}</div>
    <div class="page-header-num">Page 5 of 6</div>
  </div>

  <div class="section-hero">
    <div class="section-hero-title">{{ content.title }}</div>
    <div class="section-hero-sub">{{ content.subtitle }}</div>
  </div>

  <div class="section-content">

    <div class="section-label">Content Angles This Week</div>
    {% for angle in content.content_angles %}
    <div class="card">
      <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px;">
        <div style="flex: 1;">
          <div class="card-title">{{ angle.headline }}</div>
          <div style="margin-top: 4px;">
            {% for platform in angle.platform.split('+') %}
            <span class="tag">{{ platform.strip() }}</span>
            {% endfor %}
            <span class="tag">{{ angle.format }}</span>
          </div>
        </div>
      </div>
      <div style="background: var(--bg-deep); border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
        <div style="font-size: 8pt; color: var(--accent); font-weight: bold; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.07em;">Hook</div>
        <div style="font-size: 9pt; color: var(--text-body); font-style: italic; line-height: 1.6;">{{ angle.hook }}</div>
      </div>
      <div style="font-size: 8.5pt; color: var(--text-muted);">
        <strong style="color: var(--accent);">CTA:</strong> {{ angle.cta }}
      </div>
    </div>
    {% endfor %}

    <div class="grid-2" style="margin-top: 4px;">
      <!-- Audience Growth -->
      <div>
        <div class="section-label">Audience Growth Moves</div>
        {% for move in content.audience_growth_moves %}
        <div class="card-accent" style="margin-bottom: 12px;">
          <div class="card-title" style="font-size: 10pt;">{{ move.tactic }}</div>
          <div style="margin: 6px 0;">
            <span class="tag">{{ move.platform }}</span>
            <span class="tag">Effort: {{ move.effort }}</span>
          </div>
          <div style="font-size: 8.5pt; color: {{ c.buy_green }};">{{ move.expected_reach }}</div>
        </div>
        {% endfor %}
      </div>

      <!-- Monetization -->
      <div>
        <div class="section-label">Monetization Ideas</div>
        {% for idea in content.monetization_ideas %}
        <div class="card-accent" style="margin-bottom: 12px;">
          <div class="card-title" style="font-size: 10pt;">{{ idea.idea }}</div>
          <div style="margin: 6px 0;">
            <span class="tag">{{ idea.platform }}</span>
            <span class="tag" style="color: {{ c.buy_green }}; border: 1px solid {{ c.buy_green }};">{{ idea.revenue_model }}</span>
          </div>
          <div style="font-size: 8.5pt; color: var(--text-body); line-height: 1.5;">{{ idea.steps }}</div>
        </div>
        {% endfor %}
      </div>
    </div>

    <div class="insights-box">
      <div class="insights-title">Key Insights This Week</div>
      {% for insight in content.key_insights %}
      <div class="insight-item">{{ insight }}</div>
      {% endfor %}
    </div>

  </div>
</div>

<!-- ════════════════════════════════════════════════
     PAGE 6 — COVERED CALL STRATEGY
════════════════════════════════════════════════ -->
{% if data.sections.covered_calls is defined %}
{% set cc = data.sections.covered_calls %}
<div class="section-page">
  <div class="page-header">
    {% if logo_light_uri %}
    <img class="page-header-logo" src="{{ logo_light_uri }}" alt="FI"/>
    {% endif %}
    <div class="page-header-title">{{ cc.title }}</div>
    <div class="page-header-num">Page 6 of 6</div>
  </div>

  <div class="section-hero">
    <div class="section-hero-title">{{ cc.title }}</div>
    <div class="section-hero-sub">{{ cc.subtitle }}</div>
  </div>

  <div class="section-content">

    <!-- IV Context + Primer -->
    <div class="cc-primer">
      <div class="cc-primer-label">What Is a Covered Call?</div>
      {{ cc.covered_call_primer }}
    </div>

    {% if cc.market_iv_context %}
    <div class="narrative" style="margin-bottom: 18px;">
      <strong style="color: var(--accent);">This Week's IV Environment:</strong> {{ cc.market_iv_context }}
    </div>
    {% endif %}

    <div class="section-label">Plays This Week</div>

    {% for play in cc.plays %}
    <div class="cc-play {% if not play.viable %}cc-skip{% endif %}">
      <div class="cc-play-header">
        <div class="cc-ticker">{{ play.ticker }}</div>
        {% if play.viable %}
        <span class="cc-badge-sell">SELL CALL</span>
        {% else %}
        <span class="cc-badge-skip">SKIP</span>
        {% endif %}
        <div class="cc-viability">
          <strong style="color: var(--text-primary);">{{ play.name }}</strong>
          &nbsp;·&nbsp; ${{ play.current_price }}
          {% if play.viable and play.viability_reason %}
          <br/>{{ play.viability_reason }}
          {% endif %}
        </div>
      </div>

      {% if play.viable %}
      <!-- Stats row -->
      <div class="cc-stats">
        <table><tr>
          <td><div class="cc-stat-val">${{ play.recommended_strike }}</div><div class="cc-stat-lbl">Strike</div></td>
          <td><div class="cc-stat-val">{{ play.strike_pct_otm }}%</div><div class="cc-stat-lbl">OTM</div></td>
          <td><div class="cc-stat-val">${{ play.estimated_premium }}</div><div class="cc-stat-lbl">Premium/sh</div></td>
          <td><div class="cc-stat-val">{{ play.annualized_yield_pct }}%</div><div class="cc-stat-lbl">Ann. Yield</div></td>
          <td><div class="cc-stat-val">${{ play.max_profit_per_contract }}</div><div class="cc-stat-lbl">Max Profit</div></td>
          <td><div class="cc-stat-val">${{ play.breakeven_price }}</div><div class="cc-stat-lbl">Breakeven</div></td>
        </tr></table>
      </div>
      <div class="cc-detail">
        <strong style="color: var(--accent);">Expiry:</strong> {{ play.recommended_expiry }}
        &nbsp;·&nbsp; {{ play.days_to_expiry }} days
        &nbsp;·&nbsp; <strong style="color: var(--accent);">Timing:</strong> {{ play.timing }}
        {% if play.historical_win_rate %}
        <br/><strong style="color: var(--accent);">Historical:</strong> {{ play.historical_win_rate }}
        {% endif %}
        {% if play.upcoming_catalyst %}
        <div class="cc-catalyst-warning" style="margin-top: 8px;">
          ⚠ Catalyst: {{ play.upcoming_catalyst }}
        </div>
        {% endif %}
      </div>

      {% else %}
      <!-- Skip card -->
      <div class="cc-skip-body">{{ play.skip_reason }}</div>
      {% if play.watch_for %}
      <div class="cc-skip-watch">👁 Watch for: {{ play.watch_for }}</div>
      {% endif %}
      {% if play.upcoming_catalyst %}
      <div class="cc-catalyst-warning">⚠ {{ play.upcoming_catalyst }}</div>
      {% endif %}
      {% endif %}
    </div>
    {% endfor %}

    <div class="insights-box">
      <div class="insights-title">Key Insights This Week</div>
      {% for insight in cc.key_insights %}
      <div class="insight-item">{{ insight }}</div>
      {% endfor %}
    </div>

  </div>
</div>
{% endif %}

<!-- Running footer element (WeasyPrint) -->
<div id="page-footer">
  <span>{{ brand.tagline }} &nbsp;·&nbsp; {{ brand.brand_name }} &nbsp;·&nbsp; Confidential — For Members Only</span>
</div>

</body>
</html>"""


# ── Renderers ─────────────────────────────────────────────────────────────────

def render_weasyprint(html: str, output_path: Path):
    try:
        from weasyprint import HTML
    except ImportError:
        print("ERROR: weasyprint not installed. Run: pip install weasyprint")
        print("Or set \"pdf_engine\": \"xhtml2pdf\" in brand_config.json")
        sys.exit(1)
    HTML(string=html, base_url=str(ROOT)).write_pdf(str(output_path))


def resolve_css_vars(html: str) -> str:
    """
    Pre-process HTML for xhtml2pdf compatibility:
    1. Inline all CSS custom properties (var() not supported)
    2. Strip WeasyPrint-only @page sub-rules (@bottom-center, @top-center, etc.)
    3. Strip position: running() declarations
    """
    import re

    # 1. Resolve CSS variables from :root block
    root_match = re.search(r':root\s*\{([^}]+)\}', html, re.DOTALL)
    if root_match:
        css_vars = {}
        for line in root_match.group(1).split(';'):
            m = re.match(r'\s*--([a-zA-Z0-9-]+)\s*:\s*(.+)', line.strip())
            if m:
                css_vars[m.group(1)] = m.group(2).strip()

        def replacer(match):
            return css_vars.get(match.group(1), match.group(0))

        html = re.sub(r'var\(--([a-zA-Z0-9-]+)\)', replacer, html)

    # 2. Strip nested @-rules inside @page (WeasyPrint-only: @top-*, @bottom-*)
    html = re.sub(r'@page\s*\{[^{}]*\{[^}]*\}[^}]*\}',
                  lambda m: re.sub(r'\{[^{}]*\{[^}]*\}[^}]*\}',
                                   lambda inner: '{' + re.sub(r'@[a-z-]+\s*\{[^}]*\}', '', inner.group(0)[1:-1]) + '}',
                                   m.group(0)),
                  html, flags=re.DOTALL)
    # Simpler fallback: strip @bottom-center and @top-center blocks entirely
    html = re.sub(r'@(?:bottom|top)-[a-z]+\s*\{[^}]*\}', '', html)

    # 3. Strip position: running(...) — xhtml2pdf ignores it but let's be safe
    html = re.sub(r'position\s*:\s*running\([^)]*\)\s*;?', '', html)

    return html


def render_xhtml2pdf(html: str, output_path: Path):
    try:
        from xhtml2pdf import pisa
    except ImportError:
        print("ERROR: xhtml2pdf not installed. Run: pip install xhtml2pdf")
        sys.exit(1)
    html = resolve_css_vars(html)
    with open(output_path, "wb") as f:
        result = pisa.CreatePDF(html, dest=f)
    if result.err:
        print(f"xhtml2pdf errors: {result.err}")
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",   required=True, help="Path to report_data.json")
    parser.add_argument("--brand",  default="resources/brand_config.json", help="Path to brand_config.json")
    parser.add_argument("--output", required=True, help="Output PDF path")
    parser.add_argument("--debug",  action="store_true", help="Also save intermediate HTML")
    args = parser.parse_args()

    data_path  = Path(args.data)
    brand_path = Path(args.brand)
    out_path   = Path(args.output)

    if not data_path.exists():
        print(f"ERROR: data file not found: {data_path}")
        sys.exit(1)
    if not brand_path.exists():
        print(f"ERROR: brand config not found: {brand_path}")
        sys.exit(1)

    data  = load_json(data_path)
    brand = load_json(brand_path)
    c     = type("Colors", (), brand["colors"])()

    # Embed logos as data URIs so PDF is self-contained
    logo_path       = ROOT / brand.get("logo_path", "")
    logo_light_path = ROOT / brand.get("logo_path_light", "")
    logo_uri        = logo_as_data_uri(logo_path)
    logo_light_uri  = logo_as_data_uri(logo_light_path)

    if not logo_uri:
        print(f"WARNING: logo not found at {logo_path}")

    # Render template
    template = Template(HTML_TEMPLATE)
    html = template.render(
        data=data,
        brand=brand,
        c=c,
        logo_uri=logo_uri,
        logo_light_uri=logo_light_uri,
        arrow=arrow,
        fmt_pct=fmt_pct,
        sign_color=lambda pct, b=brand: sign_color(pct, b),
    )

    if args.debug:
        debug_path = out_path.with_suffix(".debug.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Debug HTML saved to: {debug_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    engine = brand.get("pdf_engine", "weasyprint").lower()
    print(f"Rendering PDF with {engine}...")

    if engine == "xhtml2pdf":
        render_xhtml2pdf(html, out_path)
    else:
        render_weasyprint(html, out_path)

    size_kb = out_path.stat().st_size / 1024
    print(f"PDF saved to: {out_path}  ({size_kb:.0f} KB)")

    if size_kb < 10:
        print("WARNING: PDF seems very small — open it to verify content rendered correctly.")


if __name__ == "__main__":
    main()

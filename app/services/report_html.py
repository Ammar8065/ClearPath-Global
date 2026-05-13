"""Generate a printable HTML assessment report using the ClearPath design system."""
from __future__ import annotations

from datetime import datetime
from html import escape

_JURISDICTION_LABELS = {
    "AU": "Australia", "SG": "Singapore", "HK": "Hong Kong",
    "UAE": "United Arab Emirates", "US": "United States",
}
_CATEGORY_LABELS = {
    "residency": "Residency", "tax": "Tax",
    "cross_border": "Cross-Border", "structure": "Structure",
}
_CATEGORY_WEIGHTS = {
    "residency": "30%", "tax": "30%",
    "cross_border": "25%", "structure": "15%",
}


def _esc(val: object) -> str:
    return escape(str(val)) if val else ""


def generate_report_html(result: dict, *, fact_count: int = 0) -> str:
    risk = result.get("overall_risk", "low")
    score = min(100, max(0, result.get("score", 0)))
    label = _esc(result.get("assessment_label") or "Private Assessment")
    triggered = result.get("triggered_rules", [])
    summary = result.get("summary", [])
    cat_breakdown = result.get("category_breakdown", {})
    jur_breakdown = result.get("jurisdiction_breakdown", {})
    citations = result.get("citations", [])
    incomplete = result.get("incomplete_rules", [])
    warnings = result.get("warnings", [])
    generated = datetime.now().strftime("%d %B %Y, %H:%M")

    jurisdictions = sorted({
        r.get("jurisdiction", "") if isinstance(r, dict) else r.jurisdiction
        for r in summary
    })
    jur_str = ", ".join(_JURISDICTION_LABELS.get(j, j) for j in jurisdictions) or "General review"

    # ── Triggered rules HTML ─────────────────────────────────────────────────
    rules_html = ""
    for r in (summary if isinstance(summary, list) else []):
        d = r if isinstance(r, dict) else r.model_dump()
        rc = d.get("rule_code", "")
        rl = d.get("risk_level", "low")
        desc = _esc(d.get("description", ""))
        jur = _esc(d.get("jurisdiction", ""))
        cat = d.get("category", "")
        cat_label = _CATEGORY_LABELS.get(cat, cat)
        conf = _esc(d.get("confidence_level", ""))
        rs = d.get("rule_score", 0)
        src_title = _esc(d.get("source_title", ""))
        src_url = _esc(d.get("source_url", ""))
        sec_ref = _esc(d.get("section_reference", "") or "")

        rules_html += f"""
        <div class="rule-card">
          <div class="rule-accent {rl}"></div>
          <div class="rule-body">
            <div class="rule-top">
              <span class="rule-code">{_esc(rc)}</span>
              <div class="badge-row">
                <span class="badge jurisdiction">{jur}</span>
                <span class="badge {rl}">{rl.upper()}</span>
                <span class="badge category">{_esc(cat_label)}</span>
              </div>
            </div>
            <p class="rule-desc">{desc}</p>
            <div class="rule-meta">
              {f'<span class="rule-ref">{sec_ref}</span>' if sec_ref else ''}
              <span>Score: {rs:.1f}</span>
              <span>Confidence: {conf}</span>
            </div>
            {f'<div class="rule-source">{src_title}</div>' if src_title else ''}
          </div>
        </div>"""

    # ── Category breakdown HTML ──────────────────────────────────────────────
    cat_rows = ""
    for cat_key in ("residency", "tax", "cross_border", "structure"):
        data = cat_breakdown.get(cat_key)
        if not data:
            continue
        cs = data.get("score", 0) if isinstance(data, dict) else data.score
        cc = data.get("triggered_count", 0) if isinstance(data, dict) else data.triggered_count
        cm = data.get("max_risk", "-") if isinstance(data, dict) else data.max_risk
        cat_rows += f"""
          <tr>
            <td style="font-weight:600; color:var(--ink-soft);">{_CATEGORY_LABELS.get(cat_key, cat_key)}</td>
            <td style="font-family:var(--font-mono); font-weight:600; color:var(--ink-mute);">{_CATEGORY_WEIGHTS.get(cat_key, '')}</td>
            <td>
              <div class="cat-bar-track"><div class="cat-bar-fill {cm}" style="width:{max(2, int(cs))}%"></div></div>
            </td>
            <td style="font-family:var(--font-mono); font-weight:600; text-align:center; color:var(--ink-mute);">{cs:.0f}</td>
            <td style="text-align:center; color:var(--ink-mute);">{cc}</td>
            <td style="text-align:center;"><span class="badge {cm}">{cm.upper() if cm else '-'}</span></td>
          </tr>"""

    # ── Jurisdiction breakdown HTML ──────────────────────────────────────────
    jur_rows = ""
    for j_code, j_data in sorted(jur_breakdown.items()):
        js = j_data.get("score", 0) if isinstance(j_data, dict) else j_data.score
        jc = j_data.get("triggered_count", 0) if isinstance(j_data, dict) else j_data.triggered_count
        j_label = _JURISDICTION_LABELS.get(j_code, j_code)
        jur_rows += f"""
          <tr>
            <td><span class="badge jurisdiction">{_esc(j_code)}</span> {_esc(j_label)}</td>
            <td>
              <div class="cat-bar-track"><div class="cat-bar-fill medium" style="width:{max(2, int(js))}%"></div></div>
            </td>
            <td style="font-family:var(--font-mono); font-weight:600; text-align:center; color:var(--ink-mute);">{js:.0f}</td>
            <td style="text-align:center; color:var(--ink-mute);">{jc}</td>
          </tr>"""

    # ── Citations HTML ───────────────────────────────────────────────────────
    cite_rows = ""
    for c in (citations if isinstance(citations, list) else []):
        d = c if isinstance(c, dict) else c.model_dump()
        cite_rows += f"""
        <tr>
          <td class="mono">{_esc(d.get('rule_code', ''))}</td>
          <td><span class="badge jurisdiction">{_esc(d.get('jurisdiction', ''))}</span></td>
          <td>{_esc(d.get('source_title', ''))}</td>
          <td class="brand-mono">{_esc(d.get('section_reference', '') or '')}</td>
        </tr>"""

    # ── Incomplete rules HTML ────────────────────────────────────────────────
    incomplete_html = ""
    if incomplete:
        risk_order = {"high": 0, "medium": 1, "low": 2}
        ranked = sorted(
            (i if isinstance(i, dict) else i.model_dump() for i in incomplete),
            key=lambda r: risk_order.get(r.get("risk_level", "low"), 9),
        )
        high_med = [r for r in ranked if r.get("risk_level") in ("high", "medium")]
        shown = high_med[:10] if high_med else list(ranked)[:5]
        remaining = len(incomplete) - len(shown)

        gap_items = ""
        for r in shown:
            rl = r.get("risk_level", "low")
            gap_items += f"""
          <tr>
            <td class="mono">{_esc(r.get('rule_code', ''))}</td>
            <td><span class="badge {rl}">{rl.upper()}</span></td>
            <td><span class="badge jurisdiction">{_esc(r.get('jurisdiction', ''))}</span></td>
            <td style="font-size:8.5pt; color:var(--ink-whisper);">{_esc(', '.join(r.get('missing_fields', [])))}</td>
          </tr>"""

        incomplete_html = f"""
<section class="page">
  <div class="page-header">
    <span>&mdash; <span class="brand">ClearPath Global</span> &mdash; Private Assessment Report</span>
    <span>Data Gaps</span>
  </div>
  <div class="section-kicker">&sect; Completeness</div>
  <h1>Data Gaps</h1>
  <p class="lede">{len(incomplete)} rules could not be evaluated due to missing client data.
  Providing additional facts may surface further findings.</p>

  <table>
    <thead><tr><th>Rule</th><th>Risk</th><th>Jur.</th><th>Missing Fields</th></tr></thead>
    <tbody>{gap_items}</tbody>
  </table>
  {f'<p style="font-family:var(--font-italic); font-style:italic; font-size:9pt; color:var(--ink-whisper); margin-top:4mm;">+ {remaining} additional rules omitted from this summary.</p>' if remaining > 0 else ''}
  <div class="page-footer">
    <span>&mdash; ClearPath Global &middot; Private Assessment Report</span>
    <span class="folio">Data Gaps</span>
  </div>
</section>"""

    # ── Warnings HTML ────────────────────────────────────────────────────────
    warnings_html = ""
    if warnings:
        w_items = "".join(
            f'<tr><td style="font-size:9pt; color:var(--ink-mute);">{_esc(w)}</td></tr>'
            for w in warnings
        )
        warnings_html = f"""
  <h2>Engine Warnings</h2>
  <table>
    <thead><tr><th>Warning</th></tr></thead>
    <tbody>{w_items}</tbody>
  </table>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>ClearPath Global &mdash; {label}</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@400;700;800;900&family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet" />
<style>
  :root {{
    --paper:         #ece3cf;
    --paper-raised:  #f7f0dd;
    --paper-deep:    #ddd3ba;
    --ink:           #0c0c0b;
    --ink-soft:      #1c1a16;
    --ink-mute:      #4a433a;
    --ink-whisper:   #857c69;
    --rule:          #bfb397;
    --rule-strong:   #938872;
    --brand:         #c5391a;
    --brand-deep:    #9a2710;
    --gold:          #c9922a;
    --navy:          #0d1520;
    --risk-high:     #c5391a;
    --risk-medium:   #a57318;
    --risk-low:      #2b5a3c;
    --font-display:  "Big Shoulders Display", Impact, sans-serif;
    --font-italic:   "Instrument Serif", Georgia, serif;
    --font-serif:    "Fraunces", Georgia, serif;
    --font-body:     "IBM Plex Sans", -apple-system, sans-serif;
    --font-mono:     "IBM Plex Mono", Consolas, monospace;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  @page {{ size: A4; margin: 0; }}

  html, body {{
    background: var(--paper);
    color: var(--ink);
    font-family: var(--font-body);
    font-size: 10.5pt;
    line-height: 1.6;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  /* ── PAGE SHELL ─────────────────────────────── */
  .page {{
    width: 210mm;
    min-height: 297mm;
    padding: 20mm 18mm;
    position: relative;
    page-break-after: always;
    overflow: hidden;
  }}
  .page:last-child {{ page-break-after: auto; }}

  .page::before {{
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    opacity: 0.35;
    mix-blend-mode: multiply;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.05  0 0 0 0 0.04  0 0 0 0 0.02  0 0 0 0 0.10 0'/></filter><rect width='240' height='240' filter='url(%23n)'/></svg>");
  }}

  /* ── COVER ─────────────────────────────────── */
  .cover {{
    background:
      radial-gradient(900px 600px at 120% -10%, rgba(197, 57, 26, 0.12), transparent 55%),
      radial-gradient(700px 500px at -20% 110%, rgba(201, 146, 42, 0.1), transparent 55%),
      var(--paper);
    display: flex;
    flex-direction: column;
    padding: 28mm 20mm 24mm;
  }}

  .cover-masthead {{
    border-top: 4px double var(--ink);
    border-bottom: 1px solid var(--ink);
    padding: 10px 0 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 8pt;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-soft);
  }}
  .cover-masthead .est {{ color: var(--brand); font-weight: 600; }}

  .cover-kicker {{
    margin-top: 28mm;
    font-family: var(--font-mono);
    font-size: 9pt;
    letter-spacing: 0.4em;
    text-transform: uppercase;
    color: var(--brand);
  }}

  .cover-title {{
    font-family: var(--font-display);
    font-weight: 900;
    font-size: 48pt;
    line-height: 0.92;
    letter-spacing: -0.02em;
    text-transform: uppercase;
    color: var(--ink);
    margin-top: 5mm;
    max-width: 170mm;
  }}

  .cover-subtitle {{
    font-family: var(--font-italic);
    font-style: italic;
    font-size: 15pt;
    line-height: 1.35;
    color: var(--ink-soft);
    margin-top: 8mm;
    max-width: 150mm;
  }}

  .metrics {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border: 1px solid var(--ink);
    margin: 10mm 0 0;
    background: var(--paper-raised);
  }}
  .metric {{
    padding: 5mm 4mm;
    border-right: 1px solid var(--rule);
  }}
  .metric:last-child {{ border-right: none; }}
  .metric .k {{
    font-family: var(--font-mono);
    font-size: 7pt;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--ink-whisper);
    margin-bottom: 3px;
  }}
  .metric .v {{
    font-family: var(--font-display);
    font-size: 36pt;
    font-weight: 800;
    line-height: 0.9;
  }}
  .metric .v.risk-high {{ color: var(--risk-high); }}
  .metric .v.risk-medium {{ color: var(--risk-medium); }}
  .metric .v.risk-low {{ color: var(--risk-low); }}
  .metric .u {{
    font-family: var(--font-italic);
    font-style: italic;
    font-size: 9pt;
    color: var(--brand);
    margin-top: 2px;
  }}

  .cover-meta {{
    margin-top: auto;
    border-top: 3px double var(--ink);
    padding-top: 10px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    font-family: var(--font-mono);
    font-size: 8pt;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--ink-mute);
  }}
  .cover-meta .label {{
    display: block;
    color: var(--brand);
    font-weight: 600;
    margin-bottom: 3px;
    font-size: 7pt;
  }}
  .cover-meta .value {{
    color: var(--ink);
    font-family: var(--font-serif);
    font-size: 10pt;
    letter-spacing: 0;
    text-transform: none;
  }}

  /* ── INTERIOR PAGES ────────────────────────── */
  .page-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1px solid var(--ink);
    padding-bottom: 6px;
    font-family: var(--font-mono);
    font-size: 7.5pt;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-mute);
    margin-bottom: 8mm;
  }}
  .page-header .brand {{ color: var(--brand); font-weight: 600; }}

  .page-footer {{
    position: absolute;
    left: 18mm; right: 18mm; bottom: 12mm;
    border-top: 1px solid var(--rule);
    padding-top: 6px;
    display: flex;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 7.5pt;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-whisper);
  }}
  .page-footer .folio {{ color: var(--brand); font-weight: 600; }}

  .section-kicker {{
    font-family: var(--font-mono);
    font-size: 8pt;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: var(--brand);
    margin-bottom: 4px;
  }}

  h1 {{
    font-family: var(--font-display);
    font-weight: 800;
    font-size: 34pt;
    line-height: 0.95;
    letter-spacing: -0.015em;
    text-transform: uppercase;
    color: var(--ink);
    border-bottom: 3px double var(--ink);
    padding-bottom: 10px;
    margin-bottom: 12px;
  }}

  h2 {{
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 18pt;
    text-transform: uppercase;
    letter-spacing: -0.01em;
    color: var(--ink);
    margin-top: 7mm;
    margin-bottom: 4mm;
    border-bottom: 1px solid var(--rule);
    padding-bottom: 4px;
  }}

  .lede {{
    font-family: var(--font-italic);
    font-style: italic;
    font-size: 12.5pt;
    line-height: 1.4;
    color: var(--ink-soft);
    max-width: 150mm;
    margin-bottom: 10px;
  }}

  p {{ margin-bottom: 6px; color: var(--ink-soft); }}

  /* ── BADGES ─────────────────────────────────── */
  .badge {{
    display: inline-block;
    padding: 1px 7px;
    font-family: var(--font-mono);
    font-size: 7pt;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
    vertical-align: middle;
    margin: 0 2px;
  }}
  .badge.high {{ background: var(--risk-high); color: #fff8e6; }}
  .badge.medium {{ background: var(--risk-medium); color: #fff8e6; }}
  .badge.low {{ background: var(--risk-low); color: #fff8e6; }}
  .badge.jurisdiction {{ background: var(--navy); color: #e0ddd5; }}
  .badge.category {{ background: var(--paper-raised); color: var(--ink-mute); border: 1px solid var(--rule); }}

  /* ── TABLES ─────────────────────────────────── */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 4mm 0;
    font-size: 9pt;
  }}
  th, td {{
    padding: 5px 8px;
    text-align: left;
    border-bottom: 1px solid var(--rule);
    vertical-align: top;
  }}
  th {{
    font-family: var(--font-mono);
    font-size: 7pt;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--ink-whisper);
    border-bottom: 2px solid var(--ink);
    padding-top: 0;
  }}
  td {{ color: var(--ink-soft); }}
  td.mono {{
    font-family: var(--font-mono);
    font-size: 8.5pt;
    font-weight: 500;
    color: var(--ink-soft);
  }}
  td.brand-mono {{
    font-family: var(--font-mono);
    font-size: 8pt;
    font-weight: 600;
    color: var(--brand-deep);
  }}

  /* ── CATEGORY BAR ───────────────────────────── */
  .cat-bar-track {{
    height: 8px;
    background: var(--paper-deep);
    border-radius: 1px;
    overflow: hidden;
  }}
  .cat-bar-fill {{ height: 100%; border-radius: 1px; }}
  .cat-bar-fill.high {{ background: var(--risk-high); }}
  .cat-bar-fill.medium {{ background: var(--risk-medium); }}
  .cat-bar-fill.low {{ background: var(--risk-low); }}

  /* ── RULE CARDS ─────────────────────────────── */
  .rule-card {{
    display: flex;
    margin-bottom: 4mm;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .rule-accent {{
    width: 4px;
    flex-shrink: 0;
    border-radius: 1px;
  }}
  .rule-accent.high {{ background: var(--risk-high); }}
  .rule-accent.medium {{ background: var(--risk-medium); }}
  .rule-accent.low {{ background: var(--risk-low); }}
  .rule-body {{
    flex: 1;
    padding: 4mm 5mm;
    background: var(--paper-raised);
    border: 1px solid var(--rule);
    border-left: none;
  }}
  .rule-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 3px;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .rule-code {{
    font-family: var(--font-display);
    font-weight: 800;
    font-size: 13pt;
    text-transform: uppercase;
    color: var(--ink);
    letter-spacing: -0.01em;
  }}
  .badge-row {{ display: flex; gap: 3px; flex-wrap: wrap; }}
  .rule-desc {{
    font-size: 9pt;
    color: var(--ink-soft);
    line-height: 1.5;
    margin-bottom: 3px;
  }}
  .rule-meta {{
    font-family: var(--font-mono);
    font-size: 7.5pt;
    color: var(--ink-whisper);
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .rule-ref {{ color: var(--brand-deep); font-weight: 500; }}
  .rule-source {{
    font-family: var(--font-italic);
    font-style: italic;
    font-size: 8.5pt;
    color: var(--ink-whisper);
    margin-top: 2px;
  }}

  /* ── CALLOUT ────────────────────────────────── */
  .callout {{
    background: var(--paper-raised);
    border: 1px solid var(--ink);
    border-left: 4px solid var(--brand);
    padding: 5mm 6mm;
    margin: 6mm 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .callout .c-label {{
    font-family: var(--font-mono);
    font-size: 7.5pt;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--brand);
    font-weight: 600;
    margin-bottom: 3px;
  }}
  .callout p {{
    font-size: 9pt;
    color: var(--ink-soft);
    line-height: 1.5;
    margin: 0;
  }}

  .ornament {{
    text-align: center;
    font-family: var(--font-serif);
    color: var(--brand);
    margin: 6mm 0;
    letter-spacing: 1em;
    font-size: 13pt;
  }}

  .closing {{
    text-align: center;
    font-family: var(--font-mono);
    font-size: 7.5pt;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: var(--ink-whisper);
    margin-top: 12mm;
  }}
  .closing .brand-stamp {{ color: var(--brand); font-weight: 600; }}

  @media print {{
    body {{ padding-top: 0; }}
  }}
</style>
</head>
<body>

<!-- ═══════════════ COVER ═══════════════ -->
<section class="page cover">
  <div class="cover-masthead">
    <span>Private Assessment Report</span>
    <span class="est">&mdash; ClearPath Global &mdash;</span>
    <span>Risk Intelligence</span>
  </div>

  <div class="cover-kicker">Risk Intelligence Dispatch</div>
  <h1 class="cover-title">{label}</h1>
  <p class="cover-subtitle">
    Cross-border risk assessment covering {_esc(jur_str)}.
    {len(triggered)} rule{'s' if len(triggered) != 1 else ''} triggered
    at {risk.upper()} overall risk.
  </p>

  <div class="metrics">
    <div class="metric">
      <div class="k">&mdash; Risk Level</div>
      <div class="v risk-{risk}">{risk.upper()}</div>
      <div class="u">overall severity</div>
    </div>
    <div class="metric">
      <div class="k">&mdash; Score</div>
      <div class="v">{score:.0f}</div>
      <div class="u">weighted composite</div>
    </div>
    <div class="metric">
      <div class="k">&mdash; Rules</div>
      <div class="v">{len(triggered)}</div>
      <div class="u">triggered</div>
    </div>
    <div class="metric">
      <div class="k">&mdash; Facts</div>
      <div class="v">{fact_count}</div>
      <div class="u">provided</div>
    </div>
  </div>

  <div class="cover-meta">
    <div>
      <span class="label">&mdash; Generated</span>
      <span class="value">{_esc(generated)}</span>
    </div>
    <div>
      <span class="label">&mdash; Jurisdictions</span>
      <span class="value">{_esc(jur_str)}</span>
    </div>
    <div>
      <span class="label">&mdash; Mode</span>
      <span class="value">Privacy-first</span>
    </div>
    <div>
      <span class="label">&mdash; Engine</span>
      <span class="value">ClearPath Global</span>
    </div>
  </div>
</section>

<!-- ═══════════════ CATEGORY BREAKDOWN ═══════════════ -->
{'<section class="page">' + """
  <div class="page-header">
    <span>&mdash; <span class="brand">ClearPath Global</span> &mdash; Private Assessment Report</span>
    <span>Severity Profile</span>
  </div>
  <div class="section-kicker">&sect; Severity Profile</div>
  <h1>Category Breakdown</h1>
  <p class="lede">Risk scores and rule counts across each assessment category, with the maximum
  severity level encountered in each.</p>

  <table>
    <thead>
      <tr><th>Category</th><th>Weight</th><th>Score</th><th>Score</th><th>Triggered</th><th>Max Risk</th></tr>
    </thead>
    <tbody>""" + cat_rows + """</tbody>
  </table>""" + ("""

  <h2>Jurisdiction Breakdown</h2>
  <table>
    <thead>
      <tr><th>Jurisdiction</th><th>Score</th><th>Score</th><th>Triggered</th></tr>
    </thead>
    <tbody>""" + jur_rows + """</tbody>
  </table>""" if jur_rows else '') + """

  <div class="callout" style="margin-top:6mm;">
    <div class="c-label">&mdash; How the score is calculated</div>
    <p>Each triggered rule is scored using its risk weight (Low=1, Medium=2, High=3) and confidence weight
    (Low=0.6, Medium=0.8, High=1.0). The category score is the average of all triggered rule scores in that
    category. The overall composite score is a weighted average: Residency 30%, Tax 30%, Cross-Border 25%,
    Structure 15%. The overall risk level is always the maximum severity across all triggered rules.</p>
  </div>

  <div class="page-footer">
    <span>&mdash; ClearPath Global &middot; Private Assessment Report</span>
    <span class="folio">Severity Profile</span>
  </div>
</section>""" if cat_rows else ''}

<!-- ═══════════════ TRIGGERED RULES ═══════════════ -->
<section class="page">
  <div class="page-header">
    <span>&mdash; <span class="brand">ClearPath Global</span> &mdash; Private Assessment Report</span>
    <span>Findings</span>
  </div>
  <div class="section-kicker">&sect; Findings</div>
  <h1>Triggered Rules</h1>
  <p class="lede">{len(summary)} rule{'s' if len(summary) != 1 else ''} triggered by the facts provided.
  Each finding includes the legislative basis, risk severity, and confidence assessment.</p>

  {rules_html if rules_html else '<p style="color: var(--ink-mute); font-family: var(--font-italic); font-style: italic; margin-top: 8mm;">No rules were triggered by the provided facts.</p>'}

  <div class="page-footer">
    <span>&mdash; ClearPath Global &middot; Private Assessment Report</span>
    <span class="folio">Findings</span>
  </div>
</section>

<!-- ═══════════════ CITATIONS ═══════════════ -->
{'<section class="page">' + """
  <div class="page-header">
    <span>&mdash; <span class="brand">ClearPath Global</span> &mdash; Private Assessment Report</span>
    <span>Authority</span>
  </div>
  <div class="section-kicker">&sect; Authority</div>
  <h1>Legislative Citations</h1>
  <p class="lede">Authoritative sources referenced by the triggered rules. Every finding traces
  to a specific section of legislation or regulatory guidance.</p>

  <table>
    <thead><tr><th>Rule</th><th>Jur.</th><th>Source</th><th>Section Reference</th></tr></thead>
    <tbody>""" + cite_rows + """</tbody>
  </table>
  <div class="page-footer">
    <span>&mdash; ClearPath Global &middot; Private Assessment Report</span>
    <span class="folio">Authority</span>
  </div>
</section>""" if cite_rows else ''}

<!-- ═══════════════ DATA GAPS ═══════════════ -->
{incomplete_html}

<!-- ═══════════════ CLOSING ═══════════════ -->
<section class="page">
  <div class="page-header">
    <span>&mdash; <span class="brand">ClearPath Global</span> &mdash; Private Assessment Report</span>
    <span>Disclaimer</span>
  </div>

  {warnings_html}

  <div class="callout" style="margin-top: {'6mm' if warnings else '16mm'};">
    <div class="c-label">&mdash; Important Notice</div>
    <p>
      This report is generated by ClearPath Global's rule-based assessment engine. It is intended as
      a decision-support tool for qualified tax and immigration advisors and does not constitute tax,
      legal, or financial advice. All findings should be independently verified against current
      legislation and the client's specific circumstances before any action is taken. ClearPath Global
      accepts no liability for decisions made solely on the basis of this report.
    </p>
  </div>

  <div class="callout" style="border-left-color: var(--gold);">
    <div class="c-label" style="color: var(--gold);">&mdash; Privacy Guarantee</div>
    <p>
      No client data was stored during the generation of this report. The facts used for this assessment
      existed only for the duration of the evaluation request and were discarded immediately after the
      result was computed. This report is the only record of the assessment.
    </p>
  </div>

  <div class="ornament" style="margin-top: 16mm;">&#10022; &nbsp;&nbsp; &#10022; &nbsp;&nbsp; &#10022;</div>

  <div class="closing">
    &mdash; End of Report &mdash;<br/>
    <span class="brand-stamp">ClearPath Global</span><br/>
    <span style="font-size:7pt; letter-spacing:0.15em; margin-top:4px; display:inline-block;">
      Private Assessment Report &middot; Generated {_esc(generated)}
    </span>
  </div>

  <div class="page-footer">
    <span>&mdash; ClearPath Global &middot; Private Assessment Report</span>
    <span class="folio">Fin.</span>
  </div>
</section>

</body>
</html>"""

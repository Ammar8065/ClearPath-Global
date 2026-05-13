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
    client_label = _esc(result.get("assessment_label") or "Unspecified")
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
            <td style="font-weight:600; color:var(--text);">{_CATEGORY_LABELS.get(cat_key, cat_key)}</td>
            <td class="mono">{_CATEGORY_WEIGHTS.get(cat_key, '')}</td>
            <td>
              <div class="cat-bar-track"><div class="cat-bar-fill {cm}" style="width:{max(2, int(cs))}%"></div></div>
            </td>
            <td class="mono" style="text-align:center;">{cs:.0f}</td>
            <td style="text-align:center; color:var(--text-secondary);">{cc}</td>
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
            <td><span class="badge jurisdiction">{_esc(j_code)}</span> &nbsp; {_esc(j_label)}</td>
            <td>
              <div class="cat-bar-track"><div class="cat-bar-fill medium" style="width:{max(2, int(js))}%"></div></div>
            </td>
            <td class="mono" style="text-align:center;">{js:.0f}</td>
            <td style="text-align:center; color:var(--text-secondary);">{jc}</td>
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

    # ── Severity Profile section ─────────────────────────────────────────────
    severity_html = ""
    if cat_rows:
        jur_block = ""
        if jur_rows:
            jur_block = f"""
  <h2>Jurisdiction Breakdown</h2>
  <table>
    <thead>
      <tr><th>Jurisdiction</th><th>Score</th><th>Score</th><th>Triggered</th></tr>
    </thead>
    <tbody>{jur_rows}</tbody>
  </table>"""
        severity_html = f"""
<section class="report-section">
  <div class="section-kicker">Section &mdash; Severity Profile</div>
  <h1>Category Breakdown</h1>
  <p class="lede">Risk scores and rule counts across each assessment category, with the maximum
  severity level encountered in each.</p>

  <table>
    <thead>
      <tr><th>Category</th><th>Weight</th><th>Score</th><th>Score</th><th>Triggered</th><th>Max Risk</th></tr>
    </thead>
    <tbody>{cat_rows}</tbody>
  </table>{jur_block}

  <div class="callout">
    <div class="c-label">How the score is calculated</div>
    <p>Each triggered rule is scored using its risk weight (Low=1, Medium=2, High=3) and confidence weight
    (Low=0.6, Medium=0.8, High=1.0). The category score is the average of all triggered rule scores in that
    category. The overall composite score is a weighted average: Residency 30%, Tax 30%, Cross-Border 25%,
    Structure 15%. The overall risk level is always the maximum severity across all triggered rules.</p>
  </div>
</section>"""

    # ── Citations section ────────────────────────────────────────────────────
    citations_html = ""
    if cite_rows:
        citations_html = f"""
<section class="report-section">
  <div class="section-kicker">Section &mdash; Authority</div>
  <h1>Legislative Citations</h1>
  <p class="lede">Authoritative sources referenced by the triggered rules. Every finding traces
  to a specific section of legislation or regulatory guidance.</p>

  <table>
    <thead><tr><th>Rule</th><th>Jur.</th><th>Source</th><th>Section Reference</th></tr></thead>
    <tbody>{cite_rows}</tbody>
  </table>
</section>"""

    # ── Incomplete rules section ─────────────────────────────────────────────
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
            <td style="font-size:8.5pt; color:var(--text-muted);">{_esc(', '.join(r.get('missing_fields', [])))}</td>
          </tr>"""

        more_note = (
            f'<p style="font-style:italic; font-size:9pt; color:var(--text-muted); margin-top:4mm;">'
            f'+ {remaining} additional rules omitted from this summary.</p>'
            if remaining > 0 else ''
        )
        incomplete_html = f"""
<section class="report-section">
  <div class="section-kicker">Section &mdash; Completeness</div>
  <h1>Data Gaps</h1>
  <p class="lede">{len(incomplete)} rules could not be evaluated due to missing client data.
  Providing additional facts may surface further findings.</p>

  <table>
    <thead><tr><th>Rule</th><th>Risk</th><th>Jur.</th><th>Missing Fields</th></tr></thead>
    <tbody>{gap_items}</tbody>
  </table>
  {more_note}
</section>"""

    # ── Warnings HTML ────────────────────────────────────────────────────────
    warnings_html = ""
    if warnings:
        w_items = "".join(
            f'<tr><td style="font-size:9pt; color:var(--text-secondary);">{_esc(w)}</td></tr>'
            for w in warnings
        )
        warnings_html = f"""
  <h2>Engine Warnings</h2>
  <table>
    <thead><tr><th>Warning</th></tr></thead>
    <tbody>{w_items}</tbody>
  </table>"""

    no_findings = (
        '<p style="color: var(--text-muted); font-style: italic; margin-top: 8mm;">'
        'No rules were triggered by the provided facts.</p>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>ClearPath Global &mdash; {client_label}</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<style>
  :root {{
    --bg:            #ffffff;
    --bg-subtle:     #f8f9fa;
    --bg-muted:      #f1f3f5;
    --text:          #1a1a1a;
    --text-secondary:#4a4a4a;
    --text-muted:    #6b7280;
    --text-faint:    #9ca3af;
    --border:        #e5e7eb;
    --border-strong: #d1d5db;
    --accent:        #3b82f6;
    --accent-light:  #eff6ff;
    --accent-deep:   #1d4ed8;
    --accent-subtle: #dbeafe;
    --gold:          #b8860b;
    --gold-light:    #fef9ec;
    --green:         #15803d;
    --green-light:   #f0fdf4;
    --risk-high:     #dc2626;
    --risk-medium:   #d97706;
    --risk-low:      #16a34a;
    --navy:          #0f172a;
    --font-sans:     "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --font-mono:     "JetBrains Mono", "Fira Code", Consolas, monospace;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  @page {{ size: A4; margin: 18mm 16mm 18mm 16mm; }}

  html, body {{
    background: #f1f3f5;
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 10.5pt;
    line-height: 1.65;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  /* ── COVER PAGE (forced standalone) ─────────── */
  .cover {{
    width: 210mm;
    min-height: 297mm;
    padding: 28mm 24mm 24mm;
    background: var(--bg);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    page-break-after: always;
    break-after: page;
  }}

  .cover-brand {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    margin-bottom: 12mm;
  }}
  .cover-brand .cp-mark {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    background: var(--accent);
    color: #fff;
    font-weight: 800;
    font-size: 22px;
    letter-spacing: -0.02em;
    border-radius: 14px;
  }}
  .cover-brand .brand-name {{
    font-weight: 700;
    font-size: 16pt;
    color: var(--text);
    letter-spacing: -0.02em;
  }}
  .cover-brand .brand-sub {{
    font-weight: 400;
    font-size: 9pt;
    color: var(--text-muted);
    display: block;
    margin-top: -2px;
  }}

  .cover-kicker {{
    font-family: var(--font-mono);
    font-size: 9pt;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 6px;
  }}

  .cover-title {{
    font-weight: 800;
    font-size: 32pt;
    line-height: 1.05;
    letter-spacing: -0.03em;
    color: var(--text);
    margin-bottom: 6mm;
    max-width: 160mm;
  }}

  .cover-subtitle {{
    font-weight: 400;
    font-size: 11pt;
    line-height: 1.55;
    color: var(--text-secondary);
    max-width: 150mm;
    margin-bottom: 8mm;
  }}

  /* ── PROMINENT CLIENT BANNER ────────────────── */
  .client-banner {{
    background: var(--accent);
    color: #fff;
    border-radius: 12px;
    padding: 6mm 8mm;
    width: 100%;
    max-width: 165mm;
    margin-bottom: 6mm;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    text-align: left;
  }}
  .client-banner .cb-label {{
    font-family: var(--font-mono);
    font-size: 8pt;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.78);
    margin-bottom: 4px;
  }}
  .client-banner .cb-value {{
    font-weight: 700;
    font-size: 18pt;
    letter-spacing: -0.015em;
    line-height: 1.15;
    color: #fff;
  }}
  .client-banner .cb-side {{
    font-family: var(--font-mono);
    font-size: 8pt;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.78);
    text-align: right;
    flex-shrink: 0;
  }}
  .client-banner .cb-side strong {{
    color: #fff;
    font-family: var(--font-sans);
    font-weight: 600;
    font-size: 10pt;
    letter-spacing: 0;
    text-transform: none;
    display: block;
    margin-top: 2px;
  }}

  /* ── COVER METRICS GRID ─────────────────────── */
  .metrics {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 3mm;
    width: 100%;
    max-width: 165mm;
    margin-bottom: 6mm;
  }}
  .metric {{
    background: var(--bg-subtle);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 5mm 3mm;
    text-align: center;
  }}
  .metric .k {{
    font-family: var(--font-mono);
    font-size: 7pt;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 5px;
  }}
  .metric .v {{
    font-size: 28pt;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.025em;
    color: var(--text);
  }}
  .metric .v.risk-high {{ color: var(--risk-high); }}
  .metric .v.risk-medium {{ color: var(--risk-medium); }}
  .metric .v.risk-low {{ color: var(--risk-low); }}
  .metric .u {{
    font-size: 8pt;
    color: var(--text-muted);
    margin-top: 4px;
  }}

  /* ── COVER METADATA CARD ────────────────────── */
  .cover-meta-card {{
    background: var(--accent-light);
    border: 1px solid var(--accent-subtle);
    border-radius: 12px;
    padding: 5mm 8mm;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    width: 100%;
    max-width: 165mm;
  }}
  .cover-meta-card .meta-item {{ text-align: center; }}
  .cover-meta-card .meta-label {{
    display: block;
    font-family: var(--font-mono);
    font-size: 7pt;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 3px;
  }}
  .cover-meta-card .meta-value {{
    font-weight: 600;
    font-size: 9.5pt;
    color: var(--text);
  }}

  /* ── BODY (continuous flowing pages) ────────── */
  .report-body {{
    background: var(--bg);
    width: 210mm;
    margin: 0 auto;
  }}

  .report-section {{
    margin-bottom: 9mm;
  }}

  .section-kicker {{
    font-family: var(--font-mono);
    font-size: 8pt;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 3px;
  }}

  h1 {{
    font-weight: 800;
    font-size: 22pt;
    line-height: 1.1;
    letter-spacing: -0.025em;
    color: var(--text);
    margin-bottom: 8px;
  }}

  h2 {{
    font-weight: 700;
    font-size: 14pt;
    letter-spacing: -0.01em;
    color: var(--text);
    margin-top: 7mm;
    margin-bottom: 3mm;
    padding-bottom: 3px;
    border-bottom: 1px solid var(--border);
  }}

  .lede {{
    font-weight: 400;
    font-size: 11pt;
    line-height: 1.55;
    color: var(--text-secondary);
    max-width: 155mm;
    margin-bottom: 8px;
  }}

  p {{ margin-bottom: 6px; color: var(--text-secondary); }}

  /* ── BADGES ─────────────────────────────────── */
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    font-family: var(--font-mono);
    font-size: 7pt;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 600;
    vertical-align: middle;
    margin: 0 2px;
    border-radius: 3px;
  }}
  .badge.high {{ background: var(--risk-high); color: #fff; }}
  .badge.medium {{ background: var(--risk-medium); color: #fff; }}
  .badge.low {{ background: var(--risk-low); color: #fff; }}
  .badge.jurisdiction {{ background: var(--navy); color: #e2e8f0; }}
  .badge.category {{ background: var(--bg-muted); color: var(--text-muted); border: 1px solid var(--border); }}

  /* ── TABLES ─────────────────────────────────── */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 4mm 0;
    font-size: 9pt;
  }}
  th, td {{
    padding: 6px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }}
  th {{
    font-family: var(--font-mono);
    font-size: 7pt;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    border-bottom: 2px solid var(--border-strong);
    background: var(--bg-subtle);
    font-weight: 600;
    padding-top: 5px;
    padding-bottom: 5px;
  }}
  td {{ color: var(--text-secondary); }}
  td.mono {{
    font-family: var(--font-mono);
    font-size: 8.5pt;
    font-weight: 500;
    color: var(--text-secondary);
  }}
  td.brand-mono {{
    font-family: var(--font-mono);
    font-size: 8.5pt;
    font-weight: 600;
    color: var(--accent-deep);
  }}
  thead {{ display: table-header-group; }}
  tr {{ page-break-inside: avoid; break-inside: avoid; }}

  /* ── CATEGORY BAR ───────────────────────────── */
  .cat-bar-track {{
    height: 6px;
    background: var(--bg-muted);
    border-radius: 3px;
    overflow: hidden;
  }}
  .cat-bar-fill {{ height: 100%; border-radius: 3px; }}
  .cat-bar-fill.high {{ background: var(--risk-high); }}
  .cat-bar-fill.medium {{ background: var(--risk-medium); }}
  .cat-bar-fill.low {{ background: var(--risk-low); }}

  /* ── RULE CARDS ─────────────────────────────── */
  .rule-card {{
    display: flex;
    margin-bottom: 4mm;
    break-inside: avoid;
    page-break-inside: avoid;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border);
  }}
  .rule-accent {{
    width: 4px;
    flex-shrink: 0;
  }}
  .rule-accent.high {{ background: var(--risk-high); }}
  .rule-accent.medium {{ background: var(--risk-medium); }}
  .rule-accent.low {{ background: var(--risk-low); }}
  .rule-body {{
    flex: 1;
    padding: 4mm 5mm;
    background: var(--bg-subtle);
  }}
  .rule-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .rule-code {{
    font-weight: 800;
    font-size: 12pt;
    color: var(--text);
    letter-spacing: -0.01em;
  }}
  .badge-row {{ display: flex; gap: 4px; flex-wrap: wrap; }}
  .rule-desc {{
    font-size: 9pt;
    color: var(--text-secondary);
    line-height: 1.5;
    margin: 3px 0;
  }}
  .rule-meta {{
    font-family: var(--font-mono);
    font-size: 7.5pt;
    color: var(--text-muted);
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 3px;
  }}
  .rule-ref {{ color: var(--accent-deep); font-weight: 500; }}
  .rule-source {{
    font-style: italic;
    font-size: 8.5pt;
    color: var(--text-muted);
    margin-top: 3px;
  }}

  /* ── CALLOUT ────────────────────────────────── */
  .callout {{
    background: var(--accent-light);
    border-left: 4px solid var(--accent);
    border-radius: 0 6px 6px 0;
    padding: 5mm 6mm;
    margin: 6mm 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .callout .c-label {{
    font-family: var(--font-mono);
    font-size: 7.5pt;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent-deep);
    font-weight: 600;
    margin-bottom: 4px;
  }}
  .callout p {{
    font-size: 9.5pt;
    color: var(--text-secondary);
    line-height: 1.55;
    margin: 0;
  }}
  .callout-gold {{
    background: var(--gold-light);
    border-left-color: var(--gold);
  }}
  .callout-gold .c-label {{ color: var(--gold); }}

  .ornament {{
    text-align: center;
    color: var(--accent);
    margin: 8mm 0;
    font-size: 14pt;
    letter-spacing: 0.6em;
    opacity: 0.4;
  }}

  .closing {{
    text-align: center;
    font-family: var(--font-mono);
    font-size: 7.5pt;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-faint);
    margin-top: 10mm;
  }}
  .closing .brand-stamp {{
    color: var(--accent);
    font-weight: 700;
    font-size: 8.5pt;
  }}

  @media print {{
    html, body {{
      margin: 0;
      padding: 0;
      background: #fff;
    }}
    .cover {{ padding: 18mm 18mm 14mm; }}
    .report-body {{ padding: 0; }}
  }}
  @media screen {{
    body {{ padding: 12mm 0; }}
    .cover, .report-body {{
      margin: 0 auto 12mm;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.08);
      border-radius: 2px;
    }}
    .report-body {{ padding: 18mm 16mm; }}
  }}
</style>
</head>
<body>

<!-- ═══════════════ COVER ═══════════════ -->
<section class="cover">
  <div class="cover-brand">
    <div class="cp-mark">CP</div>
    <div>
      <div class="brand-name">ClearPath Global</div>
      <span class="brand-sub">Risk Intelligence Platform</span>
    </div>
  </div>

  <div class="cover-kicker">Private Risk Assessment</div>
  <h1 class="cover-title">Cross-Border Risk Report</h1>
  <p class="cover-subtitle">
    Privacy-first cross-border risk assessment covering {_esc(jur_str)}.
  </p>

  <div class="client-banner">
    <div>
      <div class="cb-label">Client / Reference</div>
      <div class="cb-value">{client_label}</div>
    </div>
    <div class="cb-side">
      Generated<br/>
      <strong>{_esc(generated)}</strong>
    </div>
  </div>

  <div class="metrics">
    <div class="metric">
      <div class="k">Risk Level</div>
      <div class="v risk-{risk}">{risk.upper()}</div>
      <div class="u">overall severity</div>
    </div>
    <div class="metric">
      <div class="k">Score</div>
      <div class="v">{score:.0f}</div>
      <div class="u">weighted composite</div>
    </div>
    <div class="metric">
      <div class="k">Rules</div>
      <div class="v">{len(triggered)}</div>
      <div class="u">triggered</div>
    </div>
    <div class="metric">
      <div class="k">Facts</div>
      <div class="v">{fact_count}</div>
      <div class="u">provided</div>
    </div>
  </div>

  <div class="cover-meta-card">
    <div class="meta-item">
      <span class="meta-label">Jurisdictions</span>
      <span class="meta-value">{_esc(jur_str)}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Mode</span>
      <span class="meta-value">Privacy-first</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Engine</span>
      <span class="meta-value">ClearPath Global</span>
    </div>
  </div>
</section>

<!-- ═══════════════ FLOWING REPORT BODY ═══════════════ -->
<div class="report-body">
{severity_html}

<section class="report-section">
  <div class="section-kicker">Section &mdash; Findings</div>
  <h1>Triggered Rules</h1>
  <p class="lede">{len(summary)} rule{'s' if len(summary) != 1 else ''} triggered by the facts provided.
  Each finding includes the legislative basis, risk severity, and confidence assessment.</p>

  {rules_html if rules_html else no_findings}
</section>

{citations_html}

{incomplete_html}

<section class="report-section">
  {warnings_html}

  <div class="callout">
    <div class="c-label">Important Notice</div>
    <p>
      This report is generated by ClearPath Global's rule-based assessment engine. It is intended as
      a decision-support tool for qualified tax and immigration advisors and does not constitute tax,
      legal, or financial advice. All findings should be independently verified against current
      legislation and the client's specific circumstances before any action is taken. ClearPath Global
      accepts no liability for decisions made solely on the basis of this report.
    </p>
  </div>

  <div class="callout callout-gold">
    <div class="c-label">Privacy Guarantee</div>
    <p>
      No client data was stored during the generation of this report. The facts used for this assessment
      existed only for the duration of the evaluation request and were discarded immediately after the
      result was computed. This report is the only record of the assessment.
    </p>
  </div>

  <div class="ornament">&#9670; &nbsp;&nbsp; &#9670; &nbsp;&nbsp; &#9670;</div>

  <div class="closing">
    End of Report<br/>
    <span class="brand-stamp">ClearPath Global</span><br/>
    <span style="font-size:7pt; letter-spacing:0.15em; margin-top:4px; display:inline-block;">
      Private Assessment Report &middot; Generated {_esc(generated)}
    </span>
  </div>
</section>
</div>

</body>
</html>"""

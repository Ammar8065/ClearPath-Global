"""Scrape every knowledge-source page referenced by seed_sources.py.

Output: rag/scraped/{KEY}.txt (one file per source, with a metadata header)
        rag/scraped/manifest.json (fetch status, method, timestamps, char counts)

ato.gov.au blocks non-Australian traffic (Akamai 403), so ATO pages are fetched
from the most recent HTTP-200 Wayback Machine snapshot of the exact URL — the
archived copy of the real page, never synthesised content. Everything else is
fetched live. PDF sources are extracted with pypdf.
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from seed_sources import SOURCE_FIXTURES  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "scraped"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
WAYBACK_DOMAINS = ("ato.gov.au",)

# Some sources are thin "hub" landing pages; the substantive guidance the rules rely on
# lives one level down. These sub-pages are fetched the same way as their parent and
# appended to the parent's text file. Skipped gracefully if unavailable.
SUPPLEMENTARY_PAGES = {
    "AU_ATO_CGT": [
        "https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/foreign-residents-and-capital-gains-tax/main-residence-exemption-for-foreign-residents",
        "https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/foreign-residents-and-capital-gains-tax/taxable-australian-property",
        "https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/foreign-residents-and-capital-gains-tax/cgt-discount-for-foreign-residents",
    ],
    "AU_ATO_MEDICARE": [
        "https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/medicare-levy-surcharge/medicare-levy-surcharge-income-thresholds-and-rates",
    ],
    "AU_ATO_FRCGW": [
        "https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/foreign-residents-and-capital-gains-tax/foreign-resident-capital-gains-withholding/foreign-resident-capital-gains-withholding-overview",
    ],
    "HK_IRD_PROFITS": [
        "https://www.ird.gov.hk/eng/tax/bus_pft.htm",  # profits tax rates (16.5%/8.25% two-tier)
    ],
}


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # NB: never strip <form> — ASP.NET WebForms sites (tax.gov.ae) nest the whole page in one.
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside"]):
        tag.decompose()
    def extract(node) -> str:
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in node.get_text("\n").splitlines()]
        return "\n".join(ln for ln in lines if ln)

    root = soup.find("main") or soup.find("article") or soup.body or soup
    text = extract(root)
    # Some sites (e.g. tax.gov.ae) ship an empty <main>; fall back to the body.
    body = soup.body or soup
    if len(text) < 500 and root is not body:
        text = extract(body)
    return text


def pdf_to_text(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages).strip()


def latest_wayback_snapshot(client: httpx.Client, url: str) -> tuple[str, str] | None:
    """Return (timestamp, snapshot_fetch_url) of the newest HTTP-200 capture."""
    cdx = (
        "https://web.archive.org/cdx/search/cdx"
        f"?url={quote(url, safe='')}&output=json&fl=timestamp,original"
        "&filter=statuscode:200&limit=-1"
    )
    r = client.get(cdx, timeout=60)
    r.raise_for_status()
    rows = r.json()
    if len(rows) < 2:
        return None
    ts, original = rows[-1]
    return ts, f"https://web.archive.org/web/{ts}id_/{original}"


def fetch_source(client: httpx.Client, source: dict) -> dict:
    url = source["url"]
    record = {
        "key": source["key"],
        "jurisdiction": source["jurisdiction"],
        "title": source["title"],
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    is_wayback = any(d in httpx.URL(url).host for d in WAYBACK_DOMAINS)
    if is_wayback:
        snap = latest_wayback_snapshot(client, url)
        if snap is None:
            record.update(status="no_snapshot", method="wayback")
            return record
        ts, fetch_url = snap
        record.update(method="wayback", snapshot_timestamp=ts)
    else:
        fetch_url = url
        record["method"] = "direct"

    r = client.get(fetch_url, timeout=90)
    if r.status_code != 200:
        record.update(status=f"http_{r.status_code}")
        return record

    if url.lower().endswith(".pdf") or "pdf" in r.headers.get("content-type", ""):
        text = pdf_to_text(r.content)
        record["method"] = record.get("method", "direct") + "+pdf"
    else:
        text = html_to_text(r.text)

    # Some legitimate pages (e.g. IRS treaty-document indexes) are short link hubs.
    if len(text) < 300:
        record.update(status="too_short", chars=len(text))
        return record

    supplements = []
    for sub_url in SUPPLEMENTARY_PAGES.get(source["key"], []):
        try:
            if is_wayback:
                snap = latest_wayback_snapshot(client, sub_url)
                if snap is None:
                    continue
                sub_fetch = snap[1]
            else:
                sub_fetch = sub_url
            sr = client.get(sub_fetch, timeout=90)
            if sr.status_code != 200:
                continue
            sub_text = html_to_text(sr.text)
            if len(sub_text) >= 300:
                supplements.append(f"\n\n===== SUB-PAGE: {sub_url} =====\n{sub_text}")
        except Exception:
            continue
    if supplements:
        text += "".join(supplements)
        record["sub_pages"] = len(supplements)

    record.update(status="ok", chars=len(text))
    header = (
        f"SOURCE_KEY: {record['key']}\n"
        f"TITLE: {record['title']}\n"
        f"JURISDICTION: {record['jurisdiction']}\n"
        f"URL: {url}\n"
        f"METHOD: {record['method']}"
        + (f" (snapshot {record['snapshot_timestamp']})" if is_wayback else "")
        + f"\nFETCHED_AT: {record['fetched_at']}\n"
        + "-" * 78 + "\n"
    )
    (OUT_DIR / f"{record['key']}.txt").write_text(header + text, encoding="utf-8")
    return record


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    with httpx.Client(headers=UA, follow_redirects=True) as client:
        for source in SOURCE_FIXTURES:
            for attempt in (1, 2):
                try:
                    record = fetch_source(client, source)
                    break
                except Exception as exc:  # retry once on transient network errors
                    if attempt == 2:
                        record = {"key": source["key"], "url": source["url"],
                                  "status": f"error: {exc}"}
                    else:
                        time.sleep(3)
            manifest.append(record)
            print(f"{record.get('status', '?'):12s} {record['key']:24s} "
                  f"{record.get('chars', '')}")
            time.sleep(0.5)

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    ok = sum(1 for m in manifest if m.get("status") == "ok")
    print(f"\n{ok}/{len(manifest)} sources scraped successfully")


if __name__ == "__main__":
    main()

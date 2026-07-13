# Rule & Source Verification Report — 11 July 2026

Every knowledge-source URL and every rule in the seed fixtures was checked against the
live official pages. Nothing was invented; where a claim could not be located on an
accessible official page it was corrected to what the page actually says, or removed.

## Final state

- **60 knowledge sources** — all scraped successfully (`rag/scraped/manifest.json`)
- **98 rules** — all `verified_current`, each traceable to its scraped source page
- **2 rules removed** as unverifiable (see below)
- Vector DB: 98 rule documents + 1,119 source chunks across 60 pages (`rag/chroma_db/`)

## Broken source URLs fixed (page moved or never existed)

| Source | Problem | Fix |
|--------|---------|-----|
| AU_ATO_FRCGW | old "guide for conveyancers" path gone | current FRCGW section |
| AU_ATO_DEPARTURE | URL never existed (no archive record) | "How changing residency affects CGT" |
| AU_ATO_WHT | URL never existed | "Interest, unfranked dividends and royalties" |
| AU_ATO_DIV7A | old private-wealth path gone | current Div 7A section |
| AU_ATO_S99B | URL never existed | "Receiving payments or assets from foreign trusts" |
| AU_ATO_DASP | old super path gone | current DASP page |
| AU_ATO_FOREIGN_SUPER | old path gone | "Transfer from a foreign super fund" |
| AU_ATO_TEMP_RES | old path gone | "Foreign and temporary residents" |
| AU_FIRB | firb.gov.au retired | foreigninvestment.gov.au residential land guidance |
| SG_IRAS_FSIE | 404 | "Income received from overseas" |
| SG_IRAS_NOR | 404 | NOR scheme page under special tax schemes |
| SG_IRAS_AREA_REP | 404 | "I am working for a Foreign Employer" (Area Representative section) |
| UAE_FTA_SBR | mof.gov.ae path 404 | MoF Small Business Relief announcement |
| US_FINCEN_FBAR | JS-only filing portal, no content | FinCEN FBAR guidance page |
| SG_IRAS_CRS / UAE_ESR / UAE_DMTT | permanent redirects | updated to final URLs |

## New sources added (rules previously cited pages that don't cover them)

AU_ATO_CFC, AU_ATO_CRS, AU_ATO_NONRES_RATES, AU_ATO_TRUST_NONRES, AU_ATO_COMPANY_RES,
SG_IRAS_CORP, UAE_GOV_CT (u.ae corporate tax), UAE_FTA_VAT_REG, US_IRS_8938.
21 rules were re-pointed to the source that actually contains their content
(e.g. CFC rules were citing the individual-residency page; SG non-resident rates were
citing a hub page while the 15%/24% rates live on the income-tax-rates page).

## False factual claims corrected

- **AU_XB_003, UAE_XB_002** claimed an "Australia–UAE DTA signed November 2024".
  **No such treaty has been signed.** Rewritten to the verified fact: no AU-UAE DTA is
  in force (UAE absent from Treasury's income tax treaties table); consequences unchanged.
- **AU_XB_007, HK_XB_002** claimed an "Australia–Hong Kong DTA signed March 2024".
  **No such treaty has been signed** (only a TIEA exists). Rewritten the same way.
- **AU_TAX_007** cited an outdated HELP repayment threshold (AUD 54,435 for 2024-25);
  updated to the current ATO page (2025-26) and the rule condition adjusted.
- Unverifiable specifics trimmed from AU_TAX_005/006/009/012/014/015, AU_STR_002,
  SG_RES_004, US_TAX_003/007/012, UAE_TAX_003, UAE_STR_002, HK_TAX_007 — each now
  states only what its source page supports (penalty amounts, cross-state rate tables,
  illustrative dollar figures removed or generalised).

## Rules removed (unverifiable — do not re-add without a primary source)

- **HK_RES_001** — claimed a "180-day ordinary residence indicator" for HK Salaries Tax.
  No accessible IRD page supports it, and HK Salaries Tax is source-based, not
  residence-based.
- **UAE_TAX_005** — Dubai Land Department 4% transfer fee; cited the FTA VAT page which
  does not cover emirate land fees, and no accessible official page verified the schedule.

## Verification method

1. All URLs batch-checked (curl; Wayback CDX for the geo-blocked ato.gov.au domain).
2. Every page scraped to `rag/scraped/` (see README "RAG Pipeline").
3. Automated cross-check of each rule's factual anchors (day counts, rates, thresholds,
   dates) against its own source's scraped text, then manual review of every flag.
4. Remaining unmatched tokens are statutory citations only (e.g. "s. 104-160 ITAA 1997",
   "IRC §911") — legal references that plain-language guidance pages do not repeat.

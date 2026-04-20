"""Knowledge source fixtures for the ClearPath seeding pipeline."""
from app.models.knowledge_source import SourceType

# ── Knowledge Sources ─────────────────────────────────────────────────────────
# Each entry has a unique "key" used by RULE_FIXTURES to reference its source_id.
SOURCE_FIXTURES = [
    # ── Australia ─────────────────────────────────────────────────────────────
    {
        "key": "AU_ATO_RESIDENCY",
        "jurisdiction": "AU",
        "title": "ATO — Tax residency guidance for individuals",
        "url": "https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/your-tax-residency/australian-resident-for-tax-purposes",
        "source_type": SourceType.government_guidance,
    },
    {
        "key": "AU_ATO_CGT",
        "jurisdiction": "AU",
        "title": "ATO — Foreign residents and capital gains tax",
        "url": "https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/foreign-residents-and-capital-gains-tax",
        "source_type": SourceType.government_guidance,
    },
    # ── Singapore ─────────────────────────────────────────────────────────────
    {
        "key": "SG_IRAS_RESIDENCY",
        "jurisdiction": "SG",
        "title": "IRAS — Tax residency and tax rates for individuals",
        "url": "https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/tax-residency-and-tax-rates/working-out-my-tax-residency",
        "source_type": SourceType.government_guidance,
    },
    {
        "key": "SG_IRAS_NONRESIDENT",
        "jurisdiction": "SG",
        "title": "IRAS — Tax obligations for non-resident individuals",
        "url": "https://www.iras.gov.sg/taxes/individual-income-tax/non-residents",
        "source_type": SourceType.government_guidance,
    },
    # ── Hong Kong ─────────────────────────────────────────────────────────────
    {
        "key": "HK_IRD_SALARIES",
        "jurisdiction": "HK",
        "title": "IRD Hong Kong — Salaries Tax guidance",
        "url": "https://www.ird.gov.hk/eng/tax/ind.htm",
        "source_type": SourceType.government_guidance,
    },
    {
        "key": "HK_IRD_PROFITS",
        "jurisdiction": "HK",
        "title": "IRD Hong Kong — Profits Tax and territorial source principle",
        "url": "https://www.ird.gov.hk/eng/tax/bus.htm",
        "source_type": SourceType.government_guidance,
    },
    # ── UAE ───────────────────────────────────────────────────────────────────
    {
        "key": "UAE_FTA_RESIDENCY",
        "jurisdiction": "UAE",
        "title": "UAE Federal Tax Authority — Tax residency certificate guidance",
        "url": "https://tax.gov.ae/en/services/issuance.of.tax.certificates.aspx",
        "source_type": SourceType.government_guidance,
    },
    {
        "key": "UAE_FTA_CORPORATE",
        "jurisdiction": "UAE",
        "title": "UAE Federal Tax Authority — Corporate Tax guidance (effective June 2023)",
        "url": "https://tax.gov.ae/en/taxes/corporate.tax.aspx",
        "source_type": SourceType.legislation,
    },
    # ── United States ─────────────────────────────────────────────────────────
    {
        "key": "US_IRS_INTERNATIONAL",
        "jurisdiction": "US",
        "title": "IRS — Publication 54: Tax Guide for U.S. Citizens and Resident Aliens Abroad",
        "url": "https://www.irs.gov/publications/p54",
        "source_type": SourceType.government_guidance,
    },
    {
        "key": "US_FINCEN_FBAR",
        "jurisdiction": "US",
        "title": "FinCEN — FBAR filing requirements (FinCEN 114)",
        "url": "https://bsaefiling.fincen.gov/file/fbar",
        "source_type": SourceType.government_guidance,
    },
    {
        "key": "US_IRS_PFIC",
        "jurisdiction": "US",
        "title": "IRS — Passive Foreign Investment Company (PFIC) guidance",
        "url": "https://www.irs.gov/instructions/i8621",
        "source_type": SourceType.government_guidance,
    },
]

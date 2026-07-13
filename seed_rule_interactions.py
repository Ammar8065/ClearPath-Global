"""Curated rule-interaction fixtures for the ClearPath seeding pipeline.

Each entry captures a genuine, source-grounded relationship between two
rules that can legitimately trigger together, where one changes what the
other's finding actually means in practice. Every note below paraphrases
only what is already stated in the two rules' own (fact-checked)
descriptions in seed_rules.py — nothing here introduces a claim that isn't
already backed by the legislation those rules cite.

Two types (see app.models.rule_interaction.InteractionType):
    relief     the related rule is an election the client can make that
               reduces or eliminates the primary rule's exposure.
    exception  the related rule's own facts are an automatic carve-out from
               the primary rule — no election needed.

primary_rule_code / related_rule_code reference rule_code, not a specific
version — the relationship is conceptual and should hold across versions.
"""
from app.models.rule_interaction import InteractionType

RULE_INTERACTION_FIXTURES = [
    # ── UAE ──────────────────────────────────────────────────────────────────
    {
        "primary_rule_code": "UAE_TAX_001",
        "related_rule_code": "UAE_TAX_002",
        "interaction_type": InteractionType.relief,
        "note": (
            "UAE_TAX_002's Small Business Relief lets a Taxable Person with revenue ≤ AED 3M elect to be "
            "treated as having no taxable income for the period — if elected, this reduces UAE_TAX_001's "
            "9% Corporate Tax liability to nil for that tax period. The election is not automatic and must "
            "be made on the CT return; confirm the client's revenue and entity type (QFZP-electing and MNE "
            "constituents are excluded) before assuming it is available."
        ),
    },
    {
        "primary_rule_code": "UAE_TAX_001",
        "related_rule_code": "UAE_TAX_006",
        "interaction_type": InteractionType.exception,
        "note": (
            "UAE_TAX_006 shows the client is a Qualifying Free Zone Person earning only Qualifying Income — "
            "that status carries a 0% Corporate Tax rate on that income, which is an exception to UAE_TAX_001's "
            "standard 9% rate. Confirm QFZP status and substance requirements are genuinely maintained before "
            "relying on UAE_TAX_001's exposure figure for this entity."
        ),
    },
    # ── Hong Kong ────────────────────────────────────────────────────────────
    {
        "primary_rule_code": "HK_TAX_001",
        "related_rule_code": "HK_RES_002",
        "interaction_type": InteractionType.exception,
        "note": (
            "HK_RES_002's 60-day visitor exemption (s. 8(1B) IRO) is an automatic carve-out from HK_TAX_001's "
            "general territorial Salaries Tax charge — if the client was in Hong Kong for 60 days or fewer in "
            "the year of assessment, the income HK_TAX_001 flags may in fact be exempt. Verify the day count "
            "precisely (arrival and departure days both count) before treating HK_TAX_001 as the final position."
        ),
    },
    {
        "primary_rule_code": "HK_TAX_001",
        "related_rule_code": "HK_TAX_003",
        "interaction_type": InteractionType.exception,
        "note": (
            "HK_TAX_003 shows the client's employment is non-Hong Kong with services only partly rendered in "
            "HK — time-apportionment applies, so only the HK-workday share of the income HK_TAX_001 flags is "
            "actually assessable; income attributable to non-HK workdays is exempt. HK_TAX_001's finding should "
            "be read as the apportioned HK-workday amount, not the full income figure."
        ),
    },
    # ── Singapore ────────────────────────────────────────────────────────────
    {
        "primary_rule_code": "SG_TAX_001",
        "related_rule_code": "SG_TAX_009",
        "interaction_type": InteractionType.exception,
        "note": (
            "SG_TAX_009's 60-day short-term employment exemption is an automatic carve-out from SG_TAX_001's "
            "non-resident withholding — if the client was in Singapore under 61 days, the employment income "
            "SG_TAX_001 flags is generally exempt. This exception does NOT extend to director's fees, public "
            "entertainer income, or professional/consultancy fees, which remain taxable regardless of day count."
        ),
    },
    # ── United States ────────────────────────────────────────────────────────
    {
        "primary_rule_code": "US_RES_001",
        "related_rule_code": "US_RES_002",
        "interaction_type": InteractionType.exception,
        "note": (
            "US_RES_002 shows the client is claiming the Closer Connection Exception (Form 8840) — if the "
            "conditions are genuinely met (tax home and closer connection to a foreign country, current-year "
            "presence under 183 days, timely filing), the client can remain a non-resident alien despite "
            "meeting the Substantial Presence Test flagged by US_RES_001. This exception is unavailable if a "
            "green card application is pending or in the year of green card issue."
        ),
    },
    {
        "primary_rule_code": "US_RES_001",
        "related_rule_code": "US_RES_003",
        "interaction_type": InteractionType.exception,
        "note": (
            "US_RES_003 shows a treaty tie-breaker position is being claimed against US_RES_001's Substantial "
            "Presence Test finding. For a non-US-citizen this can establish non-US residency; for a US citizen "
            "it does NOT — the Saving Clause (Art 1(3)) preserves the US right to tax citizens regardless of "
            "the tie-breaker, so it only unlocks specific treaty benefits (FTC ordering, source-rule "
            "modifications, reduced withholding), not exemption from US_RES_001's residency-based taxation."
        ),
    },
    {
        "primary_rule_code": "US_TAX_004",
        "related_rule_code": "US_TAX_010",
        "interaction_type": InteractionType.relief,
        "note": (
            "US_TAX_010 shows a QEF or Mark-to-Market election has been made — if made in the first year of "
            "PFIC ownership, this election supersedes the punitive default 'excess distribution' regime "
            "US_TAX_004 flags under Section 1291. A late election leaves a Section 1291 'tail' from prior "
            "years, so US_TAX_004's exposure may still apply to earlier holding periods even where the "
            "election is now in place."
        ),
    },
]

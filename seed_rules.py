"""Rule fixtures + condition helpers for the ClearPath seeding pipeline."""
from datetime import date

from app.models.rule import ConfidenceLevel, ReviewStatus, RiskLevel, RuleCategory

# ── Helpers ───────────────────────────────────────────────────────────────────
def simple_condition(field: str, operator: str, value: str | int | bool) -> dict:
    return {"field": field, "operator": operator, "value": value}


def all_conditions(*conditions: dict) -> dict:
    return {"all": list(conditions)}


def any_conditions(*conditions: dict) -> dict:
    return {"any": list(conditions)}

# ── Rules ─────────────────────────────────────────────────────────────────────
# Each entry references its source via "source_key" matching a SOURCE_FIXTURES key.
RULE_FIXTURES = [

    # ── Australia ─────────────────────────────────────────────────────────────
    {
        "rule_code": "AU_RES_001",
        "jurisdiction": "AU",
        "category": RuleCategory.residency,
        "condition_expression": simple_condition("days_in_country", ">=", 183),
        "description": (
            "Physical presence in Australia for 183 days or more in a tax year is a primary trigger "
            "under the statutory '183-day test'. This is one of the most commonly applied residency tests "
            "for Australian expats and returning individuals."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 995-1 ITAA 1997 — 183-day test",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_RES_002",
        "jurisdiction": "AU",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("domicile_country", "==", "AU"),
            simple_condition("permanent_abode_outside_country", "==", False),
        ),
        "description": (
            "An individual with an Australian domicile who has not established a permanent place of abode "
            "outside Australia is treated as an Australian tax resident under the domicile test. This is a "
            "critical risk for Australian expats who have not formally severed their domicile."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 6(1)(a)(i) ITAA 1936 — domicile test",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_RES_003",
        "jurisdiction": "AU",
        "category": RuleCategory.residency,
        "condition_expression": simple_condition("strong_personal_economic_ties_in_country", "==", True),
        "description": (
            "Under the 'ordinary resides' concept, strong personal, economic, or employment ties to "
            "Australia — such as maintaining a family home, ongoing employment, or significant financial "
            "interests — may indicate continuing Australian tax residency regardless of physical absence."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 6(1) ITAA 1936 — 'resides' test (ordinary resides concept)",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_TAX_001",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("australian_source_income", ">", 0),
        ),
        "description": (
            "Australian non-residents with Australian-source income — including rent from Australian "
            "property, dividends from Australian companies, and interest from Australian bank accounts — "
            "remain subject to Australian withholding tax and income tax obligations. "
            "Non-resident tax rates apply from the first dollar of income with no tax-free threshold."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 6-5(3) ITAA 1997 — non-resident assessable income",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_TAX_002",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("australian_property_owned", "==", True),
        ),
        "description": (
            "Since 1 July 2020, Australian non-residents are no longer eligible for the main residence "
            "CGT exemption when selling Australian residential property. This is one of the most commonly "
            "overlooked tax exposures for Australian expats who retain their former home. The full capital "
            "gain is taxable at non-resident rates with no 50% CGT discount available."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 118-110 ITAA 1997 — main residence exemption excluded for non-residents",
        "review_status": ReviewStatus.needs_update,
        "source_key": "AU_ATO_CGT",
    },
    {
        "rule_code": "AU_XB_001",
        "jurisdiction": "AU",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("dual_tax_residency", "==", True),
            simple_condition("treaty_relief_claimed", "==", False),
        ),
        "description": (
            "An individual who is treated as a tax resident in both Australia and another jurisdiction "
            "without invoking applicable treaty tie-breaker provisions faces unresolved taxing rights. "
            "Both jurisdictions may assert full taxation rights, creating the risk of double taxation "
            "on worldwide income."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Art. 4 Model DTA — tie-breaker for dual residents",
        "source_key": "AU_ATO_RESIDENCY",
    },

    # ── Singapore ─────────────────────────────────────────────────────────────
    {
        "rule_code": "SG_RES_001",
        "jurisdiction": "SG",
        "category": RuleCategory.residency,
        "condition_expression": simple_condition("days_in_country", ">=", 183),
        "description": (
            "A foreigner who is physically present or employed in Singapore for 183 days or more in a "
            "calendar year is treated as a Singapore tax resident. This is the primary residency test "
            "applied by IRAS and is the most common trigger for Australian expats relocating to Singapore."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 2(1) ITA (Singapore) — definition of 'resident individual'",
        "source_key": "SG_IRAS_RESIDENCY",
    },
    {
        "rule_code": "SG_RES_002",
        "jurisdiction": "SG",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("employment_straddles_two_years", "==", True),
            simple_condition("total_days_in_country", ">=", 183),
        ),
        "description": (
            "Under IRAS concession rules, a foreigner whose employment period straddles two calendar "
            "years — with at least 183 total days of presence across both years — may be treated as a "
            "tax resident for both years. This commonly applies to mid-year arrivals and is a frequently "
            "missed residency trigger."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "IRAS e-Tax Guide: Tax Residency of Individuals (administrative concession)",
        "source_key": "SG_IRAS_RESIDENCY",
    },
    {
        "rule_code": "SG_TAX_001",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("singapore_source_income", ">", 0),
        ),
        "description": (
            "Singapore non-residents with Singapore-source employment income are subject to a flat "
            "withholding tax rate of 15% (or the resident rate if higher) with no personal reliefs. "
            "Director's fees and other income types attract a flat 24% rate. "
            "Non-resident tax treatment is materially more costly than the resident progressive scale."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 45 ITA (Singapore) — withholding tax on non-resident income",
        "source_key": "SG_IRAS_NONRESIDENT",
    },
    {
        "rule_code": "SG_TAX_002",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("sg_director_fees", ">", 0),
        ),
        "description": (
            "Director's fees paid by a Singapore company to a non-resident director are subject to a "
            "flat 24% Singapore withholding tax. The company is obligated to withhold and remit. "
            "This applies regardless of whether the individual attends board meetings in Singapore "
            "and is a commonly overlooked obligation for non-resident directors of Singapore-incorporated entities."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 45A ITA (Singapore) — withholding on director's fees",
        "source_key": "SG_IRAS_NONRESIDENT",
    },
    {
        "rule_code": "SG_STR_001",
        "jurisdiction": "SG",
        "category": RuleCategory.structure,
        "condition_expression": all_conditions(
            simple_condition("sg_company_owned", "==", True),
            simple_condition("residency_country", "==", "AU"),
        ),
        "description": (
            "An Australian tax resident who owns or controls a Singapore-incorporated company may be "
            "subject to Australian Controlled Foreign Company (CFC) attribution rules under Division 9A "
            "of the ITAA 1936. If the Singapore entity earns passive income or income from an associated "
            "party, that income may be attributed to and taxable in Australia regardless of whether "
            "it is distributed."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Div 9A ITAA 1936 — controlled foreign companies (CFC attribution)",
        "review_status": ReviewStatus.unsupported_or_wrong_source,
        "source_key": "AU_ATO_RESIDENCY",
    },

    # ── Hong Kong ─────────────────────────────────────────────────────────────
    {
        "rule_code": "HK_RES_001",
        "jurisdiction": "HK",
        "category": RuleCategory.residency,
        "condition_expression": simple_condition("days_in_country", ">=", 180),
        "description": (
            "Hong Kong does not have a formal statutory day-count residency rule, but physical presence "
            "of 180 days or more in a tax year (April to March) is an established indicator of 'ordinary "
            "residence' under the Inland Revenue Ordinance. Ordinary residents are liable for Salaries "
            "Tax on Hong Kong-sourced employment income and may face broader review."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 8(1A)(b) IRO (Hong Kong) — ordinary residence indicator",
        "review_status": ReviewStatus.needs_update,
        "source_key": "HK_IRD_SALARIES",
    },
    {
        "rule_code": "HK_TAX_001",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("hong_kong_source_income", ">", 0),
        "description": (
            "Hong Kong applies a strict territorial basis of taxation. Employment income arising from "
            "services rendered in Hong Kong is subject to Salaries Tax regardless of residency status. "
            "This applies even to short-term business visitors rendering services in Hong Kong, and is "
            "a commonly overlooked obligation for executives and advisors making regular visits."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 8(1) IRO (Hong Kong) — charge to Salaries Tax",
        "source_key": "HK_IRD_SALARIES",
    },
    {
        "rule_code": "HK_TAX_002",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("employer_provided_benefits_hk", "==", True),
        "description": (
            "Employer-provided benefits received by employees working in Hong Kong — including housing "
            "allowances, club memberships, share-based awards, and other non-cash remuneration — "
            "are assessable to Salaries Tax under the Inland Revenue Ordinance. Housing benefits are "
            "commonly structured to reduce Salaries Tax liability, but require careful arrangement to "
            "achieve the intended outcome."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 9(1) IRO (Hong Kong) — income from employment including benefits in kind",
        "source_key": "HK_IRD_SALARIES",
    },
    {
        "rule_code": "HK_STR_001",
        "jurisdiction": "HK",
        "category": RuleCategory.structure,
        "condition_expression": all_conditions(
            simple_condition("hk_company_owned", "==", True),
            simple_condition("tax_residency_status", "==", "non_resident"),
        ),
        "description": (
            "A non-resident who owns or operates a Hong Kong company deriving profits from Hong Kong "
            "is subject to Profits Tax at 16.5% (8.25% on first HKD 2M). The territorial principle "
            "means that profits genuinely sourced outside Hong Kong may be exempt, but the sourcing "
            "analysis is fact-sensitive and commonly disputed. Non-resident ownership does not "
            "automatically remove Hong Kong Profits Tax exposure."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 14(1) IRO (Hong Kong) — charge to Profits Tax",
        "source_key": "HK_IRD_PROFITS",
    },
    {
        "rule_code": "HK_XB_001",
        "jurisdiction": "HK",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("hk_company_owned", "==", True),
            simple_condition("residency_country", "==", "AU"),
        ),
        "description": (
            "An Australian tax resident who owns or controls a Hong Kong private company may be subject "
            "to Australian CFC attribution rules if the entity earns passive or related-party income. "
            "Additionally, Australian Transfer Pricing rules under Subdivision 815 may apply where "
            "dealings exist between the Australian resident and the Hong Kong entity. Both exposures "
            "require review where the structure is in place."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Div 9A ITAA 1936 — CFC; Subdiv 815-B ITAA 1997 — transfer pricing",
        "review_status": ReviewStatus.unsupported_or_wrong_source,
        "source_key": "AU_ATO_RESIDENCY",
    },

    # ── UAE ───────────────────────────────────────────────────────────────────
    {
        "rule_code": "UAE_RES_001",
        "jurisdiction": "UAE",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("days_in_country", ">=", 183),
            simple_condition("tax_residency_certificate_requested", "==", True),
        ),
        "description": (
            "Physical presence in the UAE for 183 days or more in a 12-month period is the primary "
            "basis for obtaining a UAE Tax Residency Certificate (TRC) from the Federal Tax Authority. "
            "A valid TRC is required to access treaty benefits and to substantiate UAE tax residency "
            "in the eyes of foreign tax authorities, including the ATO."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Cabinet Decision No. 85 of 2022, Art. 3 — 183-day residency test",
        "source_key": "UAE_FTA_RESIDENCY",
    },
    {
        "rule_code": "UAE_RES_002",
        "jurisdiction": "UAE",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("days_in_country", ">=", 90),
            simple_condition("has_other_tax_residency", "==", False),
        ),
        "description": (
            "Under UAE Cabinet Decision No. 85 of 2022 (effective March 2023), an individual who "
            "spends 90 days or more in the UAE in a 12-month period AND has no tax residency in any "
            "other country is deemed a UAE tax resident. This is a critical trap for Australian expats "
            "who have ceased Australian residency but spend significant time in the UAE without "
            "establishing residency elsewhere — they may default to UAE residency obligations."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 3, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Cabinet Decision No. 85 of 2022, Art. 4 — 90-day deemed residency",
        "review_status": ReviewStatus.needs_update,
        "source_key": "UAE_FTA_RESIDENCY",
    },
    {
        "rule_code": "UAE_TAX_001",
        "jurisdiction": "UAE",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("uae_business_owned", "==", True),
            simple_condition("uae_taxable_income", ">", 375000),
        ),
        "description": (
            "The UAE introduced Federal Corporate Tax (CT) effective for financial years starting on "
            "or after 1 June 2023. A 9% rate applies to taxable income exceeding AED 375,000 (~USD 102k). "
            "This is a significant new development for HNW individuals who own or operate UAE businesses "
            "through mainland or non-qualifying freezone structures. Prior to June 2023, corporate-level "
            "income tax was effectively zero."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 6, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Federal Decree-Law No. 47 of 2022, Art. 3 — corporate tax rate 9%",
        "source_key": "UAE_FTA_CORPORATE",
    },
    {
        "rule_code": "UAE_STR_001",
        "jurisdiction": "UAE",
        "category": RuleCategory.structure,
        "condition_expression": all_conditions(
            simple_condition("uae_freezone_entity", "==", True),
            simple_condition("uae_non_qualifying_income", ">", 0),
        ),
        "description": (
            "UAE Freezone entities may qualify for a 0% Corporate Tax rate on 'Qualifying Income' "
            "provided they meet substance requirements and do not earn Excluded Income. Where a "
            "Freezone entity earns non-qualifying income — including income from UAE mainland operations "
            "or dealings with domestic-related parties — the entire entity may lose Qualifying Freezone "
            "Person status and become subject to the standard 9% CT rate on all income."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 6, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Ministerial Decision No. 139 of 2023 — qualifying income for Freezone persons",
        "review_status": ReviewStatus.needs_update,
        "source_key": "UAE_FTA_CORPORATE",
    },
    {
        "rule_code": "UAE_XB_001",
        "jurisdiction": "UAE",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "UAE"),
            simple_condition("treaty_relief_claimed", "==", True),
            simple_condition("tax_residency_certificate", "==", False),
        ),
        "description": (
            "Claiming double tax treaty benefits from a UAE position — including reduced withholding "
            "tax rates on Australian dividends, interest, or royalties — requires a valid UAE Tax "
            "Residency Certificate as supporting documentation. Without it, the ATO or other foreign "
            "authorities may deny treaty relief and apply domestic withholding rates retroactively."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Cabinet Decision No. 85 of 2022, Art. 6 — TRC required for treaty access",
        "source_key": "UAE_FTA_RESIDENCY",
    },

    # ── United States ─────────────────────────────────────────────────────────
    {
        "rule_code": "US_RES_001",
        "jurisdiction": "US",
        "category": RuleCategory.residency,
        "condition_expression": simple_condition("us_substantial_presence_days", ">=", 183),
        "description": (
            "The US Substantial Presence Test (SPT) deems a non-US-citizen a US tax resident if they "
            "are present in the US for 183 days or more when calculated as: all days in the current "
            "year + 1/3 of days in the prior year + 1/6 of days two years prior. This catches "
            "Australian expats who make frequent business trips to the US without tracking cumulative "
            "presence. US tax residency under SPT triggers worldwide income taxation."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 7701(b)(3) — substantial presence test",
        "source_key": "US_IRS_INTERNATIONAL",
    },
    {
        "rule_code": "US_TAX_001",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("citizenship", "==", "US"),
        "description": (
            "The United States taxes its citizens on worldwide income regardless of where they live "
            "or where their income is sourced — a system unique among major economies. US citizens "
            "living in Australia (or any other country) remain obligated to file US federal tax returns "
            "annually. This is the single most significant and commonly overlooked US tax exposure "
            "for Australian expats with US citizenship or dual citizenship."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 61 — worldwide income for US citizens",
        "source_key": "US_IRS_INTERNATIONAL",
    },
    {
        "rule_code": "US_TAX_002",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("foreign_source_income", ">", 0),
        ),
        "description": (
            "US citizens with foreign-source income remain subject to US federal income tax on that "
            "income. While the Foreign Earned Income Exclusion (FEIE) and Foreign Tax Credit (FTC) "
            "may reduce the effective US tax liability, they must be proactively claimed on Form 2555 "
            "and Form 1116 respectively. Failure to file or claim reliefs correctly creates significant "
            "underpayment and penalty risk."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. §§ 911, 901 — FEIE (Form 2555) and Foreign Tax Credit (Form 1116)",
        "source_key": "US_IRS_INTERNATIONAL",
    },
    {
        "rule_code": "US_TAX_003",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("foreign_financial_accounts_balance", ">", 10000),
        ),
        "description": (
            "US persons with an aggregate balance exceeding USD 10,000 in foreign financial accounts "
            "at any point during the calendar year must file FinCEN Form 114 (FBAR) by 15 April. "
            "Failure to file carries civil penalties of up to USD 10,000 per non-wilful violation "
            "and up to USD 100,000 (or 50% of account balance) per wilful violation. "
            "This is one of the most commonly unmet obligations for US citizens living in Australia."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "31 CFR § 1010.350 — FBAR filing requirement (FinCEN Form 114)",
        "review_status": ReviewStatus.needs_update,
        "source_key": "US_FINCEN_FBAR",
    },
    {
        "rule_code": "US_TAX_004",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("pfic_holdings", "==", True),
        ),
        "description": (
            "US citizens holding interests in Passive Foreign Investment Companies (PFICs) — which "
            "include Australian managed funds, ETFs, and most foreign unit trusts — face punitive US "
            "tax treatment under the default 'excess distribution' regime (Section 1291). This "
            "includes interest charges on deferred gains dating back to the acquisition year. "
            "Australian superannuation funds held by US citizens carry separate PFIC and FBAR "
            "reporting requirements and are one of the most complex US cross-border issues for "
            "Australian-American dual residents."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 1291 — PFIC excess distribution regime (Form 8621)",
        "source_key": "US_IRS_PFIC",
    },

    # ── Australia (extended set for AU expat focus) ────────────────────────────
    {
        "rule_code": "AU_RES_004",
        "jurisdiction": "AU",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("strong_personal_economic_ties_in_country", "==", True),
        ),
        "description": (
            "An individual claiming non-resident status while retaining strong personal or economic "
            "ties to Australia (family home, business, AU employer, social/sporting club affiliation) "
            "remains exposed to ATO challenge under the 'resides' test. The ATO's TR 2023/1 emphasises "
            "that residency is a continuing fact-based analysis and the ATO scrutinises retained ties "
            "even where the day-count test is failed. Documentation of ties severed is essential."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "TR 2023/1 — Residency tests for individuals (replaces TR 98/17)",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_RES_005",
        "jurisdiction": "AU",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("eligible_commonwealth_superannuation_member", "==", True),
            simple_condition("tax_residency_status", "!=", "non_resident"),
        ),
        "description": (
            "The Commonwealth superannuation test deems members (and their spouses and children) of "
            "the CSS or PSS schemes to be Australian tax residents irrespective of physical absence. "
            "This catches former Commonwealth public servants and Defence Force personnel who relocate "
            "overseas — they remain Australian tax residents on worldwide income unless they exit the "
            "Commonwealth super arrangements entirely."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 6(1)(a)(iii) ITAA 1936 — Commonwealth superannuation test",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_RES_006",
        "jurisdiction": "AU",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("non_tarp_assets_held", "==", True),
            simple_condition("i1_deferral_election", "==", False),
        ),
        "description": (
            "Ceasing to be an Australian tax resident triggers CGT Event I1 — a deemed disposal of "
            "all non-TARP CGT assets (typically foreign property, foreign shares, and AU-listed "
            "shares not held through a PE) at market value on the departure date. Without a "
            "Subdivision 104-I deferral election, an immediate CGT liability arises with no actual "
            "sale proceeds. The deferral election keeps the assets in the AU CGT net but defers the "
            "tax point to actual disposal — each path has materially different downstream implications."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 104-160 ITAA 1997 — CGT Event I1 (individual ceases AU residency)",
        "source_key": "AU_ATO_DEPARTURE",
    },
    {
        "rule_code": "AU_RES_007",
        "jurisdiction": "AU",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("non_tarp_assets_held", "==", True),
            simple_condition("i1_deferral_election", "==", True),
            simple_condition("tax_residency_status", "==", "non_resident"),
        ),
        "description": (
            "Where a Subdivision 104-I election is made to defer CGT Event I1, the affected non-TARP "
            "assets are deemed Taxable Australian Property (TAP) until actual disposal or until "
            "Australian residency is resumed. Australian CGT continues to apply to any future gain "
            "on those assets at non-resident rates with no 50% CGT discount, and FRCGW rules can "
            "apply on later sale. The election trades immediate liquidity for ongoing AU tax exposure."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 104-165 ITAA 1997 — election to disregard CGT Event I1",
        "source_key": "AU_ATO_DEPARTURE",
    },
    {
        "rule_code": "AU_RES_008",
        "jurisdiction": "AU",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "AU"),
            simple_condition("permanent_abode_outside_country", "==", False),
            simple_condition("days_in_country", "<", 183),
        ),
        "description": (
            "Returning Australian residents who re-establish AU residency reset the cost base of "
            "previously held non-TARP foreign assets to market value on the resumption date "
            "(s. 855-45). This typically benefits clients holding appreciated foreign assets — but "
            "the cost-base reset is automatic and should be documented contemporaneously to support "
            "any subsequent CGT calculation."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 855-45 ITAA 1997 — cost base reset on resuming AU residency",
        "source_key": "AU_ATO_DEPARTURE",
    },
    {
        "rule_code": "AU_TAX_003",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("australian_property_being_sold", "==", True),
        ),
        "description": (
            "The Foreign Resident Capital Gains Withholding (FRCGW) regime requires the purchaser of "
            "Taxable Australian Real Property from a foreign resident to withhold and remit a portion "
            "of the contract price to the ATO at settlement. From 1 January 2025 the rate is 15% with "
            "no minimum threshold — every disposal is in scope. A vendor's clearance certificate (where "
            "available) avoids withholding. Without it, 15% of the gross contract price flows to the ATO."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Subdiv 14-D Sch 1 TAA 1953 — FRCGW (15%, $0 threshold from 1 Jan 2025)",
        "source_key": "AU_ATO_FRCGW",
    },
    {
        "rule_code": "AU_TAX_004",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("australian_source_income", ">", 0),
            simple_condition("treaty_relief_claimed", "==", False),
        ),
        "description": (
            "Australian-source interest paid to a non-resident is generally subject to a 10% final "
            "Interest Withholding Tax (IWT). Unfranked dividends attract 30% Dividend WHT and royalties "
            "attract 30% Royalty WHT. Where a tax treaty applies, reduced rates (commonly 15% on "
            "dividends, 10% on royalties) may be claimed — but only if treaty entitlement is claimed "
            "and substantiated. Absence of a treaty (e.g. AU-UAE pre-DTA) leaves the full domestic "
            "rates in place."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Div 11A ITAA 1936 — non-resident WHT on interest, dividends, royalties",
        "source_key": "AU_ATO_WHT",
    },
    {
        "rule_code": "AU_TAX_005",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("foreign_purchaser_property_purchase", "==", True),
            simple_condition("firb_approval_obtained", "==", False),
        ),
        "description": (
            "Foreign persons (including AU citizens ordinarily resident overseas in some cases) "
            "must obtain FIRB approval BEFORE acquiring an interest in Australian residential real "
            "estate. Acquiring without approval triggers civil penalties up to AUD 1.65M for "
            "individuals, divestment orders, and criminal exposure. Established dwellings are "
            "generally not available to foreign persons; only new dwellings, off-the-plan purchases "
            "and vacant land for redevelopment are typically permissible."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Foreign Acquisitions and Takeovers Act 1975 — FIRB approval requirement",
        "source_key": "AU_FIRB",
    },
    {
        "rule_code": "AU_TAX_006",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("foreign_purchaser_property_purchase", "==", True),
        "description": (
            "States impose substantial 'Surcharge Purchaser Duty' on foreign buyers of residential "
            "property — currently 8% in NSW, 8% in Victoria, 7% in Queensland, 7% in WA, in addition "
            "to standard transfer duty. Foreign owners also pay annual Land Tax surcharges "
            "(NSW 5%, VIC 4% absentee owner surcharge, QLD 3%). For a $2M residential purchase the "
            "combined duty surcharge alone exceeds $150,000 above resident rates."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Duties Act 1997 (NSW) Ch 2A — surcharge purchaser duty (8%)",
        "source_key": "AU_NSW_DUTY",
    },
    {
        "rule_code": "AU_TAX_007",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("au_help_debt", "==", True),
            simple_condition("worldwide_income", ">=", 54435),
        ),
        "description": (
            "Australians with HELP, VSL, TSL, or SFSS debts living overseas must report worldwide "
            "income annually and make compulsory repayments once worldwide income exceeds the "
            "minimum repayment threshold (AUD 54,435 for 2024-25). Repayment rates scale to 10% at "
            "the highest income brackets. Failure to lodge or report carries penalties and interest, "
            "and ATO has data-sharing arrangements with foreign tax authorities to identify "
            "non-reporters."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Higher Education Support Act 2003, Part 4 — overseas worldwide-income reporting",
        "review_status": ReviewStatus.needs_update,
        "source_key": "AU_ATO_HELP",
    },
    {
        "rule_code": "AU_TAX_008",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("private_health_insurance_held", "==", False),
            simple_condition("worldwide_income", ">=", 97000),
        ),
        "description": (
            "Australian residents without eligible private hospital cover whose income exceeds the "
            "MLS threshold (AUD 97,000 single / 194,000 family for 2024-25) pay the Medicare Levy "
            "Surcharge of 1.0%-1.5% on top of the standard 2% Medicare Levy. Returning expats often "
            "trigger MLS in their first AU year if hospital cover is not in place from arrival — "
            "the surcharge is calculated pro-rata only for the days uninsured."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Medicare Levy Act 1986, Part VIIB — Medicare Levy Surcharge",
        "review_status": ReviewStatus.needs_update,
        "source_key": "AU_ATO_MEDICARE",
    },
    {
        "rule_code": "AU_TAX_009",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("foreign_trust_distribution_received", "==", True),
        ),
        "description": (
            "Distributions of accumulated income or capital from a non-resident discretionary trust "
            "to an Australian resident beneficiary are fully assessable under s. 99B at marginal "
            "rates (up to 47%) with NO 50% CGT discount available. Section 99B catches the entire "
            "distribution unless an exception applies (e.g. previously taxed income, corpus). This "
            "is a critical exposure for AU expats returning home with offshore family-trust "
            "structures established while overseas."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 99B ITAA 1936 — distributions from non-resident trusts",
        "source_key": "AU_ATO_S99B",
    },
    {
        "rule_code": "AU_TAX_010",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("super_lump_sum_received", "==", True),
        ),
        "description": (
            "Australian residents receiving a lump sum from a foreign superannuation fund must "
            "include the 'Applicable Fund Earnings' (AFE) — broadly, the growth in the fund since "
            "AU residency commenced — in assessable income at marginal rates. A six-month grace "
            "period applies after first becoming an AU resident; earnings during that window can "
            "be excluded. Beyond six months, AFE accrues even if not transferred. Election to have "
            "AFE taxed in the fund (s. 305-80) is available in limited cases and requires careful "
            "modelling."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Subdiv 305-B ITAA 1997 — foreign super applicable fund earnings",
        "source_key": "AU_ATO_FOREIGN_SUPER",
    },
    {
        "rule_code": "AU_TAX_011",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("dasp_eligible", "==", True),
        "description": (
            "Former temporary residents of Australia leaving permanently can claim a Departing "
            "Australia Superannuation Payment (DASP) but face punitive withholding rates: 35% on "
            "tax-free and taxable (taxed) elements, and 45% on the taxable (untaxed) element. "
            "Working Holiday Maker visa-holders face an even harsher 65% rate on all components. "
            "Once superannuation is paid as DASP it is permanently outside the AU concessional "
            "system; alternatives (preserving the balance, rolling to a foreign fund) should be "
            "considered first."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 301-170 ITAA 1997; ITRR 2021 — DASP withholding (35%/45%/65%)",
        "source_key": "AU_ATO_DASP",
    },
    {
        "rule_code": "AU_TAX_012",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("temp_resident_status", "==", True),
            simple_condition("foreign_source_income", ">", 0),
        ),
        "description": (
            "Temporary residents (typically subclass 482, 491, 188, etc. visa-holders) qualify for "
            "the Subdivision 768-910 concession: most foreign-source income is exempt from AU tax "
            "and foreign capital gains on non-TARP assets are disregarded. The concession does NOT "
            "extend to foreign employment income directly attributable to AU services. Loss of "
            "temporary-resident status (e.g. PR grant, marriage to AU resident) ends the concession "
            "prospectively."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Subdiv 768-910 ITAA 1997 — temporary resident foreign income concession",
        "source_key": "AU_ATO_TEMP_RES",
    },
    {
        "rule_code": "AU_TAX_013",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("australian_property_owned", "==", True),
            simple_condition("australian_source_income", ">", 0),
        ),
        "description": (
            "Australian rental income earned by a non-resident is assessable from the first dollar "
            "with no tax-free threshold; non-resident marginal rates start at 30% and rise to 45%. "
            "Quarterly PAYG instalments often apply, and the agent or property manager may need to "
            "withhold. Net rental losses cannot generally be offset against AU-source income of "
            "other types in the same year by a non-resident."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "ITRA 1986 Schedule 7, Part II — non-resident marginal rates",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_STR_001",
        "jurisdiction": "AU",
        "category": RuleCategory.structure,
        "condition_expression": all_conditions(
            simple_condition("australian_company_owned", "==", True),
            simple_condition("div7a_loan_outstanding", "==", True),
        ),
        "description": (
            "Loans, payments, or forgiven debts from an Australian private company to a shareholder "
            "or associate are deemed unfranked dividends under Division 7A unless a complying loan "
            "agreement is in place by the company's lodgement day, with minimum yearly repayments "
            "and benchmark interest. Expats living overseas commonly leave Div 7A loans unstructured "
            "and trigger deemed-dividend assessments years later. Recent ATO guidance has tightened "
            "the treatment of unpaid present entitlements (UPEs) under TD 2022/11."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Div 7A ITAA 1936 — loans / payments from private companies",
        "source_key": "AU_ATO_DIV7A",
    },
    {
        "rule_code": "AU_STR_002",
        "jurisdiction": "AU",
        "category": RuleCategory.structure,
        "condition_expression": all_conditions(
            simple_condition("australian_discretionary_trust_beneficiary", "==", True),
            simple_condition("tax_residency_status", "==", "non_resident"),
        ),
        "description": (
            "An Australian discretionary trust distributing income to a non-resident beneficiary is "
            "subject to non-resident withholding (Section 98) at the top non-resident marginal rate "
            "of 45% on most categories of trust income, with no general tax-free threshold. Trustees "
            "are personally liable to the ATO for the tax on the non-resident's share. Capital gains "
            "from non-TARP assets distributed to a non-resident beneficiary may be disregarded by "
            "the beneficiary but the rules are complex (s. 855-40)."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "ss. 98, 99A ITAA 1936 — trustee assessment for non-resident beneficiary",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_XB_002",
        "jurisdiction": "AU",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "AU"),
            simple_condition("citizenship", "==", "US"),
            simple_condition("dual_tax_residency", "==", True),
        ),
        "description": (
            "The Australia-US tax treaty (1982, Protocol 2001) provides Article 4 tie-breaker rules "
            "for dual residents: permanent home → centre of vital interests → habitual abode → "
            "nationality. Importantly, Article 1(3) Saving Clause preserves the US right to tax its "
            "citizens on worldwide income REGARDLESS of treaty residency outcome. US citizens who "
            "successfully claim AU treaty residency still file US returns; the treaty mainly delivers "
            "Foreign Tax Credit ordering, source-rule modifications, and reduced withholding."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "AU-US DTA, Art. 4 (tie-breaker) and Art. 1(3) (saving clause)",
        "source_key": "AU_TREASURY_DTA",
    },
    {
        "rule_code": "AU_XB_003",
        "jurisdiction": "AU",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "UAE"),
            simple_condition("dual_tax_residency", "==", True),
        ),
        "description": (
            "Australia and the UAE signed a comprehensive double tax agreement in November 2024, "
            "but at the time of writing it has not entered into force. Until ratification and "
            "exchange of instruments, NO comprehensive treaty exists between AU and UAE — meaning "
            "no tie-breaker rule and no reduced withholding. Australian-source dividends, interest, "
            "and royalties paid to UAE residents face full domestic withholding rates (30%, 10%, "
            "30%). UAE residency cannot be invoked under Article 4 for AU treaty purposes."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Australia-UAE DTA — signed 1 Nov 2024, not yet in force",
        "source_key": "UAE_AU_DTA",
    },
    {
        "rule_code": "AU_XB_004",
        "jurisdiction": "AU",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "SG"),
            simple_condition("dual_tax_residency", "==", True),
        ),
        "description": (
            "The Australia-Singapore DTA (1969, with 2010 Protocol) provides Article 4 tie-breaker "
            "rules following the OECD model: permanent home → centre of vital interests → habitual "
            "abode → mutual agreement. The treaty also includes a 183-day rule for short-term "
            "employment (Art 15) — AU-source employment income may be exempt from AU tax for a SG "
            "resident present <183 days, paid by a non-AU employer, with no AU PE bearing the cost."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "AU-SG DTA, Arts 4 & 15 — residence and dependent personal services",
        "source_key": "AU_TREASURY_DTA",
    },
    {
        "rule_code": "AU_XB_005",
        "jurisdiction": "AU",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("working_remotely_for_foreign_employer", "==", True),
            simple_condition("residency_country", "==", "AU"),
        ),
        "description": (
            "An AU-based employee working remotely for a foreign employer can create a Permanent "
            "Establishment (PE) for that employer in Australia under Article 5 of most AU treaties, "
            "exposing the employer to AU corporate income tax on profits attributable to the PE, "
            "PAYG withholding obligations, payroll tax, and superannuation guarantee compliance. "
            "ATO PCG 2023/1 outlines the risk factors. The employee may also have unintended FBT "
            "implications. Employers commonly underestimate the AU footprint created by a single "
            "remote hire."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "PCG 2023/1 — PE risk for foreign employers with remote AU staff",
        "source_key": "AU_ATO_PE",
    },
    {
        "rule_code": "AU_XB_006",
        "jurisdiction": "AU",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("crs_reportable_account", "==", True),
            simple_condition("foreign_financial_accounts_balance", ">", 0),
        ),
        "description": (
            "Australia is a party to the OECD Common Reporting Standard (CRS). Foreign financial "
            "institutions in CRS-participating jurisdictions report account information of "
            "Australian tax residents to their home tax authority, who exchanges with the ATO "
            "annually. AU residents with undisclosed foreign accounts face significantly elevated "
            "audit risk. The ATO uses CRS data to cross-check tax returns against actual offshore "
            "positions and frequently issues 'Project DO IT'-style review letters."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Subdiv 396-A Sch 1 TAA 1953 — CRS implementation in Australia",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_XB_007",
        "jurisdiction": "AU",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "HK"),
            simple_condition("dual_tax_residency", "==", True),
        ),
        "description": (
            "Australia and Hong Kong signed a comprehensive DTA in March 2024; entry into force "
            "depends on completion of domestic ratification by both jurisdictions. Until in force, "
            "no comprehensive treaty applies — AU-source income paid to HK residents is subject to "
            "full domestic withholding and no tie-breaker is available for dual residents. The "
            "Hong Kong DTA, when active, is expected to materially reduce AU non-resident WHT on "
            "dividends, interest, and royalties for HK residents and to provide standard Article 4 "
            "tie-breaker analysis."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Australia-Hong Kong DTA — signed Mar 2024, ratification pending",
        "source_key": "AU_TREASURY_DTA",
    },
    {
        "rule_code": "AU_TAX_014",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("australian_property_owned", "==", True),
            simple_condition("australian_source_income", ">", 0),
        ),
        "description": (
            "Australian non-residents pay non-resident marginal rates from the first dollar of "
            "AU-source rental income. Negative gearing losses against AU income are quarantined and "
            "cannot be offset against foreign-source salary or investment income. Rental losses "
            "carry forward against future AU income. Many AU expats incorrectly assume foreign "
            "employment income can absorb AU rental losses — the quarantine eliminates that strategy."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 6-5(3) ITAA 1997 — non-resident assessable income (rental)",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_TAX_015",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("australian_property_owned", "==", True),
            simple_condition("australian_property_vacant", "==", True),
        ),
        "description": (
            "Vacant Residential Land Tax (VIC), Foreign-owner vacancy fees (Federal), and similar "
            "annual levies apply to dwellings owned by foreign residents that remain unoccupied or "
            "untenanted for substantial periods. The Federal Annual Vacancy Fee (introduced 2017, "
            "uplifted 2024) currently equals 3× the original FIRB application fee per year of "
            "vacancy — for a $2M acquisition this approaches $80,000 per annum."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Foreign Acquisitions and Takeovers Act 1975, Pt 3A — Vacancy Fee",
        "source_key": "AU_FIRB",
    },
    {
        "rule_code": "AU_STR_003",
        "jurisdiction": "AU",
        "category": RuleCategory.structure,
        "condition_expression": all_conditions(
            simple_condition("australian_company_owned", "==", True),
            simple_condition("tax_residency_status", "==", "non_resident"),
        ),
        "description": (
            "An AU private company with a non-resident sole director/shareholder may have its "
            "central management and control located outside Australia, raising questions about "
            "company tax residency under the 'central management and control' test. Following "
            "Bywater Investments v FCT, the ATO scrutinises where actual high-level management "
            "decisions are made. Loss of AU residency by the company can trigger CGT events, "
            "deemed disposals, and franking credit consequences — and may not match the "
            "shareholder's intent."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "TR 2018/5 — Central management and control test (Bywater)",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_TAX_016",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("australian_source_income", ">", 0),
        ),
        "description": (
            "AU non-residents lose access to the Low Income Tax Offset (LITO) and the Low and "
            "Middle Income Tax Offset (where applicable). The combined effect is that tax payable "
            "on Australian-source income is materially higher for non-residents than for residents "
            "at the same gross income level. Modelling AU-source income against residency status "
            "before departure can identify a meaningful planning opportunity."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "ITAA 1997, Subdiv 61-N — LITO not available to foreign residents",
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "AU_TAX_018",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("australian_property_owned", "==", True),
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("permanent_abode_outside_country", "==", True),
        ),
        "description": (
            "The 'six-year absence rule' (s. 118-145 ITAA 1997) lets an AU resident who treats a "
            "former home as their main residence while renting it out preserve the CGT main "
            "residence exemption for up to 6 years of absence (or indefinitely if not income-"
            "producing). Critically, the concession is ONLY available to taxpayers who are "
            "Australian tax residents at the time of CGT event A1 (sale) — the 2020 reforms "
            "removing the MRE for foreign residents override the absence rule. Returning to AU "
            "residency BEFORE settling the sale can preserve the exemption; settling while "
            "non-resident loses it entirely."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "ss. 118-145, 118-110 ITAA 1997 — six-year absence rule (residency-gated)",
        "source_key": "AU_ATO_CGT",
    },
    {
        "rule_code": "AU_TAX_017",
        "jurisdiction": "AU",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("foreign_source_income", ">", 0),
            simple_condition("temp_resident_status", "==", False),
        ),
        "description": (
            "Australian residents (other than temporary residents) are taxed on worldwide income, "
            "including foreign salary, foreign business income, foreign rental, foreign dividends "
            "and foreign capital gains. Foreign Income Tax Offsets (FITOs) are available for "
            "foreign tax actually paid, capped to the AU tax payable on the foreign income. "
            "Returning expats frequently underestimate the assessability of pre-residency-resumption "
            "foreign earnings already received in their first AU year."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 6-5(2), Div 770 ITAA 1997 — worldwide income & FITO",
        "source_key": "AU_ATO_RESIDENCY",
    },

    # ── Singapore (extended set) ───────────────────────────────────────────────
    {
        "rule_code": "SG_RES_003",
        "jurisdiction": "SG",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("nor_scheme_active", "==", True),
            simple_condition("tax_residency_status", "==", "resident"),
        ),
        "description": (
            "The Not Ordinarily Resident (NOR) scheme provided 5-year time-apportionment of "
            "employment income for foreign professionals based in Singapore but spending "
            "significant time abroad. The scheme closed to new applications after Year of "
            "Assessment 2020; existing approved individuals continue to enjoy benefits through "
            "their final 5-year window. AU expats in late-stage NOR years should plan for the "
            "post-NOR step-up in effective Singapore tax rate."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "IRAS NOR scheme — last application YA 2020 (transitional periods continue)",
        "source_key": "SG_IRAS_NOR",
    },
    {
        "rule_code": "SG_RES_004",
        "jurisdiction": "SG",
        "category": RuleCategory.residency,
        "condition_expression": simple_condition("sg_tax_clearance_required", "==", True),
        "description": (
            "Singapore employers must file Form IR21 at least one month before a foreign or PR "
            "employee ceases employment, leaves Singapore for more than 3 months, or is posted "
            "overseas. The employer is required to withhold all monies due to the employee until "
            "IRAS issues a tax clearance directive. Failure to file timely IR21 exposes the "
            "employer to penalties up to SGD 1,000 per offence and the employee to delayed "
            "departures or frozen final payments."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 68(7) ITA (Singapore) — tax clearance Form IR21",
        "source_key": "SG_IRAS_CLEARANCE",
    },
    {
        "rule_code": "SG_TAX_003",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("sg_remitted_foreign_income", ">", 0),
        ),
        "description": (
            "Singapore taxes individuals on a quasi-territorial basis: foreign-source income "
            "received in Singapore by an individual is generally exempt under s. 13(7A) ITA, "
            "EXCEPT where received via a partnership, or where the income is foreign-source "
            "trading income carried on through a Singapore presence. Investment income remitted "
            "to Singapore by a SG-resident individual is broadly exempt — a meaningful advantage "
            "for AU expats relocating with passive offshore portfolios."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 13(7A) ITA (Singapore) — foreign-source income exemption (individuals)",
        "source_key": "SG_IRAS_FSIE",
    },
    {
        "rule_code": "SG_TAX_004",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("singapore_source_income", ">", 320000),
        ),
        "description": (
            "Singapore's resident progressive scale tops out at 24% for chargeable income above "
            "SGD 1,000,000 (revised upward from 22% effective YA 2024). The marginal rate for the "
            "SGD 320k–500k bracket is 22%, and 23% for SGD 500k–1M. High-income AU expats moving "
            "to SG should model the resident progressive curve against their projected SG income "
            "rather than assuming a flat low rate."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2024, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "ITA 1947 (Singapore), Schedule 2 — resident rates effective YA 2024",
        "source_key": "SG_IRAS_RATES",
    },
    {
        "rule_code": "SG_TAX_005",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("sg_property_purchase_planned", "==", True),
        "description": (
            "Foreign individuals purchasing Singapore residential property pay Additional Buyer's "
            "Stamp Duty (ABSD) at 60% of the purchase price (effective from 27 April 2023, raised "
            "from 30%). This is in addition to standard Buyer's Stamp Duty of up to 6%. For a "
            "SGD 3M property, total stamp duty exceeds SGD 1.9M for a foreign buyer. The "
            "AU-Singapore FTA (CSFTA) provides relief for AU citizens — they pay the same ABSD as "
            "SG citizens (5% on second property, 15% on third+)."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 4, 27),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Stamp Duties Act 1929 (Singapore), 3rd Schedule — ABSD rates",
        "source_key": "SG_IRAS_PROPERTY",
    },
    {
        "rule_code": "SG_TAX_006",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("sg_property_being_sold", "==", True),
            simple_condition("sg_property_holding_years", "<", 3),
        ),
        "description": (
            "Singapore residential property sold within 3 years of acquisition attracts Seller's "
            "Stamp Duty: 12% if sold in year 1, 8% if in year 2, 4% if in year 3 (rates revised "
            "downward from prior 16/12/8/4 in 2017). SSD is in addition to any income/property "
            "gains tax characterisation — gains assessed as income (badges of trade) attract "
            "income tax separately. Short-hold flips by AU expats commonly trigger both heads."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Stamp Duties Act 1929 (Singapore), 4th Schedule — Seller's Stamp Duty",
        "source_key": "SG_IRAS_PROPERTY_GAINS",
    },
    {
        "rule_code": "SG_TAX_007",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("sg_area_representative", "==", True),
        "description": (
            "Under the Area Representative scheme, an employee based in Singapore but covering "
            "regional sales/business development across multiple countries may apportion their "
            "Singapore employment income based on actual workdays in Singapore relative to total "
            "workdays. Only the SG-workday share is subject to SG tax. Eligibility requires the "
            "employer to confirm regional duties and the employee to track workdays meticulously. "
            "Common for AU expats holding APAC roles based in SG."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "IRAS Area Representative scheme — workday apportionment of income",
        "source_key": "SG_IRAS_AREA_REP",
    },
    {
        "rule_code": "SG_XB_001",
        "jurisdiction": "SG",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "SG"),
            simple_condition("australian_source_income", ">", 0),
            simple_condition("days_in_country", "<", 183),
        ),
        "description": (
            "Under Article 15 of the AU-SG DTA, a SG tax resident's employment income earned in "
            "Australia may be exempt from AU tax where: (i) the individual is in AU < 183 days in "
            "any 12-month period; (ii) remuneration is paid by, or on behalf of, an employer who "
            "is not an AU resident; and (iii) remuneration is not borne by an AU PE of the "
            "employer. All three conditions must be satisfied. Common short-term assignment "
            "structures often fail condition (iii) once an AU PE recharges costs."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "AU-SG DTA, Art. 15 — short-term employment exemption",
        "source_key": "AU_TREASURY_DTA",
    },
    {
        "rule_code": "SG_STR_002",
        "jurisdiction": "SG",
        "category": RuleCategory.structure,
        "condition_expression": all_conditions(
            simple_condition("sg_company_owned", "==", True),
            simple_condition("singapore_source_income", ">", 0),
        ),
        "description": (
            "Singapore corporate income tax is 17% with a partial exemption: 75% of first SGD "
            "10,000 chargeable income and 50% of next SGD 190,000 are exempt, giving an effective "
            "rate well below 17% on small profits. Start-up companies (first 3 YAs, ordinary share "
            "ownership conditions met) get further concessions. AU expats should not assume "
            "headline 17% — model the partial exemption stack against expected profits."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 43 ITA (Singapore) — corporate tax 17%; partial exemption rules",
        "source_key": "SG_IRAS_RATES",
    },
    {
        "rule_code": "SG_TAX_008",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "resident"),
            simple_condition("crs_reportable_account", "==", True),
        ),
        "description": (
            "Singapore implements CRS through Income Tax Act Part XXB. Singapore Reporting "
            "Financial Institutions identify and report account holders who are tax residents of "
            "CRS-participating jurisdictions (including Australia). AU expats who are SG tax "
            "residents are not reportable to AU on their SG-resident-period accounts, but AU "
            "residents holding SG accounts are reported to the ATO. Ensuring SG tax-residency "
            "self-certifications are accurate is critical to avoid mis-classified reporting."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Part XXB ITA (Singapore) — CRS implementation",
        "source_key": "SG_IRAS_CRS",
    },
    {
        "rule_code": "SG_TAX_009",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("tax_residency_status", "==", "non_resident"),
            simple_condition("singapore_source_income", ">", 0),
            simple_condition("days_in_country", "<", 61),
        ),
        "description": (
            "Singapore-source short-term employment income (≤ 60 days in a year) is exempt from "
            "Singapore tax for non-residents under the 60-day rule, EXCEPT where the individual "
            "is a director, public entertainer, or professional. Many AU executives with brief SG "
            "engagements qualify for full exemption — but director's fees and consultancy income "
            "remain taxable at 24% (director's fees) or 15%/24% (other professional income)."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 13(6) ITA (Singapore) — 60-day short-term employment exemption",
        "source_key": "SG_IRAS_NONRESIDENT",
    },
    {
        "rule_code": "SG_TAX_010",
        "jurisdiction": "SG",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("singapore_source_income", ">", 0),
            simple_condition("tax_residency_status", "==", "resident"),
        ),
        "description": (
            "Singapore individual tax residents are entitled to personal reliefs including the "
            "Earned Income Relief, Spouse Relief, Qualifying Child Relief, Working Mother's Child "
            "Relief, and parent reliefs — collectively capped at SGD 80,000 per YA from YA 2018. "
            "Non-residents receive none of these reliefs. The reliefs materially shift effective "
            "tax rates for moderate-income AU expats with families in SG."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "ITA (Singapore), Pt VI — personal reliefs (cap SGD 80,000)",
        "source_key": "SG_IRAS_RATES",
    },

    # ── Hong Kong (extended set) ───────────────────────────────────────────────
    {
        "rule_code": "HK_RES_002",
        "jurisdiction": "HK",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("hk_services_rendered_in_hk", "==", True),
            simple_condition("days_in_country", "<=", 60),
            simple_condition("tax_residency_status", "==", "non_resident"),
        ),
        "description": (
            "Under Section 8(1B) of the Inland Revenue Ordinance, employment income from services "
            "rendered in Hong Kong by a non-resident visiting Hong Kong for ≤ 60 days in a year "
            "of assessment is exempt from Salaries Tax. The 60 days are counted as full days "
            "(date-of-arrival and date-of-departure both count). This is a critical relief for "
            "AU executives making frequent short trips to HK — careful day-counting is essential "
            "to preserve the exemption."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 8(1B) IRO (Hong Kong) — 60-day visitor exemption (DIPN 10)",
        "source_key": "HK_IRD_60DAY",
    },
    {
        "rule_code": "HK_TAX_003",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("hong_kong_source_income", ">", 0),
            simple_condition("hk_services_rendered_in_hk", "==", False),
        ),
        "description": (
            "Where employment income is from a non-Hong Kong employment but services are partly "
            "rendered in HK, time-apportionment based on workdays in HK applies. Income "
            "attributable to non-HK workdays is exempt. Conversely, income from a Hong Kong "
            "employment is fully assessable to Salaries Tax, with a credit for foreign tax paid "
            "on income re-attributable to non-HK services. The locality-of-employment analysis "
            "(Goepfert principles) is fact-sensitive."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "DIPN 10 — Salaries Tax: locality of employment & time apportionment",
        "source_key": "HK_IRD_60DAY",
    },
    {
        "rule_code": "HK_TAX_004",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("hong_kong_source_income", ">", 0),
            simple_condition("tax_residency_status", "==", "resident"),
        ),
        "description": (
            "Hong Kong Salaries Tax is the lower of (a) progressive rates (2%/6%/10%/14%/17%) on "
            "net chargeable income after personal allowances, or (b) the standard rate of 15% "
            "on net total income (no allowances). For YA 2024/25 a two-tiered standard rate "
            "applies: 15% on first HKD 5M, 16% on the excess. AU expats with HK income above "
            "~HKD 2M typically pay the standard rate."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2024, 4, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Inland Revenue Ordinance, Schedule 1 — Salaries Tax rates (YA 2024/25)",
        "source_key": "HK_IRD_RATES",
    },
    {
        "rule_code": "HK_TAX_005",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("hk_company_owned", "==", True),
            simple_condition("hong_kong_source_income", ">", 0),
        ),
        "description": (
            "Hong Kong Profits Tax operates on a two-tier scheme for incorporated businesses: "
            "8.25% on the first HKD 2M of assessable profits and 16.5% on profits above. The "
            "lower rate is restricted to one entity within a group of connected entities (the "
            "election is annual). Unincorporated businesses are taxed at 7.5%/15%."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 14AA IRO (Hong Kong) — two-tiered Profits Tax rates",
        "source_key": "HK_IRD_PROFITS",
    },
    {
        "rule_code": "HK_TAX_006",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("hk_company_owned", "==", True),
            simple_condition("hk_passive_offshore_income", ">", 0),
            simple_condition("hk_economic_substance_in_hk", "==", False),
        ),
        "description": (
            "The Foreign-Sourced Income Exemption (FSIE) regime, effective 1 January 2023, deems "
            "specified foreign-sourced income (interest, dividends, IP income, disposal gains, "
            "and from 2024 immovable-property disposal gains) to be Hong Kong-sourced and "
            "taxable at 16.5% for in-scope MNE entities that fail the economic substance "
            "requirement. The substance test requires adequate people, premises and decision-"
            "making in HK proportionate to the activity. Pure holding companies have a reduced "
            "substance test."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Inland Revenue (Amendment) (Taxation on Specified Foreign-sourced Income) Ordinance 2022",
        "source_key": "HK_IRD_FSIE",
    },
    {
        "rule_code": "HK_TAX_007",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("hk_property_transaction", "==", True),
        "description": (
            "Hong Kong Stamp Duty on residential property transactions is currently the Ad Valorem "
            "Duty (AVD) Scale 2 — same rate for residents and non-residents after the abolition "
            "of Buyer's Stamp Duty (BSD) and the New Residential Stamp Duty (NRSD) on 28 February "
            "2024. Standard AVD scales from 1.5% to 4.25% based on consideration. Non-residential "
            "property is charged on a separate scale. This 2024 reform materially reduced the "
            "transaction-cost gap between AU expats and local buyers."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2024, 2, 28),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Stamp Duty Ordinance, Schedule 1 — AVD Scale 2 (post Feb 2024 reform)",
        "source_key": "HK_IRD_STAMP",
    },
    {
        "rule_code": "HK_STR_002",
        "jurisdiction": "HK",
        "category": RuleCategory.structure,
        "condition_expression": simple_condition("hk_family_office_structure", "==", True),
        "description": (
            "Hong Kong's Family-Owned Investment Holding Vehicle (FIHV) tax concession (effective "
            "from YA 2022/23) provides a 0% Profits Tax rate on qualifying investment income for "
            "FIHVs managed by a Single Family Office in Hong Kong. Conditions include: minimum "
            "AUM HKD 240M, ≥ 2 qualified employees, ≥ HKD 2M annual operating expenditure in HK, "
            "and structuring through eligible vehicle types. Increasingly used by HNW AU "
            "expats relocating wealth-management functions to HK."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 4, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "s. 1AAB IRO — Tax concession for FIHVs managed by Single Family Offices",
        "source_key": "HK_IRD_FAMILY_OFFICE",
    },
    {
        "rule_code": "HK_XB_002",
        "jurisdiction": "HK",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "HK"),
            simple_condition("australian_source_income", ">", 0),
            simple_condition("treaty_relief_claimed", "==", True),
        ),
        "description": (
            "Australia and Hong Kong signed a comprehensive DTA in March 2024 that is not yet "
            "in force (as at the writing of this rule). Until ratification, claims for treaty "
            "benefits between AU and HK will be denied. Until then, AU-source income paid to HK "
            "residents faces full domestic withholding (30% unfranked dividends, 10% interest, "
            "30% royalties) and no Article 4 tie-breaker analysis is available."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "AU-HK DTA — signed March 2024, ratification pending",
        "source_key": "AU_TREASURY_DTA",
    },
    {
        "rule_code": "HK_TAX_008",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("hk_company_owned", "==", True),
            simple_condition("residency_country", "==", "AU"),
            simple_condition("hk_passive_offshore_income", ">", 0),
        ),
        "description": (
            "An AU resident owning an HK company that earns passive offshore income claiming "
            "FSIE exemption faces a layered analysis: (i) HK FSIE substance test must be met to "
            "preserve the HK exemption; (ii) AU CFC attribution rules under Division 9A may "
            "still apply, attributing the income to the AU resident regardless of HK treatment; "
            "(iii) AU may also assess transfer-pricing exposure under Subdiv 815-B for any "
            "related-party dealings. The HK 'exemption' often does not translate to economic "
            "tax savings for AU residents."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Div 9A ITAA 1936 (CFC) read with HK FSIE regime",
        "review_status": ReviewStatus.unsupported_or_wrong_source,
        "source_key": "AU_ATO_RESIDENCY",
    },
    {
        "rule_code": "HK_TAX_009",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("hong_kong_source_income", ">", 132000),
        "description": (
            "Hong Kong Salaries Tax allowances for YA 2024/25 include a basic personal allowance "
            "of HKD 132,000, married allowance HKD 264,000, and child allowance HKD 130,000 per "
            "child. The progressive rate scale begins at 2% above the allowance. Non-residents "
            "are entitled to allowances proportional to their HK days for non-permanent stays. "
            "Many AU expats overlook the personal allowance entitlement on partial-year HK "
            "engagements."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2024, 4, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "IRO Schedule 4 — Salaries Tax allowances (YA 2024/25)",
        "source_key": "HK_IRD_RATES",
    },
    {
        "rule_code": "HK_TAX_010",
        "jurisdiction": "HK",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("hk_company_owned", "==", True),
            simple_condition("hk_passive_offshore_income", ">", 0),
            simple_condition("hk_economic_substance_in_hk", "==", True),
        ),
        "description": (
            "An HK entity earning specified foreign-sourced income with adequate economic "
            "substance in Hong Kong (people, premises and decisions proportionate to activity) "
            "preserves the territorial exemption under FSIE. Substance documentation must be "
            "contemporaneous: board-meeting minutes, employee logs, expenditure records. The "
            "IRD has signalled increasing scrutiny of substance claims, particularly for "
            "passive-holding structures servicing AU/SG ultimate-parent groups."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "DIPN 60 — Foreign-sourced income exemption: substance requirement",
        "source_key": "HK_IRD_FSIE",
    },

    # ── UAE (extended set) ─────────────────────────────────────────────────────
    {
        "rule_code": "UAE_RES_003",
        "jurisdiction": "UAE",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("days_in_country", ">=", 90),
            simple_condition("uae_permanent_residence_established", "==", True),
            simple_condition("uae_centre_of_interests_in_uae", "==", True),
        ),
        "description": (
            "Under Article 4 of Cabinet Decision No. 85 of 2022, an individual is treated as a "
            "UAE tax resident if they spend ≥ 90 days in the UAE within a 12-month period AND "
            "have either a UAE permanent place of residence (e.g. owned/rented home habitually "
            "used) OR a UAE place of employment OR business. This 90-day pathway, combined with "
            "settled UAE life indicators, is broader than the 183-day default and catches "
            "regularly visiting AU expats with UAE business interests."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 3, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Cabinet Decision No. 85 of 2022, Art. 4(b) — 90-day with PPR/employment test",
        "source_key": "UAE_FTA_RESIDENCY",
    },
    {
        "rule_code": "UAE_RES_004",
        "jurisdiction": "UAE",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("uae_centre_of_interests_in_uae", "==", True),
            simple_condition("residency_country", "==", "UAE"),
        ),
        "description": (
            "The UAE residency regime evaluates 'centre of financial and personal interests' "
            "as a qualitative anchor for treaty-residence claims and Tax Residency Certificate "
            "applications. Indicators include family location, primary residence, principal "
            "investments, business management, and main income sources. AU expats relying on UAE "
            "TRCs for treaty benefits should ensure factual support for the centre-of-interests "
            "claim — the FTA increasingly requests substantiation."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.medium,
        "version": 1,
        "effective_from": date(2023, 3, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Cabinet Decision No. 85 of 2022 — centre of financial/personal interests",
        "source_key": "UAE_FTA_RESIDENCY",
    },
    {
        "rule_code": "UAE_TAX_002",
        "jurisdiction": "UAE",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("uae_business_owned", "==", True),
            simple_condition("uae_revenue", "<=", 3000000),
        ),
        "description": (
            "Small Business Relief under Ministerial Decision No. 73 of 2023 allows resident "
            "Taxable Persons with revenue ≤ AED 3M in the relevant tax period (and all prior "
            "periods from 1 June 2023) to elect to be treated as having no taxable income — "
            "effectively a 0% Corporate Tax outcome. Available for tax periods ending on or "
            "before 31 December 2026. Must be elected on the CT return; certain entities "
            "(QFZP electing entities, MNE constituents) are excluded."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 6, 1),
        "effective_to": date(2026, 12, 31),
        "is_deleted": False,
        "section_reference": "Ministerial Decision No. 73 of 2023 — Small Business Relief",
        "review_status": ReviewStatus.unsupported_or_wrong_source,
        "source_key": "UAE_FTA_SBR",
    },
    {
        "rule_code": "UAE_TAX_003",
        "jurisdiction": "UAE",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("uae_business_owned", "==", True),
            simple_condition("uae_vat_taxable_supplies", ">=", 375000),
        ),
        "description": (
            "Mandatory VAT registration is required where a taxable person's annual taxable "
            "supplies exceed AED 375,000 in the past 12 months OR are expected to in the next "
            "30 days. Standard VAT rate is 5%. Voluntary registration is available from "
            "AED 187,500 of taxable supplies/expenses. Failure to register attracts penalties "
            "of AED 10,000. AU expats running freezone businesses commonly underestimate when "
            "their cross-border supplies trigger UAE VAT obligations."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Federal Decree-Law No. 8 of 2017, Art. 13 — mandatory VAT registration",
        "source_key": "UAE_FTA_VAT",
    },
    {
        "rule_code": "UAE_STR_002",
        "jurisdiction": "UAE",
        "category": RuleCategory.structure,
        "condition_expression": simple_condition("uae_relevant_activity_esr", "==", True),
        "description": (
            "Economic Substance Regulations (Cabinet Decision No. 57 of 2020) require UAE "
            "entities (including freezone entities) carrying out 'Relevant Activities' — "
            "banking, insurance, investment fund management, lease-finance, headquarter, "
            "shipping, holding, IP, and distribution and service centre business — to "
            "demonstrate adequate economic substance in the UAE. Annual ESR notifications and "
            "reports are required. Penalties for non-compliance start at AED 20,000 (failure to "
            "submit notification) and escalate to AED 400,000+ for repeated failures."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Cabinet Decision No. 57 of 2020 — Economic Substance Regulations",
        "source_key": "UAE_ESR",
    },
    {
        "rule_code": "UAE_TAX_004",
        "jurisdiction": "UAE",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("uae_business_owned", "==", True),
            simple_condition("mne_global_revenue_eur_millions", ">=", 750),
        ),
        "description": (
            "The UAE Domestic Minimum Top-up Tax (DMTT) implements OECD Pillar Two GloBE rules "
            "for in-scope Multinational Enterprise Groups with consolidated revenue ≥ EUR 750M "
            "in at least two of the four preceding fiscal years, effective for financial years "
            "starting on or after 1 January 2025. The DMTT brings the effective tax rate of "
            "UAE constituent entities up to 15% where the headline 9% CT (or 0% QFZP) results "
            "in a lower effective rate. AU expats running mid-large MNEs through UAE structures "
            "should reassess effective tax rates under Pillar Two."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Cabinet Decision implementing OECD Pillar Two DMTT (effective Jan 2025)",
        "source_key": "UAE_DMTT",
    },
    {
        "rule_code": "UAE_TAX_005",
        "jurisdiction": "UAE",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("uae_property_transaction", "==", True),
        "description": (
            "Transfer of real estate in the UAE attracts emirate-level transfer fees (no federal "
            "stamp duty). Dubai Land Department charges 4% of the transaction value (typically "
            "split equally between buyer and seller by convention but legally borne by the "
            "buyer); Abu Dhabi charges ~2% transfer fee. AU expats acquiring UAE real estate "
            "should budget the transfer fee plus mortgage-registration fees (0.25% of loan) "
            "and the 5% VAT on commercial property (zero-rated for residential)."
        ),
        "risk_level": RiskLevel.low,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Dubai Law No. 7 of 2006, Art. 184 — Land Department transfer fee 4%",
        "source_key": "UAE_FTA_VAT",
    },
    {
        "rule_code": "UAE_XB_002",
        "jurisdiction": "UAE",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "UAE"),
            simple_condition("australian_property_owned", "==", True),
            simple_condition("treaty_relief_claimed", "==", True),
        ),
        "description": (
            "AU expats living in the UAE who claim AU treaty relief on AU-source income should "
            "verify treaty status: the AU-UAE comprehensive DTA was signed November 2024 but is "
            "not yet in force. Until ratification, claims for reduced AU withholding (e.g. on "
            "Australian dividends, interest, royalties) under a treaty are not available. UAE "
            "Tax Residency Certificates do not unlock AU treaty relief in the absence of a "
            "treaty between the two countries."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "AU-UAE DTA — signed Nov 2024, not yet in force",
        "source_key": "UAE_AU_DTA",
    },
    {
        "rule_code": "UAE_TAX_006",
        "jurisdiction": "UAE",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("uae_freezone_entity", "==", True),
            simple_condition("uae_non_qualifying_income", "==", 0),
            simple_condition("uae_taxable_income", ">", 0),
        ),
        "description": (
            "A Qualifying Free Zone Person (QFZP) earning ONLY Qualifying Income (and de minimis "
            "exempt) benefits from a 0% Corporate Tax rate on Qualifying Income (with 9% applying "
            "to any non-qualifying income). Qualifying activities are defined in Ministerial "
            "Decision No. 265 of 2023 and include manufacturing, trading of qualifying "
            "commodities, holding of shares, fund management for qualifying funds, headquarters "
            "services, treasury services, and others. Substance and adequate operating expenditure "
            "in the freezone is mandatory."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 6, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Ministerial Decision No. 265 of 2023 — Qualifying Activities for QFZPs",
        "source_key": "UAE_FTA_CORPORATE",
    },
    {
        "rule_code": "UAE_RES_005",
        "jurisdiction": "UAE",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("residency_country", "==", "UAE"),
            simple_condition("days_in_country", "<", 90),
            simple_condition("has_other_tax_residency", "==", True),
        ),
        "description": (
            "Spending fewer than 90 days in the UAE in a 12-month period AND maintaining tax "
            "residency in another country generally means the individual is not a UAE tax "
            "resident — closing off access to UAE Tax Residency Certificates. AU expats with "
            "UAE business interests but limited physical presence often discover they have "
            "neither successfully ceased AU residency NOR established UAE residency, leaving "
            "them effectively stateless from a treaty-residence perspective."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2023, 3, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "Cabinet Decision No. 85 of 2022, Arts. 3-4 — UAE residency thresholds",
        "source_key": "UAE_FTA_RESIDENCY",
    },

    # ── United States (extended set) ───────────────────────────────────────────
    {
        "rule_code": "US_RES_002",
        "jurisdiction": "US",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("us_substantial_presence_days", ">=", 183),
            simple_condition("closer_connection_claimed", "==", True),
            simple_condition("days_in_country", "<", 183),
        ),
        "description": (
            "An individual who meets the Substantial Presence Test but is present in the US for "
            "fewer than 183 days in the current year may claim the Closer Connection Exception "
            "(Form 8840) to remain a non-resident alien. Conditions: (i) tax home in a foreign "
            "country, (ii) closer connection to that country than to the US, (iii) timely Form "
            "8840 filed by the return due date including extensions. Cannot apply if a US LPR "
            "application is pending. Not available for the year of green card issue."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 7701(b)(3)(B); Treas. Reg. § 301.7701(b)-2 — Closer Connection",
        "source_key": "US_IRS_CLOSER",
    },
    {
        "rule_code": "US_RES_003",
        "jurisdiction": "US",
        "category": RuleCategory.residency,
        "condition_expression": all_conditions(
            simple_condition("us_substantial_presence_days", ">=", 183),
            simple_condition("treaty_tie_breaker_claimed", "==", True),
        ),
        "description": (
            "An individual meeting the Substantial Presence Test who is also resident under "
            "Australian (or other treaty-partner) domestic law can apply the AU-US treaty Article "
            "4 tie-breaker to claim non-US residency. The position must be disclosed on Form "
            "8833 with the Form 1040-NR. The Saving Clause (Art 1(3)) preserves US right to tax "
            "US citizens — so US citizens cannot use the tie-breaker to escape US residence-based "
            "taxation, only to obtain specific treaty benefits (FTC ordering, source-rule "
            "modifications, reduced WHT)."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 6114; Form 8833 — treaty-based return position",
        "source_key": "US_IRS_TIE_BREAKER",
    },
    {
        "rule_code": "US_TAX_005",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("specified_foreign_assets_balance", ">", 200000),
        ),
        "description": (
            "FATCA Form 8938 (Statement of Specified Foreign Financial Assets) is required for "
            "US persons living abroad whose foreign asset value exceeds USD 200,000 on the last "
            "day of the year OR USD 300,000 at any time during the year (single filers; doubled "
            "for MFJ). For US persons living in the US the thresholds are USD 50,000/75,000. "
            "Form 8938 is FILED WITH the federal return — not separately like FBAR. Penalties "
            "start at USD 10,000 with a USD 50,000 cap for continued failure. Reporting thresholds "
            "are LOWER than FBAR but cover overlapping (and additional) asset classes."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 6038D; Form 8938 — FATCA specified foreign assets",
        "review_status": ReviewStatus.needs_update,
        "source_key": "US_IRS_FATCA",
    },
    {
        "rule_code": "US_TAX_006",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("cfc_us_shareholder", "==", True),
        ),
        "description": (
            "A US citizen or resident owning ≥ 10% (vote or value) of a foreign corporation that "
            "is a CFC must include in current US income their pro-rata share of the CFC's GILTI "
            "(Global Intangible Low-Taxed Income) under §951A. Subpart F income (passive, "
            "related-party) is also currently included under §951. AU expats with US citizenship "
            "owning AU companies routinely face these inclusions; high-tax exception elections "
            "and §250 deductions can reduce the burden but require active election and modelling. "
            "Form 5471 is mandatory information reporting."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. §§ 951, 951A, 250; Form 5471 — Subpart F & GILTI inclusions",
        "review_status": ReviewStatus.unsupported_or_wrong_source,
        "source_key": "US_IRS_GILTI",
    },
    {
        "rule_code": "US_TAX_007",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "!=", "US"),
            simple_condition("us_situs_assets_value", ">", 60000),
        ),
        "description": (
            "Non-resident, non-US-domiciled aliens owning US-situs assets (US real estate, "
            "tangible personal property in the US, US-incorporated company shares) above USD "
            "60,000 face US estate tax exposure — at rates up to 40%. The USD 60,000 lifetime "
            "exemption is MUCH lower than the USD 13.6M+ exemption for US persons. AU expats "
            "directly holding US-listed shares (Apple, Microsoft, etc.) are commonly unaware of "
            "this exposure. Holding through an Australian or other foreign company can avoid "
            "US-situs treatment for the equity (but not for US real estate)."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 2102 — non-resident alien estate tax (USD 60k exemption)",
        "review_status": ReviewStatus.needs_update,
        "source_key": "US_IRS_ESTATE_NRA",
    },
    {
        "rule_code": "US_TAX_008",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": simple_condition("expatriated_covered", "==", True),
        "description": (
            "A covered expatriate under §877A — broadly, an individual relinquishing US "
            "citizenship or long-term LPR status who meets one of the (i) average net income tax "
            "test (USD 206,000 for 2025), (ii) net worth test (USD 2M), or (iii) certification "
            "test (failed to certify 5-year tax compliance) — faces a deemed-disposal exit tax "
            "on worldwide assets at the date of expatriation. Specified tax-deferred accounts "
            "(IRAs, pensions) face accelerated taxation. Bequests to US persons after "
            "expatriation may attract the §2801 inheritance tax on the recipient."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 877A; Form 8854 — Mark-to-market exit tax for covered expatriates",
        "review_status": ReviewStatus.needs_update,
        "source_key": "US_IRS_EXIT",
    },
    {
        "rule_code": "US_TAX_009",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("niit_investment_income", ">", 0),
            simple_condition("foreign_source_income", ">=", 200000),
        ),
        "description": (
            "The 3.8% Net Investment Income Tax (§1411) applies to US persons with Modified "
            "Adjusted Gross Income above USD 200,000 (single) / 250,000 (MFJ) on the lesser of "
            "(a) net investment income or (b) MAGI excess over threshold. Crucially, NIIT cannot "
            "be reduced by the Foreign Tax Credit — there is no treaty-based NIIT credit in most "
            "treaties (the AU-US treaty does NOT provide one). US citizens in AU therefore pay "
            "NIIT on investment income with no AU credit relief, creating real double tax."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 1411 — Net Investment Income Tax (3.8%)",
        "review_status": ReviewStatus.needs_update,
        "source_key": "US_IRS_NIIT",
    },
    {
        "rule_code": "US_TAX_010",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("pfic_holdings", "==", True),
            simple_condition("pfic_election_made", "==", True),
        ),
        "description": (
            "QEF (§1295) and Mark-to-Market (§1296) elections shift PFIC tax treatment away from "
            "the punitive default §1291 excess-distribution regime. QEF requires annual "
            "Information Statements from the PFIC (rare for non-US funds) and converts PFIC "
            "earnings to ordinary income / LTCG flow-through. MTM marks the PFIC to market "
            "annually with gains as ordinary income, losses limited. Both elections must be "
            "made in the first year of PFIC ownership to be fully effective; late elections "
            "leave a §1291 'tail' from prior years."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. §§ 1295, 1296; Form 8621 — QEF / MTM elections",
        "source_key": "US_IRS_PFIC",
    },
    {
        "rule_code": "US_XB_001",
        "jurisdiction": "US",
        "category": RuleCategory.cross_border,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("residency_country", "==", "AU"),
            simple_condition("foreign_source_income", ">", 0),
        ),
        "description": (
            "The AU-US tax treaty allocates taxing rights and provides for relief, but its "
            "Saving Clause (Art 1(3)) preserves the US right to tax US citizens as if the "
            "treaty did not exist. Specific Saving-Clause exceptions (e.g. social security, "
            "pensions, certain dependent personal services) restore treaty benefits. The "
            "interaction with FTC ordering, AU's Foreign Income Tax Offset, and the §911 FEIE "
            "creates planning complexity — particularly around AU superannuation contributions "
            "(deductible in AU but not in US), franking credits, and timing differences."
        ),
        "risk_level": RiskLevel.high,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "AU-US DTA, Art. 1(3) (Saving Clause) and Art. 22 (FTC)",
        "source_key": "US_AU_DTA",
    },
    {
        "rule_code": "US_TAX_011",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("residency_country", "!=", "US"),
            simple_condition("us_state_residency", "in", ["CA", "NY", "VA", "NM", "SC"]),
        ),
        "description": (
            "Several US states (notably California, New York, Virginia, New Mexico, and South "
            "Carolina) apply 'sticky' residency tests that can keep an individual as a state "
            "tax resident even after moving abroad. California in particular looks to domicile "
            "and 'closest connections' rather than simple physical presence. Federal expatriation "
            "or treaty-based non-residency does not affect state-level residency. AU expats with "
            "California ties should formally sever state residency (file Form 540NR final return, "
            "evidence intent to abandon CA domicile) before relying on non-resident status."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "California Rev. & Tax. Code § 17014 — definition of resident",
        "source_key": "US_IRS_INTERNATIONAL",
    },
    {
        "rule_code": "US_TAX_012",
        "jurisdiction": "US",
        "category": RuleCategory.tax,
        "condition_expression": all_conditions(
            simple_condition("citizenship", "==", "US"),
            simple_condition("foreign_source_income", ">", 0),
            simple_condition("residency_country", "!=", "US"),
        ),
        "description": (
            "The Foreign Earned Income Exclusion (FEIE) under §911 lets qualifying US citizens "
            "abroad exclude up to USD 126,500 (2024, indexed) of foreign earned income, plus a "
            "Foreign Housing Exclusion/Deduction. Eligibility requires either Bona Fide Residence "
            "or Physical Presence (330 full days in any 12-month period). FEIE applies BEFORE "
            "FTC, and is generally inferior to FTC for AU-based US citizens because AU tax rates "
            "exceed US rates — running FEIE leaves no FTC to absorb US tax on remaining income. "
            "An informed FTC-only election commonly produces a better outcome."
        ),
        "risk_level": RiskLevel.medium,
        "confidence_level": ConfidenceLevel.high,
        "version": 1,
        "effective_from": date(2025, 1, 1),
        "effective_to": None,
        "is_deleted": False,
        "section_reference": "26 U.S.C. § 911; Form 2555 — Foreign Earned Income Exclusion",
        "review_status": ReviewStatus.needs_update,
        "source_key": "US_IRS_INTERNATIONAL",
    },
]

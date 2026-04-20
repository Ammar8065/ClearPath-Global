"""Rule fixtures + condition helpers for the ClearPath seeding pipeline."""
from datetime import date

from app.models.rule import ConfidenceLevel, RiskLevel, RuleCategory

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
        "source_key": "SG_IRAS_RESIDENCY",
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
        "source_key": "HK_IRD_PROFITS",
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
]

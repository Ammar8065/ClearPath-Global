"""Python mirror of the assessment field catalog in frontend/evaluation_config.js.

Single source the extraction prompt and extraction validation both read.
``tests/test_ai_field_catalog.py`` guards against drift between this module and
the JavaScript ``DEFAULT_STATE`` definition.

Field types map to payload value types:
    ternary       -> bool
    number        -> float (ints accepted)
    jurisdiction  -> one of AU / SG / HK / UAE / US
    tax_status    -> one of resident / non_resident / dual_resident
    us_state      -> one of CA / NY / VA / NM / SC
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

ALLOWED_VALUES: dict[str, tuple[str, ...]] = {
    "jurisdiction": ("AU", "SG", "HK", "UAE", "US"),
    "tax_status": ("resident", "non_resident", "dual_resident"),
    "us_state": ("CA", "NY", "VA", "NM", "SC"),
}


@dataclass(frozen=True)
class FieldSpec:
    key: str
    type: str
    label: str
    help: str
    group: str


_SPECS: tuple[FieldSpec, ...] = (
    # ── Core Profile ─────────────────────────────────────────────────────────
    FieldSpec("days_in_country", "number", "How many days has the client spent in the relevant country?", "The day count that matters most for the residency test being reviewed.", "core"),
    FieldSpec("citizenship", "jurisdiction", "What citizenship is being assessed?", "Select the citizenship most relevant to this review.", "core"),
    FieldSpec("domicile_country", "jurisdiction", "Where is the client domiciled?", "Important for domicile-based residency tests like Australia's.", "core"),
    FieldSpec("residency_country", "jurisdiction", "Where does the client currently reside?", "The country where the client is currently living or treated as resident.", "core"),
    FieldSpec("tax_residency_status", "tax_status", "What is the client's current tax residency status?", "Select how the client is currently being treated for tax purposes.", "core"),
    FieldSpec("worldwide_income", "number", "What is the client's worldwide income?", "Total global income from all sources — needed for certain thresholds and surcharges.", "core"),
    FieldSpec("temp_resident_status", "ternary", "Does the client hold temporary resident status?", "Yes if the client is on a temporary visa (e.g. 457/482 in Australia) with special tax treatment.", "core"),
    FieldSpec("working_remotely_for_foreign_employer", "ternary", "Is the client working remotely for a foreign employer?", "Yes if the client is physically in one country but employed by a company in another.", "core"),
    # ── Cross-Border Signals ─────────────────────────────────────────────────
    FieldSpec("foreign_source_income", "number", "Does the client earn foreign-source income?", "The annual amount from sources outside the residency country.", "cross-border"),
    FieldSpec("foreign_financial_accounts_balance", "number", "What is the highest balance in foreign financial accounts?", "The peak aggregate balance across all accounts held outside the residency country.", "cross-border"),
    FieldSpec("dual_tax_residency", "ternary", "Do two countries currently claim the client as tax resident?", "Yes when the client appears resident in more than one jurisdiction at the same time.", "cross-border"),
    FieldSpec("treaty_relief_claimed", "ternary", "Has treaty relief already been claimed?", "Yes if the client has relied on a tax treaty tie-breaker or treaty exemption.", "cross-border"),
    FieldSpec("crs_reportable_account", "ternary", "Does the client hold CRS-reportable accounts?", "Yes if the client has financial accounts reported under the Common Reporting Standard.", "cross-border"),
    FieldSpec("foreign_purchaser_property_purchase", "ternary", "Is the client purchasing property as a foreign person?", "Yes if the client is buying real estate in a country where they are not a citizen or permanent resident.", "cross-border"),
    FieldSpec("firb_approval_obtained", "ternary", "Has FIRB approval been obtained?", "Required for foreign persons purchasing Australian real estate above certain thresholds.", "cross-border"),
    # ── Australia ────────────────────────────────────────────────────────────
    FieldSpec("australian_source_income", "number", "Does the client earn Australian-source income?", "Rent, dividends, salary, interest, or any other Australian-sourced amounts (annual).", "australia"),
    FieldSpec("australian_property_owned", "ternary", "Does the client own Australian property?", "Yes if the client owns a home, rental property, or other real estate in Australia.", "australia"),
    FieldSpec("australian_property_being_sold", "ternary", "Is Australian property being sold?", "Triggers CGT withholding and non-resident capital gains obligations.", "australia"),
    FieldSpec("australian_property_vacant", "ternary", "Has the Australian property been left vacant?", "Foreign owners of residential property may owe an annual vacancy fee if it is not occupied or genuinely available for rent.", "australia"),
    FieldSpec("permanent_abode_outside_country", "ternary", "Has a permanent home been established outside Australia?", "Yes if the client has set up a lasting, settled home overseas — not just temporary accommodation.", "australia"),
    FieldSpec("strong_personal_economic_ties_in_country", "ternary", "Do strong personal or economic ties remain in Australia?", "Family, employment, bank accounts, memberships — anything anchoring the client to Australia.", "australia"),
    FieldSpec("eligible_commonwealth_superannuation_member", "ternary", "Is the client a Commonwealth superannuation scheme member?", "These members are deemed Australian residents regardless of physical presence.", "australia"),
    FieldSpec("australian_company_owned", "ternary", "Does the client own or control an Australian company?", "Yes if the client has a meaningful ownership or control role in an Australian entity.", "australia"),
    FieldSpec("div7a_loan_outstanding", "ternary", "Is there an outstanding Division 7A loan?", "Loans from a private company to shareholders or associates — special deemed-dividend rules apply.", "australia"),
    FieldSpec("australian_discretionary_trust_beneficiary", "ternary", "Is the client a beneficiary of an Australian discretionary trust?", "Non-resident beneficiaries face different withholding and distribution rules.", "australia"),
    FieldSpec("foreign_trust_distribution_received", "ternary", "Has the client received distributions from a foreign trust?", "Australian residents receiving foreign trust income have specific reporting and tax obligations.", "australia"),
    FieldSpec("super_lump_sum_received", "ternary", "Has the client received a superannuation lump sum?", "The tax treatment differs between residents and non-residents and depends on the components.", "australia"),
    FieldSpec("dasp_eligible", "ternary", "Is the client eligible for a Departing Australia Superannuation Payment?", "Available to temporary residents who are permanently leaving Australia.", "australia"),
    FieldSpec("private_health_insurance_held", "ternary", "Does the client hold private health insurance?", "Residents without adequate cover may face the Medicare Levy Surcharge above certain income thresholds.", "australia"),
    FieldSpec("au_help_debt", "ternary", "Does the client have a HELP/HECS debt?", "Overseas-resident debtors must make repayments once their worldwide income exceeds the threshold.", "australia"),
    FieldSpec("non_tarp_assets_held", "ternary", "Does the client hold non-TARP Australian assets?", "Non-taxable Australian real property — affects CGT outcomes for departing residents.", "australia"),
    FieldSpec("i1_deferral_election", "ternary", "Has an IT 2650 / I1 CGT deferral election been made?", "Departing residents can choose to defer CGT on certain assets until actual disposal.", "australia"),
    # ── Singapore ────────────────────────────────────────────────────────────
    FieldSpec("singapore_source_income", "number", "Does the client earn Singapore-source income?", "Salary, consulting fees, or other income sourced from Singapore (annual).", "singapore"),
    FieldSpec("sg_company_owned", "ternary", "Does the client own or control a Singapore company?", "Yes if the client has a meaningful ownership or control role.", "singapore"),
    FieldSpec("sg_director_fees", "number", "Does the client receive Singapore director fees?", "Director fees from a Singapore company are taxable regardless of residency (annual amount).", "singapore"),
    FieldSpec("employment_straddles_two_years", "ternary", "Does the employment span two calendar years?", "Relevant to IRAS's two-year administrative concession for residency.", "singapore"),
    FieldSpec("total_days_in_country", "number", "Total days in Singapore across the review period?", "Use the broader period count when the test looks beyond a single year.", "singapore"),
    FieldSpec("sg_tax_clearance_required", "ternary", "Is a tax clearance (IR21) required?", "Employers must file IR21 when a foreign employee ceases employment or leaves Singapore.", "singapore"),
    FieldSpec("sg_remitted_foreign_income", "number", "Has foreign income been remitted into Singapore?", "Singapore generally exempts foreign income unless remitted — the remitted amount if applicable.", "singapore"),
    FieldSpec("sg_property_purchase_planned", "ternary", "Is the client planning to purchase Singapore property?", "Additional Buyer's Stamp Duty (ABSD) rates differ by residency status and number of properties.", "singapore"),
    FieldSpec("sg_property_being_sold", "ternary", "Is the client selling Singapore property?", "Seller's Stamp Duty (SSD) may apply — rates depend on the holding period and residency status.", "singapore"),
    FieldSpec("sg_property_holding_years", "number", "How long has the property been held (years)?", "Seller's Stamp Duty (SSD) applies to properties sold within the holding period.", "singapore"),
    FieldSpec("sg_area_representative", "ternary", "Is the client acting as a Singapore area representative?", "Area representatives have specific tax obligations even without physical presence.", "singapore"),
    FieldSpec("nor_scheme_active", "ternary", "Is the client on Singapore's Not Ordinarily Resident (NOR) scheme?", "The NOR scheme time-apportioned employment income for foreign professionals based in Singapore. It closed to new applicants after YA 2020; existing approvals run to the end of their five-year window.", "singapore"),
    # ── Hong Kong ────────────────────────────────────────────────────────────
    FieldSpec("hong_kong_source_income", "number", "Does the client earn Hong Kong-source income?", "Employment income, business profits, or other income sourced from Hong Kong (annual).", "hong-kong"),
    FieldSpec("hk_company_owned", "ternary", "Does the client own or control a Hong Kong company?", "Yes if the client has an ownership or control role in a Hong Kong entity.", "hong-kong"),
    FieldSpec("employer_provided_benefits_hk", "ternary", "Does the client receive employer-provided benefits in Hong Kong?", "Housing, share awards, memberships, and similar taxable perquisites.", "hong-kong"),
    FieldSpec("hk_services_rendered_in_hk", "ternary", "Were services physically rendered in Hong Kong?", "Determines whether the 60-day exemption or income apportionment applies.", "hong-kong"),
    FieldSpec("hk_passive_offshore_income", "number", "Does the Hong Kong company earn passive offshore income?", "Dividends, interest, IP royalties, or disposal gains from outside Hong Kong — relevant under the FSIE regime.", "hong-kong"),
    FieldSpec("hk_economic_substance_in_hk", "ternary", "Does the Hong Kong entity maintain economic substance?", "Adequate staff, premises, and decision-making in Hong Kong — a key defence under the FSIE regime.", "hong-kong"),
    FieldSpec("hk_family_office_structure", "ternary", "Is there a Hong Kong family office structure?", "Eligible single-family offices can apply for profits tax concessions on qualifying transactions.", "hong-kong"),
    FieldSpec("hk_property_transaction", "ternary", "Is the client involved in a Hong Kong property transaction?", "Special stamp duty, buyer's stamp duty, or ad valorem duty may apply.", "hong-kong"),
    # ── UAE ──────────────────────────────────────────────────────────────────
    FieldSpec("uae_business_owned", "ternary", "Does the client own or operate a UAE business?", "Yes if the client owns a mainland or freezone business entity.", "uae"),
    FieldSpec("uae_taxable_income", "number", "What is the estimated UAE taxable income?", "Annual taxable amount in AED — corporate tax applies above the small-business threshold.", "uae"),
    FieldSpec("uae_freezone_entity", "ternary", "Does the client use a UAE freezone entity?", "Freezone entities may qualify for 0% corporate tax on qualifying income.", "uae"),
    FieldSpec("uae_non_qualifying_income", "number", "Does the freezone entity earn non-qualifying income?", "Non-qualifying income (mainland sourced, certain excluded activities) erodes the 0% benefit (AED amount).", "uae"),
    FieldSpec("has_other_tax_residency", "ternary", "Does the client hold tax residency in another country?", "Yes if the client is still considered tax resident somewhere else as well.", "uae"),
    FieldSpec("tax_residency_certificate_requested", "ternary", "Has a UAE tax residency certificate been requested?", "Yes if the application has been submitted to the Federal Tax Authority.", "uae"),
    FieldSpec("tax_residency_certificate", "ternary", "Has the UAE tax residency certificate been issued?", "Yes only if the certificate is already in hand — not just applied for.", "uae"),
    FieldSpec("uae_permanent_residence_established", "ternary", "Has permanent residence been established in the UAE?", "A golden visa, investor visa, or long-term residency supports the tax residency application.", "uae"),
    FieldSpec("uae_centre_of_interests_in_uae", "ternary", "Is the client's centre of vital interests in the UAE?", "Where the client's closest personal and economic ties are — a key factor for residency and treaty tie-breakers.", "uae"),
    FieldSpec("uae_revenue", "number", "What is the UAE entity's annual revenue?", "Revenue below AED 3M may qualify for the small-business relief.", "uae"),
    FieldSpec("uae_vat_taxable_supplies", "number", "What is the value of taxable supplies for VAT purposes?", "Mandatory VAT registration applies at AED 375,000; voluntary at AED 187,500.", "uae"),
    FieldSpec("uae_relevant_activity_esr", "ternary", "Does the entity carry out a relevant activity under ESR?", "Economic Substance Regulations require substance in the UAE for certain activities (banking, insurance, IP, etc.).", "uae"),
    FieldSpec("mne_global_revenue_eur_millions", "number", "What is the MNE group's global revenue (EUR millions)?", "Groups with EUR 750M+ revenue face Pillar Two global minimum tax and country-by-country reporting.", "uae"),
    # ── US ───────────────────────────────────────────────────────────────────
    FieldSpec("us_substantial_presence_days", "number", "What is the weighted substantial presence day count?", "The IRS uses a 3-year weighted formula — the computed figure.", "us"),
    FieldSpec("pfic_holdings", "ternary", "Does the client hold PFICs or foreign managed funds?", "Foreign mutual funds, ETFs, or pooled investments are often classified as PFICs for US persons.", "us"),
    FieldSpec("pfic_election_made", "ternary", "Has a QEF or mark-to-market election been made?", "These elections change how PFIC income is taxed — often more favourable than the default excess-distribution regime.", "us"),
    FieldSpec("closer_connection_claimed", "ternary", "Is a closer-connection exception being claimed?", "Available if present under 183 days in the current year and the client maintains a tax home elsewhere.", "us"),
    FieldSpec("treaty_tie_breaker_claimed", "ternary", "Is a treaty tie-breaker position being taken?", "Used when the client is resident under both the SPT and another country's rules.", "us"),
    FieldSpec("specified_foreign_assets_balance", "number", "What is the total value of specified foreign financial assets?", "FATCA Form 8938 filing thresholds differ by residency — $200K for overseas filers, $50K for domestic.", "us"),
    FieldSpec("cfc_us_shareholder", "ternary", "Is the client a US shareholder of a controlled foreign corporation?", "US persons owning 10%+ of a foreign corporation face Subpart F and GILTI inclusion rules.", "us"),
    FieldSpec("us_situs_assets_value", "number", "What is the value of US-situs assets?", "Non-US persons with US-situs assets over $60,000 may face US estate tax exposure.", "us"),
    FieldSpec("expatriated_covered", "ternary", "Is the client a covered expatriate?", "Former US citizens or long-term residents who meet certain thresholds face the exit tax on departure.", "us"),
    FieldSpec("niit_investment_income", "number", "What is the client's net investment income?", "The 3.8% Net Investment Income Tax applies above $200K (single) / $250K (married filing jointly).", "us"),
    FieldSpec("us_state_residency", "us_state", "Which US state claims the client as resident?", "Some states (CA, NY, VA, NM, SC) impose ongoing tax obligations even after moving abroad.", "us"),
)

FIELD_CATALOG: dict[str, FieldSpec] = {spec.key: spec for spec in _SPECS}


def coerce_value(spec: FieldSpec, value: Any) -> tuple[Any, str | None]:
    """Validate and normalise an extracted value against its field spec.

    Returns (coerced_value, None) on success or (None, reason) on rejection.
    bool is checked before number because bool is a subclass of int.
    """
    if spec.type == "ternary":
        if isinstance(value, bool):
            return value, None
        return None, f"expected true/false, got {value!r}"

    if spec.type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None, f"expected a number, got {value!r}"
        if not isfinite(float(value)):
            return None, f"expected a finite number, got {value!r}"
        return float(value), None

    allowed = ALLOWED_VALUES[spec.type]
    if not isinstance(value, str):
        return None, f"expected one of {', '.join(allowed)}, got {value!r}"
    normalised = value.strip()
    for option in allowed:
        if normalised.lower() == option.lower():
            return option, None
    return None, f"expected one of {', '.join(allowed)}, got {value!r}"


def catalog_prompt_lines() -> str:
    """Render the catalog as prompt text, grouped, one field per line."""
    lines: list[str] = []
    current_group = None
    for spec in _SPECS:
        if spec.group != current_group:
            current_group = spec.group
            lines.append(f"\n## {current_group}")
        if spec.type in ALLOWED_VALUES:
            type_note = f"one of: {', '.join(ALLOWED_VALUES[spec.type])}"
        elif spec.type == "ternary":
            type_note = "true/false"
        else:
            type_note = "number"
        lines.append(f"- {spec.key} ({type_note}): {spec.label} {spec.help}")
    return "\n".join(lines)

import { JURISDICTIONS } from "./core.js";

export const TAX_RESIDENCY_OPTIONS = [
  { value: "", label: "Not specified" },
  { value: "resident", label: "Resident" },
  { value: "non_resident", label: "Non-resident" },
  { value: "dual_resident", label: "Dual resident" },
];

export const FOCUS_OPTIONS = JURISDICTIONS.map((item) => ({
  value: item.value,
  label: item.label.replace(/ \(.+\)$/, ""),
}));

export const US_STATE_OPTIONS = [
  { value: "", label: "Not applicable" },
  { value: "CA", label: "California" },
  { value: "NY", label: "New York" },
  { value: "VA", label: "Virginia" },
  { value: "NM", label: "New Mexico" },
  { value: "SC", label: "South Carolina" },
];

export const DEFAULT_STATE = {
  // Core
  days_in_country: null,
  citizenship: "",
  domicile_country: "",
  residency_country: "",
  tax_residency_status: "",
  worldwide_income: null,
  temp_resident_status: null,
  working_remotely_for_foreign_employer: null,

  // Cross-border
  foreign_source_income: null,
  foreign_financial_accounts_balance: null,
  dual_tax_residency: null,
  treaty_relief_claimed: null,
  crs_reportable_account: null,
  foreign_purchaser_property_purchase: null,
  firb_approval_obtained: null,

  // Australia
  australian_source_income: null,
  australian_property_owned: null,
  australian_property_being_sold: null,
  australian_property_vacant: null,
  permanent_abode_outside_country: null,
  strong_personal_economic_ties_in_country: null,
  eligible_commonwealth_superannuation_member: null,
  australian_company_owned: null,
  div7a_loan_outstanding: null,
  australian_discretionary_trust_beneficiary: null,
  foreign_trust_distribution_received: null,
  super_lump_sum_received: null,
  dasp_eligible: null,
  private_health_insurance_held: null,
  au_help_debt: null,
  non_tarp_assets_held: null,
  i1_deferral_election: null,

  // Singapore
  singapore_source_income: null,
  sg_company_owned: null,
  sg_director_fees: null,
  employment_straddles_two_years: null,
  total_days_in_country: null,
  sg_tax_clearance_required: null,
  sg_remitted_foreign_income: null,
  sg_property_purchase_planned: null,
  sg_property_being_sold: null,
  sg_property_holding_years: null,
  sg_area_representative: null,
  nor_scheme_active: null,

  // Hong Kong
  hong_kong_source_income: null,
  hk_company_owned: null,
  employer_provided_benefits_hk: null,
  hk_services_rendered_in_hk: null,
  hk_passive_offshore_income: null,
  hk_economic_substance_in_hk: null,
  hk_family_office_structure: null,
  hk_property_transaction: null,

  // UAE
  uae_business_owned: null,
  uae_taxable_income: null,
  uae_freezone_entity: null,
  uae_non_qualifying_income: null,
  has_other_tax_residency: null,
  tax_residency_certificate_requested: null,
  tax_residency_certificate: null,
  uae_permanent_residence_established: null,
  uae_centre_of_interests_in_uae: null,
  uae_revenue: null,
  uae_vat_taxable_supplies: null,
  uae_relevant_activity_esr: null,
  mne_global_revenue_eur_millions: null,

  // US
  us_substantial_presence_days: null,
  pfic_holdings: null,
  pfic_election_made: null,
  closer_connection_claimed: null,
  treaty_tie_breaker_claimed: null,
  specified_foreign_assets_balance: null,
  cfc_us_shareholder: null,
  us_situs_assets_value: null,
  expatriated_covered: null,
  niit_investment_income: null,
  us_state_residency: "",
};

// ── showWhen condition evaluator ────────────────────────────────────────────
// Supports: { field, is }, { field, not }, { any: [...] }, { all: [...] }
export function fieldVisible(condition, currentAnswers) {
  if (!condition) return true;
  if (condition.any) return condition.any.some((c) => fieldVisible(c, currentAnswers));
  if (condition.all) return condition.all.every((c) => fieldVisible(c, currentAnswers));
  const val = currentAnswers[condition.field];
  if ("is" in condition) return val === condition.is;
  if ("not" in condition) return val !== condition.not;
  if ("provided" in condition) {
    if (condition.provided) return val !== null && val !== undefined && val !== "";
    return val === null || val === undefined || val === "";
  }
  return true;
}

// ── Groups & fields ─────────────────────────────────────────────────────────

export const GROUPS = [
  {
    id: "core",
    title: "Core Profile",
    description: "Start here — the basics that shape every assessment.",
    alwaysVisible: true,
    open: true,
    fields: [
      { key: "days_in_country", label: "How many days has the client spent in the relevant country?", help: "The day count that matters most for the residency test being reviewed.", type: "number", placeholder: "e.g. 183" },
      { key: "citizenship", label: "What citizenship is being assessed?", help: "Select the citizenship most relevant to this review.", type: "jurisdiction" },
      { key: "domicile_country", label: "Where is the client domiciled?", help: "Important for domicile-based residency tests like Australia's.", type: "jurisdiction" },
      { key: "residency_country", label: "Where does the client currently reside?", help: "The country where the client is currently living or treated as resident.", type: "jurisdiction" },
      { key: "tax_residency_status", label: "What is the client's current tax residency status?", help: "Select how the client is currently being treated for tax purposes.", type: "tax_status" },
      { key: "worldwide_income", label: "What is the client's worldwide income?", help: "Total global income from all sources — needed for certain thresholds and surcharges.", type: "number", placeholder: "e.g. 120000" },
      { key: "temp_resident_status", label: "Does the client hold temporary resident status?", help: "Choose Yes if the client is on a temporary visa (e.g. 457/482 in Australia) with special tax treatment.", type: "ternary" },
      { key: "working_remotely_for_foreign_employer", label: "Is the client working remotely for a foreign employer?", help: "Choose Yes if the client is physically in one country but employed by a company in another.", type: "ternary" },
    ],
  },
  {
    id: "cross-border",
    title: "Cross-Border Signals",
    description: "High-level facts that drive treaty, foreign-income, and reporting obligations.",
    alwaysVisible: true,
    open: true,
    fields: [
      { key: "foreign_source_income", label: "Does the client earn foreign-source income?", help: "Enter the annual amount from sources outside the residency country.", type: "number", placeholder: "e.g. 145000" },
      { key: "foreign_financial_accounts_balance", label: "What is the highest balance in foreign financial accounts?", help: "The peak aggregate balance across all accounts held outside the residency country.", type: "number", placeholder: "e.g. 42000" },
      { key: "dual_tax_residency", label: "Do two countries currently claim the client as tax resident?", help: "Choose Yes when the client appears resident in more than one jurisdiction at the same time.", type: "ternary" },
      { key: "treaty_relief_claimed", label: "Has treaty relief already been claimed?", help: "Choose Yes if the client has relied on a tax treaty tie-breaker or treaty exemption.", type: "ternary" },
      { key: "crs_reportable_account", label: "Does the client hold CRS-reportable accounts?", help: "Choose Yes if the client has financial accounts that are reported under the Common Reporting Standard.", type: "ternary",
        showWhen: { any: [{ field: "foreign_financial_accounts_balance", provided: true }, { field: "dual_tax_residency", is: true }] },
      },
      { key: "foreign_purchaser_property_purchase", label: "Is the client purchasing property as a foreign person?", help: "Choose Yes if the client is buying real estate in a country where they are not a citizen or permanent resident.", type: "ternary" },
      { key: "firb_approval_obtained", label: "Has FIRB approval been obtained?", help: "Required for foreign persons purchasing Australian real estate above certain thresholds.", type: "ternary",
        showWhen: { field: "foreign_purchaser_property_purchase", is: true },
      },
    ],
  },

  // ── Australia ─────────────────────────────────────────────────────────────
  {
    id: "australia",
    title: "Australia",
    description: "Residency tests, property, superannuation, and Australian-source income signals.",
    focus: "AU",
    fields: [
      { key: "australian_source_income", label: "Does the client earn Australian-source income?", help: "Include rent, dividends, salary, interest, or any other Australian-sourced amounts.", type: "number", placeholder: "e.g. 48000" },
      { key: "australian_property_owned", label: "Does the client own Australian property?", help: "Choose Yes if the client owns a home, rental property, or other real estate in Australia.", type: "ternary" },
      { key: "australian_property_being_sold", label: "Is Australian property being sold?", help: "Triggers CGT withholding and non-resident capital gains obligations.",
        type: "ternary",
        showWhen: { field: "australian_property_owned", is: true },
      },
      { key: "australian_property_vacant", label: "Has the Australian property been left vacant?", help: "Foreign owners of residential property may owe an annual vacancy fee if it is not occupied or genuinely available for rent.",
        type: "ternary",
        showWhen: { field: "australian_property_owned", is: true },
      },
      { key: "permanent_abode_outside_country", label: "Has a permanent home been established outside Australia?", help: "Choose Yes if the client has set up a lasting, settled home overseas — not just temporary accommodation.", type: "ternary" },
      { key: "strong_personal_economic_ties_in_country", label: "Do strong personal or economic ties remain in Australia?", help: "Family, employment, bank accounts, memberships — anything anchoring the client to Australia.", type: "ternary" },
      { key: "eligible_commonwealth_superannuation_member", label: "Is the client a Commonwealth superannuation scheme member?", help: "These members are deemed Australian residents regardless of physical presence.", type: "ternary" },
      { key: "australian_company_owned", label: "Does the client own or control an Australian company?", help: "Choose Yes if the client has a meaningful ownership or control role in an Australian entity.", type: "ternary" },
      { key: "div7a_loan_outstanding", label: "Is there an outstanding Division 7A loan?", help: "Loans from a private company to shareholders or associates — special deemed-dividend rules apply.",
        type: "ternary",
        showWhen: { field: "australian_company_owned", is: true },
      },
      { key: "australian_discretionary_trust_beneficiary", label: "Is the client a beneficiary of an Australian discretionary trust?", help: "Non-resident beneficiaries face different withholding and distribution rules.", type: "ternary" },
      { key: "foreign_trust_distribution_received", label: "Has the client received distributions from a foreign trust?", help: "Australian residents receiving foreign trust income have specific reporting and tax obligations.", type: "ternary",
        showWhen: { field: "tax_residency_status", is: "resident" },
      },
      { key: "super_lump_sum_received", label: "Has the client received a superannuation lump sum?", help: "The tax treatment differs between residents and non-residents and depends on the components.",
        type: "ternary",
        showWhen: { field: "tax_residency_status", is: "resident" },
      },
      { key: "dasp_eligible", label: "Is the client eligible for a Departing Australia Superannuation Payment?", help: "Available to temporary residents who are permanently leaving Australia.", type: "ternary",
        showWhen: { field: "temp_resident_status", is: true },
      },
      { key: "private_health_insurance_held", label: "Does the client hold private health insurance?", help: "Residents without adequate cover may face the Medicare Levy Surcharge above certain income thresholds.",
        type: "ternary",
        showWhen: { field: "tax_residency_status", is: "resident" },
      },
      { key: "au_help_debt", label: "Does the client have a HELP/HECS debt?", help: "Overseas-resident debtors must make repayments once their worldwide income exceeds the threshold.", type: "ternary" },
      { key: "non_tarp_assets_held", label: "Does the client hold non-TARP Australian assets?", help: "Non-taxable Australian real property — affects CGT outcomes for departing residents.",
        type: "ternary",
        showWhen: { field: "tax_residency_status", is: "non_resident" },
      },
      { key: "i1_deferral_election", label: "Has an IT 2650 / I1 CGT deferral election been made?", help: "Departing residents can choose to defer CGT on certain assets until actual disposal.",
        type: "ternary",
        showWhen: { field: "non_tarp_assets_held", is: true },
      },
    ],
  },

  // ── Singapore ─────────────────────────────────────────────────────────────
  {
    id: "singapore",
    title: "Singapore",
    description: "IRAS residency, company exposure, property, and employment signals.",
    focus: "SG",
    fields: [
      { key: "singapore_source_income", label: "Does the client earn Singapore-source income?", help: "Salary, consulting fees, or other income sourced from Singapore.", type: "number", placeholder: "e.g. 80000" },
      { key: "sg_company_owned", label: "Does the client own or control a Singapore company?", help: "Choose Yes if the client has a meaningful ownership or control role.", type: "ternary" },
      { key: "sg_director_fees", label: "Does the client receive Singapore director fees?", help: "Director fees from a Singapore company are taxable regardless of residency.", type: "number", placeholder: "e.g. 15000" },
      { key: "employment_straddles_two_years", label: "Does the employment span two calendar years?", help: "Relevant to IRAS's two-year administrative concession for residency.", type: "ternary" },
      { key: "total_days_in_country", label: "Total days in Singapore across the review period?", help: "Use the broader period count when the test looks beyond a single year.", type: "number", placeholder: "e.g. 190" },
      { key: "sg_tax_clearance_required", label: "Is a tax clearance (IR21) required?", help: "Employers must file IR21 when a foreign employee ceases employment or leaves Singapore.", type: "ternary" },
      { key: "sg_remitted_foreign_income", label: "Has foreign income been remitted into Singapore?", help: "Singapore generally exempts foreign income unless remitted — enter the remitted amount if applicable.",
        type: "number", placeholder: "e.g. 30000",
        showWhen: { field: "tax_residency_status", is: "resident" },
      },
      { key: "sg_property_purchase_planned", label: "Is the client planning to purchase Singapore property?", help: "Additional Buyer's Stamp Duty (ABSD) rates differ by residency status and number of properties.", type: "ternary" },
      { key: "sg_property_being_sold", label: "Is the client selling Singapore property?", help: "Seller's Stamp Duty (SSD) may apply — rates depend on the holding period and residency status.",
        type: "ternary",
      },
      { key: "sg_property_holding_years", label: "How long has the property been held (years)?", help: "Seller's Stamp Duty (SSD) applies to properties sold within the holding period.",
        type: "number", placeholder: "e.g. 2",
        showWhen: { field: "sg_property_being_sold", is: true },
      },
      { key: "sg_area_representative", label: "Is the client acting as a Singapore area representative?", help: "Area representatives have specific tax obligations even without physical presence.", type: "ternary" },
      { key: "nor_scheme_active", label: "Is the client on Singapore's Not Ordinarily Resident (NOR) scheme?", help: "The NOR scheme time-apportioned employment income for foreign professionals based in Singapore. It closed to new applicants after YA 2020; existing approvals run to the end of their five-year window.",
        type: "ternary",
        showWhen: { field: "tax_residency_status", is: "resident" },
      },
    ],
  },

  // ── Hong Kong ─────────────────────────────────────────────────────────────
  {
    id: "hong-kong",
    title: "Hong Kong",
    description: "Salaries tax, company structures, FSIE regime, and property transactions.",
    focus: "HK",
    fields: [
      { key: "hong_kong_source_income", label: "Does the client earn Hong Kong-source income?", help: "Employment income, business profits, or other income sourced from Hong Kong.", type: "number", placeholder: "e.g. 65000" },
      { key: "hk_company_owned", label: "Does the client own or control a Hong Kong company?", help: "Choose Yes if the client has an ownership or control role in a Hong Kong entity.", type: "ternary" },
      { key: "employer_provided_benefits_hk", label: "Does the client receive employer-provided benefits in Hong Kong?", help: "Housing, share awards, memberships, and similar taxable perquisites.", type: "ternary" },
      { key: "hk_services_rendered_in_hk", label: "Were services physically rendered in Hong Kong?", help: "Determines whether the 60-day exemption or income apportionment applies.", type: "ternary" },
      { key: "hk_passive_offshore_income", label: "Does the Hong Kong company earn passive offshore income?", help: "Dividends, interest, IP royalties, or disposal gains from outside Hong Kong — relevant under the FSIE regime.",
        type: "number", placeholder: "e.g. 200000",
        showWhen: { field: "hk_company_owned", is: true },
      },
      { key: "hk_economic_substance_in_hk", label: "Does the Hong Kong entity maintain economic substance?", help: "Adequate staff, premises, and decision-making in Hong Kong — a key defence under the FSIE regime.",
        type: "ternary",
        showWhen: { field: "hk_company_owned", is: true },
      },
      { key: "hk_family_office_structure", label: "Is there a Hong Kong family office structure?", help: "Eligible single-family offices can apply for profits tax concessions on qualifying transactions.", type: "ternary" },
      { key: "hk_property_transaction", label: "Is the client involved in a Hong Kong property transaction?", help: "Special stamp duty, buyer's stamp duty, or ad valorem duty may apply.", type: "ternary" },
    ],
  },

  // ── UAE ────────────────────────────────────────────────────────────────────
  {
    id: "uae",
    title: "UAE",
    description: "Corporate tax, freezone eligibility, ESR, VAT, and residency certificate signals.",
    focus: "UAE",
    fields: [
      { key: "uae_business_owned", label: "Does the client own or operate a UAE business?", help: "Choose Yes if the client owns a mainland or freezone business entity.", type: "ternary" },
      { key: "uae_taxable_income", label: "What is the estimated UAE taxable income?", help: "Annual taxable amount in AED — corporate tax applies above the small-business threshold.", type: "number", placeholder: "e.g. 525000" },
      { key: "uae_revenue", label: "What is the UAE entity's annual revenue?", help: "Revenue below AED 3M may qualify for the small-business relief.",
        type: "number", placeholder: "e.g. 2500000",
        showWhen: { field: "uae_business_owned", is: true },
      },
      { key: "uae_freezone_entity", label: "Does the client use a UAE freezone entity?", help: "Freezone entities may qualify for 0% corporate tax on qualifying income.", type: "ternary" },
      { key: "uae_non_qualifying_income", label: "Does the freezone entity earn non-qualifying income?", help: "Non-qualifying income (mainland sourced, certain excluded activities) erodes the 0% benefit.",
        type: "number", placeholder: "e.g. 50000",
        showWhen: { field: "uae_freezone_entity", is: true },
      },
      { key: "uae_vat_taxable_supplies", label: "What is the value of taxable supplies for VAT purposes?", help: "Mandatory VAT registration applies at AED 375,000; voluntary at AED 187,500.",
        type: "number", placeholder: "e.g. 400000",
        showWhen: { field: "uae_business_owned", is: true },
      },
      { key: "uae_relevant_activity_esr", label: "Does the entity carry out a relevant activity under ESR?", help: "Economic Substance Regulations require substance in the UAE for certain activities (banking, insurance, IP, etc.).",
        type: "ternary",
        showWhen: { field: "uae_business_owned", is: true },
      },
      { key: "uae_permanent_residence_established", label: "Has permanent residence been established in the UAE?", help: "A golden visa, investor visa, or long-term residency supports the tax residency application.", type: "ternary" },
      { key: "uae_centre_of_interests_in_uae", label: "Is the client's centre of vital interests in the UAE?", help: "Where the client's closest personal and economic ties are — a key factor for residency and treaty tie-breakers.", type: "ternary" },
      { key: "has_other_tax_residency", label: "Does the client hold tax residency in another country?", help: "Choose Yes if the client is still considered tax resident somewhere else as well.", type: "ternary" },
      { key: "tax_residency_certificate_requested", label: "Has a UAE tax residency certificate been requested?", help: "Choose Yes if the application has been submitted to the Federal Tax Authority.", type: "ternary" },
      { key: "tax_residency_certificate", label: "Has the UAE tax residency certificate been issued?", help: "Choose Yes only if the certificate is already in hand — not just applied for.",
        type: "ternary",
        showWhen: { field: "tax_residency_certificate_requested", is: true },
      },
      { key: "mne_global_revenue_eur_millions", label: "What is the MNE group's global revenue (EUR millions)?", help: "Groups with EUR 750M+ revenue face Pillar Two global minimum tax and country-by-country reporting.",
        type: "number", placeholder: "e.g. 800",
        showWhen: { field: "uae_business_owned", is: true },
      },
    ],
  },

  // ── US ────────────────────────────────────────────────────────────────────
  {
    id: "us",
    title: "US Obligations",
    description: "Citizenship-based taxation, substantial presence, PFIC, FBAR, and exit tax.",
    focus: "US",
    fields: [
      { key: "us_substantial_presence_days", label: "What is the weighted substantial presence day count?", help: "The IRS uses a 3-year weighted formula — enter the computed figure.", type: "number", placeholder: "e.g. 183" },
      { key: "closer_connection_claimed", label: "Is a closer-connection exception being claimed?", help: "Available if present under 183 days in the current year and the client maintains a tax home elsewhere.",
        type: "ternary",
        showWhen: { field: "us_substantial_presence_days", provided: true },
      },
      { key: "treaty_tie_breaker_claimed", label: "Is a treaty tie-breaker position being taken?", help: "Used when the client is resident under both the SPT and another country's rules.",
        type: "ternary",
        showWhen: { field: "us_substantial_presence_days", provided: true },
      },
      { key: "pfic_holdings", label: "Does the client hold PFICs or foreign managed funds?", help: "Foreign mutual funds, ETFs, or pooled investments are often classified as PFICs for US persons.", type: "ternary" },
      { key: "pfic_election_made", label: "Has a QEF or mark-to-market election been made?", help: "These elections change how PFIC income is taxed — often more favourable than the default excess-distribution regime.",
        type: "ternary",
        showWhen: { field: "pfic_holdings", is: true },
      },
      { key: "specified_foreign_assets_balance", label: "What is the total value of specified foreign financial assets?", help: "FATCA Form 8938 filing thresholds differ by residency — $200K for overseas filers, $50K for domestic.",
        type: "number", placeholder: "e.g. 250000",
        showWhen: { field: "citizenship", is: "US" },
      },
      { key: "cfc_us_shareholder", label: "Is the client a US shareholder of a controlled foreign corporation?", help: "US persons owning 10%+ of a foreign corporation face Subpart F and GILTI inclusion rules.",
        type: "ternary",
        showWhen: { field: "citizenship", is: "US" },
      },
      { key: "us_situs_assets_value", label: "What is the value of US-situs assets?", help: "Non-US persons with US-situs assets over $60,000 may face US estate tax exposure.",
        type: "number", placeholder: "e.g. 100000",
        showWhen: { field: "citizenship", not: "US" },
      },
      { key: "expatriated_covered", label: "Is the client a covered expatriate?", help: "Former US citizens or long-term residents who meet certain thresholds face the exit tax (mark-to-market) on departure.", type: "ternary" },
      { key: "niit_investment_income", label: "What is the client's net investment income?", help: "The 3.8% Net Investment Income Tax applies above $200K (single) / $250K (married filing jointly).",
        type: "number", placeholder: "e.g. 85000",
        showWhen: { field: "citizenship", is: "US" },
      },
      { key: "us_state_residency", label: "Which US state claims the client as resident?", help: "Some states (CA, NY, VA, NM, SC) impose ongoing tax obligations even after moving abroad.",
        type: "us_state",
        showWhen: { field: "citizenship", is: "US" },
      },
    ],
  },
];

export const FIELD_MAP = Object.fromEntries(
  GROUPS.flatMap((group) => group.fields.map((field) => [field.key, field])),
);

export const GROUP_FIELD_KEYS = Object.fromEntries(
  GROUPS.map((group) => [group.id, group.fields.map((field) => field.key)]),
);

export const PRESETS = {
  blank: { assessmentLabel: "", focus: [], answers: { ...DEFAULT_STATE } },
  "au-expat": {
    assessmentLabel: "Australian Expat Review",
    focus: ["AU"],
    answers: {
      ...DEFAULT_STATE,
      days_in_country: 185,
      domicile_country: "AU",
      residency_country: "AU",
      tax_residency_status: "non_resident",
      australian_source_income: 48000,
      australian_property_owned: true,
      permanent_abode_outside_country: false,
      strong_personal_economic_ties_in_country: true,
      dual_tax_residency: true,
    },
  },
  "uae-move": {
    assessmentLabel: "UAE Transition Review",
    focus: ["UAE"],
    answers: {
      ...DEFAULT_STATE,
      days_in_country: 190,
      residency_country: "UAE",
      tax_residency_status: "resident",
      uae_business_owned: true,
      uae_taxable_income: 525000,
      has_other_tax_residency: false,
      tax_residency_certificate_requested: true,
    },
  },
  "us-citizen": {
    assessmentLabel: "US Citizen Abroad Review",
    focus: ["US", "AU"],
    answers: {
      ...DEFAULT_STATE,
      citizenship: "US",
      residency_country: "AU",
      tax_residency_status: "resident",
      foreign_source_income: 145000,
      foreign_financial_accounts_balance: 42000,
      pfic_holdings: true,
    },
  },
};

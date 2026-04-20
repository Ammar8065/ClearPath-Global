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

export const DEFAULT_STATE = {
  days_in_country: null,
  citizenship: "",
  domicile_country: "",
  residency_country: "",
  tax_residency_status: "",
  australian_source_income: null,
  australian_property_owned: null,
  permanent_abode_outside_country: null,
  strong_personal_economic_ties_in_country: null,
  eligible_commonwealth_superannuation_member: null,
  singapore_source_income: null,
  sg_company_owned: null,
  sg_director_fees: null,
  employment_straddles_two_years: null,
  total_days_in_country: null,
  hong_kong_source_income: null,
  hk_company_owned: null,
  employer_provided_benefits_hk: null,
  uae_business_owned: null,
  uae_taxable_income: null,
  uae_freezone_entity: null,
  uae_non_qualifying_income: null,
  has_other_tax_residency: null,
  tax_residency_certificate_requested: null,
  tax_residency_certificate: null,
  foreign_source_income: null,
  foreign_financial_accounts_balance: null,
  pfic_holdings: null,
  us_substantial_presence_days: null,
  dual_tax_residency: null,
  treaty_relief_claimed: null,
  asset_location: "",
};

export const GROUPS = [
  {
    id: "core",
    title: "Core Profile",
    description: "Start with the client's main residence, citizenship, and overall tax position.",
    alwaysVisible: true,
    open: true,
    fields: [
      { key: "days_in_country", label: "Relevant days present", help: "Enter the day count that matters for this residency review.", type: "number", placeholder: "e.g. 183" },
      { key: "citizenship", label: "Citizenship being assessed", help: "Use the citizenship most relevant to the current review.", type: "text", placeholder: "e.g. US" },
      { key: "domicile_country", label: "Domicile country", help: "Useful for domicile-based residency tests such as Australia.", type: "jurisdiction" },
      { key: "residency_country", label: "Current residency country", help: "Where the client is currently living or treated as resident.", type: "jurisdiction" },
      { key: "tax_residency_status", label: "Current tax residency status", help: "Use this when you already know how the client is currently being treated.", type: "tax_status" },
      { key: "asset_location", label: "Main asset location", help: "Use the jurisdiction of the key property or investment relevant to this review.", type: "jurisdiction" },
    ],
  },
  {
    id: "cross-border",
    title: "Cross-Border Risk Signals",
    description: "Capture the high-level facts that often drive treaty and foreign-income issues.",
    alwaysVisible: true,
    open: true,
    fields: [
      { key: "foreign_source_income", label: "Foreign-source income", help: "Enter the annual foreign-source income amount if it is relevant.", type: "number", placeholder: "e.g. 145000" },
      { key: "foreign_financial_accounts_balance", label: "Foreign financial accounts balance", help: "Use the highest aggregate balance if foreign account reporting may matter.", type: "number", placeholder: "e.g. 42000" },
      { key: "dual_tax_residency", label: "Two countries currently claim tax residency", help: "Choose Yes when the client appears resident in more than one jurisdiction.", type: "ternary" },
      { key: "treaty_relief_claimed", label: "Treaty relief already claimed", help: "Choose Yes if the client has already relied on treaty tie-breaker or treaty benefits.", type: "ternary" },
    ],
  },
  {
    id: "australia",
    title: "Australia Exposure",
    description: "Only shown when Australia is in scope or when Australian facts have been entered.",
    focus: "AU",
    fields: [
      { key: "australian_source_income", label: "Australian-source income", help: "Include rent, dividends, salary, interest, or other Australian-source amounts.", type: "number", placeholder: "e.g. 48000" },
      { key: "australian_property_owned", label: "Owns Australian property", help: "Includes a home, rental property, or other real estate in Australia.", type: "ternary" },
      { key: "permanent_abode_outside_country", label: "Permanent abode outside Australia established", help: "Choose Yes if the client has clearly established a permanent home outside Australia.", type: "ternary" },
      { key: "strong_personal_economic_ties_in_country", label: "Strong ties remain in Australia", help: "Examples include close family, work, or significant financial connections in Australia.", type: "ternary" },
      { key: "eligible_commonwealth_superannuation_member", label: "Eligible Commonwealth superannuation member", help: "Use this when the client falls within the Commonwealth superannuation residency rules.", type: "ternary" },
    ],
  },
  {
    id: "singapore",
    title: "Singapore Exposure",
    description: "Use when Singapore residence, income, or company exposure may be relevant.",
    focus: "SG",
    fields: [
      { key: "singapore_source_income", label: "Singapore-source income", help: "Enter salary, consulting, or other Singapore-source income if relevant.", type: "number", placeholder: "e.g. 80000" },
      { key: "sg_company_owned", label: "Owns or controls a Singapore company", help: "Choose Yes if the client owns or controls a Singapore-incorporated entity.", type: "ternary" },
      { key: "sg_director_fees", label: "Singapore director fees", help: "Enter director fees received from a Singapore company.", type: "number", placeholder: "e.g. 15000" },
      { key: "employment_straddles_two_years", label: "Employment spans two calendar years", help: "Relevant to certain IRAS residency concessions.", type: "ternary" },
      { key: "total_days_in_country", label: "Total days in Singapore across the review period", help: "Use the total day count when the test looks across a broader period than a single year.", type: "number", placeholder: "e.g. 190" },
    ],
  },
  {
    id: "hong-kong",
    title: "Hong Kong Exposure",
    description: "Use when Hong Kong salary, benefits, or company structures are in play.",
    focus: "HK",
    fields: [
      { key: "hong_kong_source_income", label: "Hong Kong-source income", help: "Enter employment or other Hong Kong-source income if relevant.", type: "number", placeholder: "e.g. 65000" },
      { key: "hk_company_owned", label: "Owns or controls a Hong Kong company", help: "Choose Yes if the client owns or controls a Hong Kong entity.", type: "ternary" },
      { key: "employer_provided_benefits_hk", label: "Receives Hong Kong employment benefits", help: "Examples include housing, memberships, share awards, and similar benefits.", type: "ternary" },
    ],
  },
  {
    id: "uae",
    title: "UAE Exposure",
    description: "Use for UAE residency certificate, business, and freezone questions.",
    focus: "UAE",
    fields: [
      { key: "uae_business_owned", label: "Owns or operates a UAE business", help: "Choose Yes if the client owns a UAE mainland or freezone business.", type: "ternary" },
      { key: "uae_taxable_income", label: "Estimated UAE taxable income", help: "Enter the annual taxable amount in AED if known.", type: "number", placeholder: "e.g. 525000" },
      { key: "uae_freezone_entity", label: "Uses a UAE freezone entity", help: "Relevant for freezone tax treatment and qualifying income analysis.", type: "ternary" },
      { key: "uae_non_qualifying_income", label: "UAE non-qualifying income", help: "Use this if freezone eligibility may be affected by non-qualifying income.", type: "number", placeholder: "e.g. 50000" },
      { key: "has_other_tax_residency", label: "Has tax residency in another country", help: "Choose Yes if the client is still tax resident somewhere else as well.", type: "ternary" },
      { key: "tax_residency_certificate_requested", label: "UAE tax residency certificate requested", help: "Choose Yes if a UAE tax residency certificate has been applied for.", type: "ternary" },
      { key: "tax_residency_certificate", label: "UAE tax residency certificate already issued", help: "Choose Yes only if the certificate is already in hand.", type: "ternary" },
    ],
  },
  {
    id: "us",
    title: "US Obligations",
    description: "Use when US citizenship or US day-count exposure might matter.",
    focus: "US",
    fields: [
      { key: "us_substantial_presence_days", label: "US substantial presence day count", help: "Use the weighted day-count figure relevant to the substantial presence test.", type: "number", placeholder: "e.g. 183" },
      { key: "pfic_holdings", label: "Holds PFICs or foreign managed funds", help: "Choose Yes if the client holds foreign funds, ETFs, or similar pooled investments that may be PFICs.", type: "ternary" },
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
      asset_location: "AU",
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
      asset_location: "UAE",
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
      asset_location: "AU",
    },
  },
};

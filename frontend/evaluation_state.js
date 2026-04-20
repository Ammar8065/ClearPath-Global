/* Pure helpers for the private-assessment flow.
   No DOM access, no module-level mutable state.
   Every function takes `answers` and/or `focusJurisdictions` explicitly. */

import { JURISDICTIONS } from "./core.js";
import {
  DEFAULT_STATE,
  FIELD_MAP,
  FOCUS_OPTIONS,
  GROUP_FIELD_KEYS,
  GROUPS,
  TAX_RESIDENCY_OPTIONS,
} from "./evaluation_config.js";

export const CORE_PRIORITY_KEYS = [
  "days_in_country",
  "citizenship",
  "residency_country",
  "tax_residency_status",
];

export const FOCUS_PRIORITY_KEYS = {
  AU: [
    "australian_source_income",
    "australian_property_owned",
    "permanent_abode_outside_country",
    "strong_personal_economic_ties_in_country",
  ],
  SG: [
    "singapore_source_income",
    "total_days_in_country",
    "sg_company_owned",
  ],
  HK: [
    "hong_kong_source_income",
    "hk_company_owned",
    "employer_provided_benefits_hk",
  ],
  UAE: [
    "uae_business_owned",
    "has_other_tax_residency",
    "tax_residency_certificate_requested",
  ],
  US: [
    "us_substantial_presence_days",
    "pfic_holdings",
    "foreign_financial_accounts_balance",
  ],
};

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function focusLabelList(codes) {
  return codes.map((code) => FOCUS_OPTIONS.find((option) => option.value === code)?.label || code).join(", ");
}

export function isValueProvided(field, value) {
  if (field.type === "ternary") return value === true || value === false;
  if (field.type === "number") return value !== null && value !== "" && Number.isFinite(Number(value));
  return typeof value === "string" ? value.trim() !== "" : value !== null && value !== undefined;
}

export function buildPayload(sourceAnswers) {
  const payload = {};
  Object.entries(FIELD_MAP).forEach(([key, field]) => {
    const value = sourceAnswers[key];
    if (!isValueProvided(field, value)) return;
    payload[key] = field.type === "number" ? Number(value) : value;
  });
  return payload;
}

export function providedFactCount(sourceAnswers) {
  return Object.entries(FIELD_MAP).filter(([key, field]) => isValueProvided(field, sourceAnswers[key])).length;
}

export function inferFocusFromAnswers(sourceAnswers, focusJurisdictions) {
  const derived = new Set(focusJurisdictions);
  GROUPS.forEach((group) => {
    if (!group.focus) return;
    const hasAnswers = GROUP_FIELD_KEYS[group.id].some((key) => isValueProvided(FIELD_MAP[key], sourceAnswers[key]));
    if (hasAnswers) derived.add(group.focus);
  });
  return derived;
}

export function groupShouldShow(group, answers, focusJurisdictions) {
  if (group.alwaysVisible) return true;
  if (group.focus && focusJurisdictions.has(group.focus)) return true;
  return GROUP_FIELD_KEYS[group.id].some((key) => isValueProvided(FIELD_MAP[key], answers[key]));
}

export function answeredCountForGroup(group, sourceAnswers) {
  return group.fields.filter((field) => isValueProvided(field, sourceAnswers[field.key])).length;
}

export function uniquePriorityKeys(focusCodes) {
  return [...new Set([
    ...CORE_PRIORITY_KEYS,
    ...focusCodes.flatMap((code) => FOCUS_PRIORITY_KEYS[code] || []),
  ])].filter((key) => FIELD_MAP[key]);
}

export function missingPriorityFields(sourceAnswers, focusCodes) {
  return uniquePriorityKeys(focusCodes)
    .filter((key) => !isValueProvided(FIELD_MAP[key], sourceAnswers[key]))
    .map((key) => FIELD_MAP[key]);
}

export function formatFieldValue(field, value) {
  if (field.type === "ternary") return value ? "Yes" : "No";
  if (field.type === "number") return new Intl.NumberFormat().format(Number(value));
  if (field.type === "jurisdiction") {
    return JURISDICTIONS.find((option) => option.value === value)?.label || value;
  }
  if (field.type === "tax_status") {
    return TAX_RESIDENCY_OPTIONS.find((option) => option.value === value)?.label || value;
  }
  return String(value);
}

export function summarizeKnownFacts(sourceAnswers, limit = 8) {
  return Object.entries(FIELD_MAP)
    .filter(([key, field]) => isValueProvided(field, sourceAnswers[key]))
    .slice(0, limit)
    .map(([key, field]) => ({
      key,
      label: field.label,
      value: formatFieldValue(field, sourceAnswers[key]),
    }));
}

export function payloadToAnswers(payload) {
  const nextAnswers = { ...DEFAULT_STATE };
  Object.entries(FIELD_MAP).forEach(([key, field]) => {
    if (!(key in payload)) return;
    if (field.type === "number") nextAnswers[key] = payload[key] === "" ? null : Number(payload[key]);
    else if (field.type === "ternary") nextAnswers[key] = payload[key] === true ? true : payload[key] === false ? false : null;
    else nextAnswers[key] = payload[key] ?? "";
  });
  return nextAnswers;
}

/** "input_trust_level" -> "Input trust level" — several backend catalogs
 * (finding categories, control categories, evidence keys) are raw snake_case
 * identifiers with no fixed vocabulary, so this formats them without a
 * per-value i18n map. */
export function formatSnakeCase(value: string): string {
  const spaced = value.replace(/_/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

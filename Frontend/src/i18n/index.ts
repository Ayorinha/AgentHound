export const NAMESPACES = ["common", "layout", "home"] as const satisfies readonly string[];

export type Namespace = (typeof NAMESPACES)[number];

export const LOCALES = ["en", "es"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_COOKIE = "agenthound-lang";

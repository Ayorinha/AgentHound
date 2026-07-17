"use client";
import { useRef, useTransition } from "react";
import { useTranslations, useLocale } from "next-intl";
import { setLocale } from "@/app/actions/setLocale";
import type { Locale } from "@/i18n";
import { applyAlpha, skinVars } from "@telefonica/mistica";

type Lang = Locale;

function LanguageSelector() {
  const t = useTranslations("layout");
  const locale = useLocale();
  const currentLang: Lang = locale.startsWith("es") ? "es" : "en";
  const [isPending, startTransition] = useTransition();

  const enRef = useRef<HTMLButtonElement>(null);
  const esRef = useRef<HTMLButtonElement>(null);

  const changeLanguage = (target: Lang) => {
    startTransition(() => setLocale(target));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    const navKeys = ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"];
    if (!navKeys.includes(e.key)) return;
    e.preventDefault();
    const target: Lang = currentLang === "en" ? "es" : "en";
    changeLanguage(target);
    (target === "en" ? enRef : esRef).current?.focus();
  };

  const baseClass = "px-3 py-1 rounded-full transition-colors";

  const buttonStyle = (active: boolean): React.CSSProperties => ({
    backgroundColor: active ? skinVars.colors.brand : "transparent",
    color: active ? skinVars.colors.textButtonPrimary : skinVars.colors.textSecondary,
    fontWeight: active ? 700 : 500,
  });

  return (
    <div
      className={`rounded-full flex items-center${isPending ? " opacity-60 pointer-events-none" : ""}`}
      style={{ backgroundColor: applyAlpha(skinVars.rawColors.backgroundContainer, 0.8) }}
      role="radiogroup"
      aria-label={t("languageSelector")}
    >
      <button
        ref={enRef}
        type="button"
        onClick={() => changeLanguage("en")}
        onKeyDown={handleKeyDown}
        tabIndex={currentLang === "en" ? 0 : -1}
        className={`${baseClass}${currentLang === "en" ? "" : " cursor-pointer"}`}
        style={buttonStyle(currentLang === "en")}
        role="radio"
        aria-checked={currentLang === "en"}
        aria-label="English"
        lang="en"
      >
        EN
      </button>
      <button
        ref={esRef}
        type="button"
        onClick={() => changeLanguage("es")}
        onKeyDown={handleKeyDown}
        tabIndex={currentLang === "es" ? 0 : -1}
        className={`${baseClass}${currentLang === "es" ? "" : " cursor-pointer"}`}
        style={buttonStyle(currentLang === "es")}
        role="radio"
        aria-checked={currentLang === "es"}
        aria-label="Español"
        lang="es"
      >
        ES
      </button>
    </div>
  );
}

export default LanguageSelector;

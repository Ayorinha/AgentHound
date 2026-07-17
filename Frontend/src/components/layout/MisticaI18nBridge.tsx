"use client";
import { ThemeContextProvider, skinVars } from "@telefonica/mistica";
import { useLocale } from "next-intl";
import { appSkin } from "@/lib/theme";
import type { ThemeConfig } from "@telefonica/mistica";
import { useCallback, useMemo, useSyncExternalStore } from "react";
import { ColorSchemeContext, colorSchemeListeners, subscribeColorScheme, getColorSchemeSnapshot, getServerColorSchemeSnapshot } from "@/contexts/ColorSchemeContext";
import NextLink from "next/link";

const LOCALE_MAP = { en: "en-GB", es: "es-ES" } as const;
const REGION_MAP = { en: "GB", es: "ES" } as const;
const MISTICA_LINK = { type: "Next14" as const, Component: NextLink };

// Sets the page's base font/background/text color from the active skin. Component styling
// should use skinVars directly (inline style or Mistica props) rather than adding tokens here.
const GlobalStyles = () => (
  <style>{`
    body {
      font-family: 'OnAir', 'Helvetica', 'Arial', sans-serif;
      background-color: ${skinVars.colors.background};
      color: ${skinVars.colors.textPrimary};
    }
  `}</style>
);

function MisticaI18nBridge({ children }: { children: React.ReactNode }) {
  const locale = useLocale();
  const lang = locale.startsWith("es") ? "es" : "en";

  const colorScheme = useSyncExternalStore(subscribeColorScheme, getColorSchemeSnapshot, getServerColorSchemeSnapshot);

  const toggleColorScheme = useCallback(() => {
    const next = colorScheme === "dark" ? "light" : "dark";
    localStorage.setItem("colorScheme", next);
    colorSchemeListeners.forEach(cb => cb());
  }, [colorScheme]);

  const theme: ThemeConfig = useMemo(
    () => ({
      skin: appSkin,
      colorScheme,
      i18n: {
        locale: LOCALE_MAP[lang],
        phoneNumberFormattingRegionCode: REGION_MAP[lang],
      },
      Link: MISTICA_LINK,
    }),
    [lang, colorScheme],
  );

  return (
    <ColorSchemeContext.Provider value={{ colorScheme, toggleColorScheme }}>
      <ThemeContextProvider theme={theme}>
        <GlobalStyles />
        {children}
      </ThemeContextProvider>
    </ColorSchemeContext.Provider>
  );
}

export default MisticaI18nBridge;

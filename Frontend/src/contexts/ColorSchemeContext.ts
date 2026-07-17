import { createContext, useContext } from "react";

export type ColorScheme = "light" | "dark" | "auto";

export const ColorSchemeContext = createContext<{
  colorScheme: ColorScheme;
  toggleColorScheme: () => void;
}>({
  colorScheme: "light",
  toggleColorScheme: () => {},
});

export const useColorScheme = () => useContext(ColorSchemeContext);

export const colorSchemeListeners = new Set<() => void>();

export const subscribeColorScheme = (callback: () => void) => {
  colorSchemeListeners.add(callback);
  return () => { colorSchemeListeners.delete(callback); };
};

export const getColorSchemeSnapshot = (): ColorScheme => {
  const s = localStorage.getItem("colorScheme");
  return s === "light" || s === "dark" ? s : "light";
};

export const getServerColorSchemeSnapshot = (): ColorScheme => "light";

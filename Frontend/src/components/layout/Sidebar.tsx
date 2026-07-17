"use client";
import Image from "next/image";
import {
  IconButton,
  IconMoonRegular,
  IconSunRegular,
  Inline,
  skinVars,
  Stack,
  Text2,
  Text4,
  Tooltip,
  useTheme,
} from "@telefonica/mistica";
import IconSidenavCollapseRegular from "@/components/ui/icons/IconSidenavCollapseRegular";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/constants";
import { backgroundSelected } from "@/lib/cyberSkin";
import { useColorScheme } from "@/contexts/ColorSchemeContext";

import type { NavItem, SidebarProps } from "@/types/Common";
import { useTranslations } from "next-intl";

function isItemActive(href: string, pathname: string): boolean {
  return pathname === href || (href !== "/" && pathname.startsWith(href));
}

/** Highlight (active or hover) is painted by a CSS `:hover` rule rather than
 * React state, so pointer movement over the nav doesn't re-render anything. */
const SIDEBAR_LINK_STYLES = `
  .sidebar-link {
    cursor: pointer;
    position: relative;
    isolation: isolate;
    display: flex;
    height: 44px;
    min-height: 44px;
    align-items: center;
    justify-content: space-between;
    padding-left: 16px;
    padding-right: 16px;
    border-radius: ${skinVars.borderRadii.button};
  }
  .sidebar-link-highlight {
    position: absolute;
    inset: 0;
    z-index: -1;
    border-radius: ${skinVars.borderRadii.button};
    opacity: 0;
    transition: opacity 0.15s ease;
  }
  .sidebar-link:hover .sidebar-link-highlight,
  .sidebar-link[aria-current="page"] .sidebar-link-highlight {
    opacity: 1;
  }
  .sidebar-link-marker {
    position: absolute;
    left: 0;
    top: 12px;
    width: 2px;
    height: 20px;
    border-radius: ${skinVars.borderRadii.button};
    background-color: ${skinVars.colors.controlActivated};
  }
`;

function SidebarLink({ item, active, label }: { item: NavItem; active: boolean; label: string }) {
  const Icon = item.icon;
  const { isDarkMode } = useTheme();

  return (
    <Link href={item.href} aria-current={active ? "page" : undefined} className="sidebar-link">
      <span
        aria-hidden
        className="sidebar-link-highlight"
        style={{ backgroundColor: isDarkMode ? backgroundSelected.dark : backgroundSelected.light }}
      />
      {active && <span aria-hidden className="sidebar-link-marker" />}
      <Inline space={8} alignItems="center">
        <Icon color={skinVars.colors.textPrimary} size={20} />
        <Text2 regular color={skinVars.colors.textPrimary}>{label}</Text2>
      </Inline>
    </Link>
  );
}

/** Sun/moon switch for the color scheme. The app defaults to light; this is the
 * only entry point to dark mode, so the `isDarkMode` branches around the app
 * stay reachable. */
function ThemeToggle() {
  const t = useTranslations();
  const { colorScheme, toggleColorScheme } = useColorScheme();
  const isDark = colorScheme === "dark";

  return (
    <IconButton
      Icon={isDark ? IconSunRegular : IconMoonRegular}
      type="neutral"
      backgroundType="transparent"
      small
      aria-label={t(isDark ? "layout.sidebar.themeToLight" : "layout.sidebar.themeToDark")}
      onPress={toggleColorScheme}
    />
  );
}

function Sidebar({ name = "AgentHound", className = "" }: SidebarProps) {
  const pathname = usePathname() ?? "";
  const t = useTranslations();

  return (
    <aside
      className={`flex h-full flex-col ${className}`}
      style={{ width: 240, backgroundColor: skinVars.colors.background, color: skinVars.colors.textPrimary }}
    >
      <style>{SIDEBAR_LINK_STYLES}</style>

      {/* Header */}
      <Stack space={8}>
        <div className="pt-6 px-5">
          <Inline space={8} alignItems="center">
            <Image src="/logo.svg" width={24} height={24} loading="eager" className="shrink-0" alt={`${name} Logo`} priority />
            <Text4 light color={skinVars.colors.textPrimary}>{name}</Text4>
          </Inline>
        </div>
        <div className="px-5 pb-6">
          <Tooltip description={t("common.comingSoon")} target={
            <IconButton
              Icon={IconSidenavCollapseRegular}
              type="neutral"
              backgroundType="transparent"
              small
              aria-label={t("layout.sidebar.collapse")}
              onPress={() => {}}
            />
          } />
        </div>
      </Stack>

      {/* Navigation */}
      <nav className="flex-1 px-2">
        <Stack space={8}>
          <div className="px-4">
            <Text2 medium color={skinVars.colors.textSecondary}>{t("layout.sidebar.testsSection")}</Text2>
          </div>
          <Stack space={0}>
            {NAV_ITEMS.map((item) => (
              <SidebarLink key={item.href} item={item} active={isItemActive(item.href, pathname)} label={t(item.labelKey)} />
            ))}
          </Stack>
        </Stack>
      </nav>

      {/* Footer */}
      <div className="px-5 pb-6">
        <ThemeToggle />
      </div>
    </aside>
  );
}

export default Sidebar;

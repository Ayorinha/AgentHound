"use client";
import Image from "next/image";
import React from "react";
import { Align, Inline, Stack, Text1, Title3, skinVars } from "@telefonica/mistica";
import { useTranslations } from "next-intl";
const MIN_DESKTOP_WIDTH = 1024;

function subscribe(callback: () => void) {
  const mq = window.matchMedia(`(min-width: ${MIN_DESKTOP_WIDTH}px)`);
  mq.addEventListener("change", callback);
  return () => mq.removeEventListener("change", callback);
}

function getSnapshot() {
  return window.matchMedia(`(min-width: ${MIN_DESKTOP_WIDTH}px)`).matches;
}

function useIsDesktop() {
  return React.useSyncExternalStore(subscribe, getSnapshot, () => true);
}

function DesktopOnlyGuard({ children }: { children: React.ReactNode }) {
  const isDesktop = useIsDesktop();
  const t = useTranslations("layout");

  if (isDesktop) {
    return <>{children}</>;
  }

  return (
    <div className="h-screen w-full px-6 text-center" style={{ backgroundColor: skinVars.colors.background }}>
      <Align x="center" y="center" height="100%">
      <div className="max-w-md rounded-2xl p-10" style={{ backgroundColor: skinVars.colors.backgroundContainer }}>
        <Stack space={24}>
          <Align x="center">
            <Image
              src="/logo.svg"
              alt="AgentHound"
              width={64}
              height={64}
              loading="eager"
              className="h-16 w-16"
            />
          </Align>
          <Title3 as="h1">{t("desktopGuard.title")}</Title3>
          <div className="leading-relaxed">
            <Text1 regular color={skinVars.colors.textSecondary}>{t("desktopGuard.description")}</Text1>
          </div>
          <Align x="center">
            <div className="rounded-full px-4 py-2" style={{ backgroundColor: skinVars.colors.brandLow }}>
              <Inline space={8} alignItems="center">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                  style={{ color: skinVars.colors.brand }}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                <Text1 medium as="span" color={skinVars.colors.brand}>
                  {t("desktopGuard.minWidth", { width: MIN_DESKTOP_WIDTH })}
                </Text1>
              </Inline>
            </div>
          </Align>
        </Stack>
      </div>
      </Align>
    </div>
  );
}

export default DesktopOnlyGuard;

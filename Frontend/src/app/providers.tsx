"use client";

import MisticaI18nBridge from "@/components/layout/MisticaI18nBridge";
import DesktopOnlyGuard from "@/components/layout/DesktopOnlyGuard";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <MisticaI18nBridge>
      <DesktopOnlyGuard>{children}</DesktopOnlyGuard>
    </MisticaI18nBridge>
  );
}

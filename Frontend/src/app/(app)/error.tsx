"use client";

import { useEffect } from "react";
import { useTranslations } from "next-intl";
import { logger } from "@/lib/logger";
import InlineError from "@/components/ui/InlineError";

export default function Error({ error, retry }: { error: Error & { digest?: string }; retry: () => void }) {
  const t = useTranslations();

  useEffect(() => {
    logger.error(error);
  }, [error]);

  return (
    <div className="p-8">
      <InlineError message={t("common.error.description")} onRetry={async () => { retry(); }} />
    </div>
  );
}

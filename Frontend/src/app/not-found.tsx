"use client";

import { Title3 } from "@telefonica/mistica";
import { useTranslations } from "next-intl";

export default function NotFound() {
  const t = useTranslations("common");
  return (
    <main className="p-8">
      <Title3 as="h1">{t("noResults")}</Title3>
    </main>
  );
}

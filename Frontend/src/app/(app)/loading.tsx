"use client";
import { Box, Inline, Spinner, Text2, skinVars } from "@telefonica/mistica";
import { useTranslations } from "next-intl";

export default function Loading() {
  const t = useTranslations();

  return (
    <Box padding={32}>
      <Inline space={8} alignItems="center">
        <Spinner size={20} color={skinVars.colors.brand} />
        <Text2 regular color={skinVars.colors.textSecondary}>{t("common.loading.generic")}</Text2>
      </Inline>
    </Box>
  );
}

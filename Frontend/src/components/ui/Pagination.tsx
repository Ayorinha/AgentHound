// TODO: temporary custom pagination built from Mistica primitives to match the Figma design.
// Replace with the Cyber pagination component once it exists in the design system.
import { Circle, IconButton, IconChevronLeftRegular, IconChevronRightRegular, Inline, Text2, Touchable, skinVars } from "@telefonica/mistica";
import { useTranslations } from "next-intl";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  compact?: boolean;
}

type PageItem = number | "ellipsis";

function getPageItems(current: number, total: number): PageItem[] {
  if (total <= 5) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  if (current <= 4) {
    return [1, 2, 3, 4, "ellipsis", total];
  }
  if (current >= total - 3) {
    return [1, "ellipsis", total - 3, total - 2, total - 1, total];
  }
  return [1, "ellipsis", current - 1, current, current + 1, "ellipsis", total];
}

function Pagination({ currentPage, totalPages, onPageChange, compact = false }: PaginationProps) {
  const t = useTranslations("common");

  if (totalPages <= 1) {
    return null;
  }

  const items = getPageItems(currentPage, totalPages);
  const size = compact ? 24 : 32;

  return (
    <div>
    <Inline space={compact ? 8 : 16} alignItems="center">
      {currentPage > 1 && (
        <IconButton
          Icon={IconChevronLeftRegular}
          onPress={() => onPageChange(currentPage - 1)}
          aria-label={t("pagination.previous")}
          type="neutral"
          backgroundType="transparent"
          small={compact}
        />
      )}

      <Inline space={compact ? 12 : 24} alignItems="center">
        {items.map((item, index) =>
          item === "ellipsis" ? (
            <Text2 key={`ellipsis-${index}`} medium color={skinVars.colors.textSecondary}>
              …
            </Text2>
          ) : item === currentPage ? (
            <Circle key={item} backgroundColor={skinVars.colors.brand} size={size}>
              <Text2 medium color={skinVars.colors.textButtonPrimary}>{item}</Text2>
            </Circle>
          ) : (
            <Touchable
              key={item}
              onPress={() => onPageChange(item)}
              aria-label={t("pagination.page", { page: item })}
            >
              <Text2 medium color={skinVars.colors.textPrimary}>{item}</Text2>
            </Touchable>
          ),
        )}
      </Inline>

      {currentPage < totalPages && (
        <IconButton
          Icon={IconChevronRightRegular}
          onPress={() => onPageChange(currentPage + 1)}
          aria-label={t("pagination.next")}
          type="neutral"
          backgroundType="transparent"
          small={compact}
        />
      )}
    </Inline>
    </div>
  );
}

export default Pagination;

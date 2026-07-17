import {
  Box,
  ButtonPrimary,
  ButtonSecondary,
  IconArrowLineLeftLight,
  IconArrowLineRightRegular,
  Inline,
  skinVars,
} from "@telefonica/mistica";
import { useTranslations } from "next-intl";

interface WizardFooterProps {
  onPrevious?: () => void;
  onNext?: () => void;
  disablePrevious?: boolean;
  disableNext?: boolean;
  hideNext?: boolean;
  nextLabel?: string;
  isNextLoading?: boolean;
}

function WizardFooter({ onPrevious, onNext, disablePrevious = false, disableNext = false, hideNext = false, nextLabel, isNextLoading = false }: WizardFooterProps) {
  const t = useTranslations("wizard");
  const resolvedNextLabel = nextLabel ?? t("next");
  return (
    <div className="rounded-full mt-auto w-full" style={{ backgroundColor: skinVars.colors.backgroundContainer, borderColor: skinVars.colors.border, borderWidth: 1, borderStyle: "solid" }}>
      <Box paddingX={32} paddingY={20}>
        <Inline space="between" alignItems="center">
          <ButtonSecondary onPress={() => onPrevious?.()} disabled={disablePrevious} StartIcon={IconArrowLineLeftLight}>
            {t("back")}
          </ButtonSecondary>
          {!hideNext && (
            <ButtonPrimary onPress={() => onNext?.()} disabled={disableNext} showSpinner={isNextLoading} EndIcon={IconArrowLineRightRegular}>
              {resolvedNextLabel}
            </ButtonPrimary>
          )}
        </Inline>
      </Box>
    </div>
  );
}

export default WizardFooter;

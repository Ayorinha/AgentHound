"use client";
import { useState } from "react";
import { ButtonSecondary, Stack, Text1, skinVars } from "@telefonica/mistica";
import { useTranslations } from "next-intl";

interface InlineErrorProps {
    message: string;
    onRetry?: () => void | Promise<void>;
    className?: string;
}

function InlineError({ message, onRetry, className = "" }: InlineErrorProps) {
    const t = useTranslations("common");
    const [isRetrying, setIsRetrying] = useState(false);

    const handleRetry = async () => {
        setIsRetrying(true);
        try {
            await onRetry?.();
        } finally {
            setIsRetrying(false);
        }
    };

    return (
        <Stack space={12} className={className}>
            <Text1 regular color={skinVars.colors.error}>{message}</Text1>
            {onRetry && (
                <ButtonSecondary small onPress={handleRetry} showSpinner={isRetrying} disabled={isRetrying}>
                    {t("actions.retry")}
                </ButtonSecondary>
            )}
        </Stack>
    );
}

export default InlineError;

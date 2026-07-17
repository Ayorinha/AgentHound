"use client";
import { Align, Box, IconButton, Inline, Stack, IconTrashCanRegular, Spinner, Text1, Text2, applyAlpha, skinVars } from "@telefonica/mistica";
import { useMemo } from "react";
import { useTranslations } from "next-intl";
import type { UploadStatus } from "@/types/ThreatModel";
import FileIcon, { type FileIconType } from "@/components/ui/icons/FileIcon";

interface FileBoxProps {
  file: File;
  status?: UploadStatus;
  errorMessage?: string;
  onRemove?: () => void;
}

function formatFileSize(size: number): string {
  if (size === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / 1024 ** exponent;
  return `${value.toFixed(value >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

export default function FileBox({ file, status = "success", errorMessage, onRemove }: FileBoxProps) {
  const t = useTranslations("configuration");
  const extension = useMemo(() => {
    const parts = file.name.split(".");
    return parts.length > 1 ? parts.pop()!.toLowerCase() : "";
  }, [file.name]);

  const formattedSize = useMemo(() => formatFileSize(file.size), [file.size]);
  const isUploading = status === "uploading";
  const isError = status === "error";

  const wrapperStyle: React.CSSProperties = isError
    ? { backgroundColor: skinVars.colors.errorLow, borderColor: skinVars.colors.error, color: skinVars.colors.textPrimary }
    : { backgroundColor: skinVars.colors.backgroundContainer, borderColor: skinVars.colors.border, color: skinVars.colors.textPrimary };
  const iconColor = isError ? skinVars.colors.error : skinVars.colors.brand;

  const iconType: FileIconType = useMemo(() => {
    if (!extension) return "default";
    const normalized = extension.toLowerCase();
    if (normalized === "jpeg") return "jpg";
    if (normalized === "yml") return "yaml";
    if (["pdf", "jpg", "png", "mp3", "html", "css", "json", "yaml", "txt"].includes(normalized)) {
      return normalized as FileIconType;
    }
    return "default";
  }, [extension]);

  const renderIcon = () => {
    if (isUploading) {
      return <Spinner size={24} color={skinVars.colors.brand} />;
    }

    return (
      <FileIcon
        type={iconType}
        className="h-[28px] w-[24px]"
        style={{ color: iconColor }}
        aria-hidden
      />
    );
  };

  return (
    <div
      className="group relative flex min-w-[343px] max-w-[343px] h-[80px] flex-col justify-center rounded-2xl border p-4 transition-colors"
      style={wrapperStyle}
    >
      <Inline space={16} alignItems="center">
        <div style={{ height: 28, width: 24 }}>
          <Align x="center" y="center" height="100%">
            {renderIcon()}
          </Align>
        </div>
        <Box paddingRight={40}>
          <Stack space={4}>
            <Text2 medium truncate>{file.name}</Text2>
            {isError ? (
              <Text1 medium truncate color={skinVars.colors.error}>{errorMessage ?? t("uploadError")}</Text1>
            ) : (
              <Text1 regular truncate color={applyAlpha(skinVars.rawColors.textPrimary, 0.8)}>
                {extension ? extension.toUpperCase() : ""}
                {formattedSize ? ` · ${formattedSize}` : ""}
              </Text1>
            )}
          </Stack>
        </Box>
        {onRemove && (
          <div className="absolute right-4 top-4 transition-all">
            <IconButton
              aria-label={t("removeFile")}
              onPress={onRemove}
              Icon={IconTrashCanRegular}
              type={isError ? "danger" : "neutral"}
              backgroundType="transparent"
              small
            />
          </div>
        )}
      </Inline>
    </div>
  );
}

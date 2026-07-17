import type { SVGProps } from "react";

export type FileIconType = "pdf" | "jpg" | "png" | "mp3" | "html" | "css" | "json" | "yaml" | "txt" | "default";

interface FileIconProps extends SVGProps<SVGSVGElement> {
  type: FileIconType;
}

const LABEL_MAP: Record<FileIconType, string> = {
  pdf: "PDF",
  jpg: "JPG",
  png: "PNG",
  mp3: "MP3",
  html: "</>",
  css: "CSS",
  json: "JSON",
  yaml: "YAML",
  txt: "TXT",
  default: "FILE",
};

function renderIconContent(type: FileIconType, label: string) {
  if (type === "json") {
    return (
      <g stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 9.5L6.5 12L9 14.5" />
        <path d="M15 9.5L17.5 12L15 14.5" />
        <path d="M12 8.5V15.5" />
      </g>
    );
  }

  if (type === "txt") {
    return (
      <g stroke="currentColor" strokeWidth="1.2" strokeLinecap="round">
        <line x1="8" y1="9.75" x2="16" y2="9.75" />
        <line x1="8" y1="12.75" x2="16" y2="12.75" />
        <line x1="8" y1="15.75" x2="13.5" y2="15.75" />
      </g>
    );
  }

  return (
    <text
      x="12"
      y="18.5"
      textAnchor="middle"
      fontSize="6.2"
      fontWeight="700"
      fill="currentColor"
      fontFamily="'Inter', 'Helvetica', 'Arial', sans-serif"
    >
      {label}
    </text>
  );
}

export function FileIcon({ type, ...props }: FileIconProps) {
  const label = LABEL_MAP[type] ?? LABEL_MAP.default;

  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <g stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round">
        <path d="M6 2H14L20 8V20C20 21.1046 19.1046 22 18 22H6C4.89543 22 4 21.1046 4 20V4C4 2.89543 4.89543 2 6 2Z" />
        <path d="M14 2V8H20" />
      </g>
      {renderIconContent(type, label)}
    </svg>
  );
}

export default FileIcon;

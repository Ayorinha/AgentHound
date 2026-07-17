"use client";
import type { CSSProperties } from "react";

function ContentLayout({ children, style, paddingTop = 24 }: { children: React.ReactNode; style?: CSSProperties; paddingTop?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100%", paddingTop, ...style }}>
      {children}
    </div>
  );
}

export default ContentLayout;

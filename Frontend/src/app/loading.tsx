"use client";
import { Spinner, skinVars } from "@telefonica/mistica";

export default function Loading() {
  return (
    <div className="flex h-screen items-center justify-center" style={{ backgroundColor: skinVars.colors.background }}>
      <Spinner size={32} color={skinVars.colors.brand} />
    </div>
  );
}

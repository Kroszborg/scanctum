"use client";

import { CustomCursor } from "@/components/landing/custom-cursor";
import { BackgroundCanvas } from "@/components/landing/background-canvas";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <CustomCursor />
      <BackgroundCanvas />
      <div className="flex min-h-screen items-center justify-center relative z-10">
        {children}
      </div>
    </>
  );
}

"use client";

import { HeroSection } from "@/components/landing/hero-section";
import { FeaturesSection } from "@/components/landing/features-section";
import { HowItWorksSection } from "@/components/landing/how-it-works-section";
import { ScanModesSection } from "@/components/landing/scan-modes-section";
import { LogoCarousel } from "@/components/landing/logo-carousel";
import { FooterSection } from "@/components/landing/footer-section";
import { BackgroundCanvas } from "@/components/landing/background-canvas";
import { CustomCursor } from "@/components/landing/custom-cursor";

export default function LandingPage() {
  return (
    <>
      <CustomCursor />
      <BackgroundCanvas />

      <main className="relative">
        <HeroSection />
        <LogoCarousel />
        <FeaturesSection />
        <HowItWorksSection />
        <ScanModesSection />
      </main>

      <FooterSection />
    </>
  );
}

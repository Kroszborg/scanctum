"use client";

import { motion } from "framer-motion";
import { MagneticWrapper } from "./magnetic-wrapper";
import { ChevronRight, Shield, Zap, Eye, Activity } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-6 py-24">
      <div className="max-w-6xl mx-auto text-center relative z-10">

        {/* Main heading */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
          className="text-6xl md:text-8xl font-bold tracking-tight mb-6"
          style={{
            fontFamily: "Bricolage Grotesque",
            background: "linear-gradient(180deg, #e8e0d5 0%, #8a7f74 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          SCANCTUM
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="text-xl md:text-2xl text-[#8a7f74] max-w-3xl mx-auto mb-12 leading-relaxed"
        >
          Modular web application security scanner for modern applications.
          Detect vulnerabilities before attackers do.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <MagneticWrapper intensity={0.8}>
            <a
              href="/login"
              className="group inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-[#f59e0b] text-[#0c0a08] font-semibold text-lg transition-all hover:bg-[#d97706] hover:shadow-lg hover:shadow-[#f59e0b]/20"
            >
              Launch Scanner
              <ChevronRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
            </a>
          </MagneticWrapper>

          <MagneticWrapper intensity={0.8}>
            <a
              href="#features"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-lg border border-[#2c2820] bg-[#141210]/50 text-[#e8e0d5] font-semibold text-lg hover:bg-[#1c1916] transition-all"
            >
              Learn More
            </a>
          </MagneticWrapper>
        </motion.div>

        {/* Feature highlights */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5, ease: "easeOut" }}
          className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-24 pt-12 border-t border-[#1c1916]"
        >
          {[
            { icon: Shield, label: "26+ Modules", desc: "Detection rules" },
            { icon: Zap, label: "Real-time", desc: "Live progress" },
            { icon: Eye, label: "Deep Scans", desc: "5-level depth" },
            { icon: Activity, label: "CVSS Scoring", desc: "Risk assessment" },
          ].map((feature, i) => (
            <div key={i} className="text-center">
              <feature.icon className="w-6 h-6 mx-auto mb-3 text-[#f59e0b]" />
              <p className="text-lg font-semibold text-[#e8e0d5]">{feature.label}</p>
              <p className="text-sm text-[#4a4440] font-mono">{feature.desc}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

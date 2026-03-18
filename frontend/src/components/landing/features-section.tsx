"use client";

import { motion } from "framer-motion";
import { Eye, Crosshair, KeyRound, Globe, FileText, BarChart3, ShieldAlert, Cpu } from "lucide-react";

const features = [
  {
    title: "Passive Detection",
    desc: "Analyze headers, cookies, and configurations without sending payloads. Zero noise, zero impact.",
    color: "#f59e0b",
    icon: Eye,
    size: "large",
  },
  {
    title: "Active Testing",
    desc: "Safe payload injection to detect XSS, SQLi, and injection flaws.",
    color: "#fb923c",
    icon: Crosshair,
    size: "normal",
  },
  {
    title: "Auth Testing",
    desc: "JWT analysis, CSRF checks, and session security validation.",
    color: "#f43f5e",
    icon: KeyRound,
    size: "normal",
  },
  {
    title: "SSRF Detection",
    desc: "Identify server-side request forgery vulnerabilities in real time.",
    color: "#38bdf8",
    icon: Globe,
    size: "normal",
  },
  {
    title: "PDF Reports",
    desc: "Professional VAPT reports with CVSS scores and remediation guidance.",
    color: "#4ade80",
    icon: FileText,
    size: "normal",
  },
  {
    title: "Risk Scoring",
    desc: "Industry-standard CVSS v3.1 severity ratings with contextual analysis.",
    color: "#a78bfa",
    icon: BarChart3,
    size: "large",
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-32 px-6 relative">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <p className="text-sm text-[#f59e0b] font-mono tracking-widest uppercase mb-4">
            Capabilities
          </p>
          <h2 className="text-4xl md:text-5xl font-bold text-[#e8e0d5] mb-6">
            Comprehensive Security Testing
          </h2>
          <p className="text-xl text-[#8a7f74] max-w-2xl mx-auto">
            26 detection modules covering OWASP Top 10 and beyond
          </p>
        </motion.div>

        {/* Bento grid */}
        <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-4 auto-rows-[200px]">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className={`group relative overflow-hidden rounded-2xl border transition-all duration-300 hover:scale-[1.02] ${
                  feature.size === "large" ? "md:col-span-2" : ""
                }`}
                style={{
                  background: `${feature.color}08`,
                  borderColor: `${feature.color}20`,
                }}
              >
                {/* Hover glow */}
                <div
                  className="absolute -right-16 -top-16 h-48 w-48 rounded-full opacity-0 transition-opacity duration-700 group-hover:opacity-100 blur-3xl pointer-events-none"
                  style={{ background: feature.color, opacity: 0 }}
                  onMouseEnter={(e) => { (e.target as HTMLElement).style.opacity = "0.12"; }}
                />

                <div className="relative h-full p-6 flex flex-col justify-between">
                  {/* Icon */}
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110"
                    style={{
                      background: `${feature.color}15`,
                      border: `1px solid ${feature.color}30`,
                    }}
                  >
                    <Icon
                      className="h-5 w-5"
                      style={{ color: feature.color }}
                      strokeWidth={1.5}
                    />
                  </div>

                  {/* Text */}
                  <div>
                    <h3 className="text-base font-semibold text-[#e8e0d5] mb-1.5 leading-snug">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-[#8a7f74] leading-relaxed">
                      {feature.desc}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

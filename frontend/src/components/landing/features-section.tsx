"use client";

import { motion } from "framer-motion";
import { Shield, Code, Lock, Globe, FileText, AlertTriangle } from "lucide-react";

const features = [
  {
    icon: Shield,
    title: "Passive Detection",
    desc: "Analyze headers, cookies, and configurations without sending payloads",
    color: "#f59e0b",
  },
  {
    icon: Code,
    title: "Active Testing",
    desc: "Safe payload injection to detect XSS, SQLi, and injection flaws",
    color: "#fb923c",
  },
  {
    icon: Lock,
    title: "Auth Testing",
    desc: "JWT analysis, CSRF checks, and session security validation",
    color: "#f43f5e",
  },
  {
    icon: Globe,
    title: "SSRF Detection",
    desc: "Identify server-side request forgery vulnerabilities",
    color: "#38bdf8",
  },
  {
    icon: FileText,
    title: "PDF Reports",
    desc: "Professional VAPT reports with CVSS scores and remediation",
    color: "#4ade80",
  },
  {
    icon: AlertTriangle,
    title: "Risk Scoring",
    desc: "Industry-standard CVSS v3.1 severity ratings",
    color: "#a78bfa",
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

        {/* Features grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="group p-8 rounded-xl border border-[#2c2820] bg-[#141210]/50 hover:bg-[#1c1916] transition-all hover:border-[#f59e0b]/30"
            >
              <div
                className="w-12 h-12 rounded-lg flex items-center justify-center mb-6"
                style={{
                  background: `${feature.color}15`,
                  border: `1px solid ${feature.color}30`,
                }}
              >
                <feature.icon className="w-6 h-6" style={{ color: feature.color }} />
              </div>
              <h3 className="text-xl font-semibold text-[#e8e0d5] mb-3">
                {feature.title}
              </h3>
              <p className="text-[#8a7f74] leading-relaxed">
                {feature.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

"use client";

import { motion } from "framer-motion";
import { Terminal, Scan, Clock, CheckCircle } from "lucide-react";

const steps = [
  {
    icon: Terminal,
    title: "Enter Target",
    desc: "Input your target URL and configure scan parameters",
    terminal: "> scanctum --target https://example.com",
  },
  {
    icon: Scan,
    title: "Crawl & Discover",
    desc: "Automated endpoint discovery and parameter mapping",
    terminal: "[*] Crawling... 47 endpoints found",
  },
  {
    icon: Clock,
    title: "Vulnerability Scan",
    desc: "Parallel testing with 26 security modules",
    terminal: "[*] Running: XSS, SQLi, IDOR, SSRF...",
  },
  {
    icon: CheckCircle,
    title: "Report Generation",
    desc: "PDF/JSON reports with CVSS scores and fixes",
    terminal: "[+] Report: vuln-report-2024.pdf",
  },
];

export function HowItWorksSection() {
  return (
    <section className="py-32 px-6 relative bg-[#0a0908]/50">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <p className="text-sm text-[#f59e0b] font-mono tracking-widest uppercase mb-4">
            Workflow
          </p>
          <h2 className="text-4xl md:text-5xl font-bold text-[#e8e0d5] mb-6">
            How Scanning Works
          </h2>
          <p className="text-xl text-[#8a7f74] max-w-2xl mx-auto">
            Four steps from target to comprehensive vulnerability report
          </p>
        </motion.div>

        {/* Steps with terminal */}
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left side - steps */}
          <div className="space-y-8">
            {steps.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.15 }}
                className="flex gap-6"
              >
                <div className="flex-shrink-0">
                  <div className="w-14 h-14 rounded-xl border border-[#2c2820] bg-[#141210] flex items-center justify-center">
                    <step.icon className="w-7 h-7 text-[#f59e0b]" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-[#e8e0d5] mb-2">
                    {step.title}
                  </h3>
                  <p className="text-[#8a7f74]">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Right side - terminal visualization */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.7 }}
            className="relative"
          >
            <div className="rounded-xl border border-[#2c2820] bg-[#0c0a08] overflow-hidden">
              {/* Terminal header */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-[#1c1916] bg-[#141210]">
                <div className="w-3 h-3 rounded-full bg-[#f43f5e]" />
                <div className="w-3 h-3 rounded-full bg-[#f59e0b]" />
                <div className="w-3 h-3 rounded-full bg-[#4ade80]" />
                <span className="ml-4 text-sm text-[#4a4440] font-mono">scanctum — terminal</span>
              </div>

              {/* Terminal content */}
              <div className="p-6 font-mono text-sm space-y-4 min-h-[320px]">
                <motion.div
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: 0.2 }}
                  className="text-[#8a7f74]"
                >
                  <span className="text-[#f59e0b]">$</span> scanctum --target https://example.com --mode full
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: 0.6 }}
                  className="text-[#38bdf8]"
                >
                  [*] Initializing scanner...
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: 1 }}
                  className="text-[#38bdf8]"
                >
                  [*] Crawling target... 47 endpoints discovered
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: 1.4 }}
                  className="space-y-1"
                >
                  <p className="text-[#4ade80]">[+] XSS: 2 vulnerabilities found</p>
                  <p className="text-[#f59e0b]">[!] SQLi: 1 potential issue</p>
                  <p className="text-[#8a7f74]">[−] IDOR: No issues detected</p>
                  <p className="text-[#8a7f74]">[−] SSRF: No issues detected</p>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: 2 }}
                  className="text-[#f59e0b]"
                >
                  [+] Scan completed in 2m 34s
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: 2.4 }}
                  className="text-[#e8e0d5]"
                >
                  Report saved:{" "}
                  <span className="text-[#f59e0b]">./reports/scan-2024-03-18.pdf</span>
                </motion.div>
              </div>
            </div>

            {/* Glow effect */}
            <div className="absolute -inset-4 bg-[#f59e0b]/5 blur-3xl -z-10" />
          </motion.div>
        </div>
      </div>
    </section>
  );
}

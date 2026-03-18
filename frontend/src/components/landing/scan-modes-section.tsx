"use client";

import { motion } from "framer-motion";
import { Check, X } from "lucide-react";
import { MagneticWrapper } from "./magnetic-wrapper";

const plans = [
  {
    name: "Quick Scan",
    desc: "Fast security check for common vulnerabilities",
    price: "~2 min",
    features: [
      { text: "Max 20 pages", included: true },
      { text: "Depth level 2", included: true },
      { text: "Passive modules", included: true },
      { text: "Basic report", included: true },
      { text: "Active testing", included: false },
      { text: "PDF export", included: false },
    ],
    cta: "/scans/new?mode=quick",
    popular: false,
  },
  {
    name: "Full Scan",
    desc: "Comprehensive vulnerability assessment",
    price: "~15 min",
    features: [
      { text: "Max 100 pages", included: true },
      { text: "Depth level 5", included: true },
      { text: "Passive modules", included: true },
      { text: "Basic report", included: true },
      { text: "Active testing", included: true },
      { text: "PDF export", included: true },
    ],
    cta: "/scans/new?mode=full",
    popular: true,
  },
];

export function ScanModesSection() {
  return (
    <section className="py-32 px-6 relative">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <p className="text-sm text-[#f59e0b] font-mono tracking-widest uppercase mb-4">
            Scan Modes
          </p>
          <h2 className="text-4xl md:text-5xl font-bold text-[#e8e0d5] mb-6">
            Choose Your Scan Type
          </h2>
          <p className="text-xl text-[#8a7f74] max-w-2xl mx-auto">
            Quick scans for fast feedback, full scans for thorough assessment
          </p>
        </motion.div>

        {/* Pricing cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {plans.map((plan, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
              className={`relative p-8 rounded-xl border ${
                plan.popular
                  ? "border-[#f59e0b]/50 bg-[#141210]"
                  : "border-[#2c2820] bg-[#141210]/50"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-[#f59e0b] text-[#0c0a08] text-sm font-semibold">
                  Recommended
                </div>
              )}

              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-[#e8e0d5] mb-2">{plan.name}</h3>
                <p className="text-[#8a7f74] mb-4">{plan.desc}</p>
                <p className="text-3xl font-bold text-[#f59e0b]">{plan.price}</p>
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, j) => (
                  <li key={j} className="flex items-center gap-3">
                    {feature.included ? (
                      <Check className="w-5 h-5 text-[#4ade80] flex-shrink-0" />
                    ) : (
                      <X className="w-5 h-5 text-[#4a4440] flex-shrink-0" />
                    )}
                    <span className={feature.included ? "text-[#e8e0d5]" : "text-[#4a4440]"}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              <MagneticWrapper>
                <a
                  href={plan.cta}
                  className={`block w-full py-4 px-8 rounded-lg text-center font-semibold transition-all ${
                    plan.popular
                      ? "bg-[#f59e0b] text-[#0c0a08] hover:bg-[#d97706]"
                      : "border border-[#2c2820] text-[#e8e0d5] hover:bg-[#1c1916]"
                  }`}
                >
                  Start {plan.name}
                </a>
              </MagneticWrapper>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

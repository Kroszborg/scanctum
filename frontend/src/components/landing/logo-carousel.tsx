"use client";

import { motion } from "framer-motion";

const logos = [
  { name: "OWASP", color: "#8a7f74" },
  { name: "CVE", color: "#8a7f74" },
  { name: "CVSS v3.1", color: "#8a7f74" },
  { name: "SANS 25", color: "#8a7f74" },
  { name: "NIST", color: "#8a7f74" },
];

export function LogoCarousel() {
  return (
    <section className="py-16 border-y border-[#1c1916] bg-[#0a0908]/30">
      <div className="max-w-7xl mx-auto px-6">
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center text-sm text-[#4a4440] font-mono uppercase tracking-widest mb-8"
        >
          Aligned with industry standards
        </motion.p>

        <div className="flex flex-wrap items-center justify-center gap-12 md:gap-20">
          {logos.map((logo, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="text-2xl md:text-3xl font-bold"
              style={{ color: logo.color }}
            >
              {logo.name}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

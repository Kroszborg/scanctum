"use client";

import { motion } from "framer-motion";
import { Shield, Github, Mail, ExternalLink } from "lucide-react";
import { MagneticWrapper } from "./magnetic-wrapper";

export function FooterSection() {
  return (
    <footer className="border-t border-[#1c1916] bg-[#0a0908] px-6 py-16">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-8 h-8 text-[#f59e0b]" />
              <span className="text-xl font-bold text-[#e8e0d5]">SCANCTUM</span>
            </div>
            <p className="text-[#8a7f74] text-sm leading-relaxed">
              Modular web application security scanner for modern applications.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-sm font-semibold text-[#e8e0d5] uppercase tracking-wider mb-4">
              Product
            </h4>
            <ul className="space-y-3">
              {["Features", "Scan Modes", "Pricing", "API"].map((item) => (
                <li key={item}>
                  <a
                    href="#"
                    className="text-[#8a7f74] hover:text-[#f59e0b] transition-colors text-sm"
                  >
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-sm font-semibold text-[#e8e0d5] uppercase tracking-wider mb-4">
              Resources
            </h4>
            <ul className="space-y-3">
              {["Documentation", "API Reference", "Blog", "Changelog"].map((item) => (
                <li key={item}>
                  <a
                    href="#"
                    className="text-[#8a7f74] hover:text-[#f59e0b] transition-colors text-sm"
                  >
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-sm font-semibold text-[#e8e0d5] uppercase tracking-wider mb-4">
              Legal
            </h4>
            <ul className="space-y-3">
              {["Privacy Policy", "Terms of Service", "Security", "Contact"].map(
                (item) => (
                  <li key={item}>
                    <a
                      href="#"
                      className="text-[#8a7f74] hover:text-[#f59e0b] transition-colors text-sm"
                    >
                      {item}
                    </a>
                  </li>
                )
              )}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-[#1c1916] flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-[#4a4440]">
            © 2024 Scanctum. Built for B.Tech IT PBL Evaluation.
          </p>

          <div className="flex items-center gap-6">
            <MagneticWrapper>
              <a
                href="https://github.com/Kroszborg/scanctum"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#4a4440] hover:text-[#f59e0b] transition-colors"
              >
                <Github className="w-5 h-5" />
              </a>
            </MagneticWrapper>
            <MagneticWrapper>
              <a
                href="mailto:admin@kroszborg.co"
                className="text-[#4a4440] hover:text-[#f59e0b] transition-colors"
              >
                <Mail className="w-5 h-5" />
              </a>
            </MagneticWrapper>
            <MagneticWrapper>
              <a
                href="https://scanctum.kroszborg.co"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#4a4440] hover:text-[#f59e0b] transition-colors flex items-center gap-1"
              >
                <span className="text-sm">Live Demo</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </MagneticWrapper>
          </div>
        </div>
      </div>
    </footer>
  );
}

"use client";

import { motion } from "framer-motion";
import { Github, Mail, ExternalLink } from "lucide-react";
import { MagneticWrapper } from "./magnetic-wrapper";

export function FooterSection() {
  return (
    <footer className="border-t border-[#1c1916] bg-[#0a0908] px-6 py-12">
      <div className="max-w-7xl mx-auto">
        {/* Main footer content */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
          {/* Brand */}
          <div>
            <p className="text-[10px] tracking-[0.2em] uppercase text-[#f59e0b] font-mono mb-1">
              SCANCTUM
            </p>
            <p className="text-sm text-[#8a7f74]">
              Web Application Security Scanner
            </p>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8">
            <a href="#" className="text-sm text-[#8a7f74] hover:text-[#f59e0b] transition-colors">
              Documentation
            </a>
            <a href="#" className="text-sm text-[#8a7f74] hover:text-[#f59e0b] transition-colors">
              API
            </a>
            <a href="#" className="text-sm text-[#8a7f74] hover:text-[#f59e0b] transition-colors">
              Privacy
            </a>
            <a href="#" className="text-sm text-[#8a7f74] hover:text-[#f59e0b] transition-colors">
              Terms
            </a>
          </div>

          {/* Social */}
          <div className="flex items-center gap-4">
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
                <span className="text-sm">Demo</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </MagneticWrapper>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-6 border-t border-[#1c1916] flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-[#4a4440]">
            © 2024 Scanctum. Built for B.Tech IT PBL Evaluation.
          </p>
          <p className="text-xs text-[#4a4440] font-mono">
            v0.2.0
          </p>
        </div>
      </div>
    </footer>
  );
}

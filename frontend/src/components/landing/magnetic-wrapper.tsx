"use client";

import { ReactNode, useRef, useState } from "react";
import { motion, useSpring, useTransform, useMotionValue } from "framer-motion";

interface MagneticWrapperProps {
  children: ReactNode;
  intensity?: number;
  range?: number;
}

export function MagneticWrapper({
  children,
  intensity = 0.6,
  range = 100
}: MagneticWrapperProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const springConfig = { damping: 30, stiffness: 200, mass: 0.8 };
  const xSpring = useSpring(x, springConfig);
  const ySpring = useSpring(y, springConfig);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;

    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const distanceX = e.clientX - centerX;
    const distanceY = e.clientY - centerY;

    const isInRange = Math.abs(distanceX) < range && Math.abs(distanceY) < range;

    if (isInRange) {
      const factor = Math.max(
        0,
        1 - Math.max(Math.abs(distanceX) / range, Math.abs(distanceY) / range)
      );
      x.set(distanceX * intensity * factor);
      y.set(distanceY * intensity * factor);
    } else {
      x.set(0);
      y.set(0);
    }
  };

  const handleMouseEnter = () => setIsHovered(true);
  const handleMouseLeave = () => {
    setIsHovered(false);
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{
        x: xSpring,
        y: ySpring,
      }}
      className="inline-block"
    >
      {children}
    </motion.div>
  );
}

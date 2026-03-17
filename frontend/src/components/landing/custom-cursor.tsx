"use client";

import { useEffect, useState } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";

export function CustomCursor() {
  const [isHovering, setIsHovering] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });

  const cursorX = useMotionValue(0);
  const cursorY = useMotionValue(0);

  const springConfig = { damping: 25, stiffness: 700, mass: 0.5 };
  const cursorSpringX = useSpring(cursorX, springConfig);
  const cursorSpringY = useSpring(cursorY, springConfig);

  const scale = useTransform(
    cursorSpringY,
    () => isHovering ? 2 : 1
  );

  const opacity = useTransform(
    cursorSpringY,
    () => isVisible ? 1 : 0
  );

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - lastMousePos.x;
      const deltaY = e.clientY - lastMousePos.y;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

      if (distance > 2) {
        setIsVisible(true);
      }

      setLastMousePos({ x: e.clientX, y: e.clientY });
      cursorX.set(e.clientX - 8);
      cursorY.set(e.clientY - 8);
    };

    const onMouseEnter = () => setIsVisible(true);
    const onMouseLeave = () => setIsVisible(false);

    const onMouseDown = () => setIsHovering(true);
    const onMouseUp = () => setIsHovering(false);

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseenter", onMouseEnter);
    document.addEventListener("mouseleave", onMouseLeave);
    document.addEventListener("mousedown", onMouseDown);
    document.addEventListener("mouseup", onMouseUp);

    const clickableElements = document.querySelectorAll("a, button, input, [role='button']");
    clickableElements.forEach((el) => {
      el.addEventListener("mouseenter", () => setIsHovering(true));
      el.addEventListener("mouseleave", () => setIsHovering(false));
    });

    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseenter", onMouseEnter);
      document.removeEventListener("mouseleave", onMouseLeave);
      document.removeEventListener("mousedown", onMouseDown);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [cursorX, cursorY, isHovering, lastMousePos]);

  return (
    <motion.div
      className="fixed top-0 left-0 w-4 h-4 pointer-events-none z-[9999] mix-blend-difference"
      style={{
        x: cursorSpringX,
        y: cursorSpringY,
        scale,
        opacity,
      }}
    >
      <div className="w-full h-full rounded-full border-2 border-[#f59e0b] bg-[#f59e0b]" />
    </motion.div>
  );
}

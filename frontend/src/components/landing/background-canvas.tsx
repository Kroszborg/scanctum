"use client";

import { Canvas } from "@react-three/fiber";
import { ShaderBackground } from "./shader-background";

export function BackgroundCanvas() {
  return (
    <div className="fixed inset-0 -z-10">
      <Canvas
        camera={{ position: [0, 0, 1] }}
        gl={{ antialias: false, alpha: true }}
      >
        <ShaderBackground />
      </Canvas>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0c0a08]/20 to-[#0c0a08]" />
    </div>
  );
}

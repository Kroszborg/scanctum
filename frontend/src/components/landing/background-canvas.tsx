"use client";

import { Canvas } from "@react-three/fiber";
import { ShaderBackground } from "./shader-background";

export function BackgroundCanvas() {
  return (
    <div className="fixed inset-0 -z-10 w-screen h-screen" style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0 }}>
      <Canvas
        camera={{ position: [0, 0, 1.5] }}
        gl={{ antialias: false, alpha: true, preserveDrawingBuffer: true }}
        style={{ width: "100vw", height: "100vh" }}
      >
        <ShaderBackground />
      </Canvas>
    </div>
  );
}

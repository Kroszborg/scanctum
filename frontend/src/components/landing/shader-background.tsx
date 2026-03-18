"use client";

import { useRef, useEffect } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

const vertexShader = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const fragmentShader = `
uniform float uTime;
uniform vec3 uColor1;
uniform vec2 uResolution;
varying vec2 vUv;

// Simplex noise
vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
           -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy) );
  vec2 x0 = v -   i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
  + i.x + vec3(0.0, i1.x, 1.0 ));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
  m = m*m ;
  m = m*m ;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
  vec2 uv = vUv;

  // Aspect ratio correction for fullscreen
  float aspect = uResolution.x / uResolution.y;
  vec2 correctedUV = vec2(uv.x * aspect, uv.y);

  // Multiple noise layers for more visible movement
  float noise1 = snoise(correctedUV * 1.5 + uTime * 0.08);
  float noise2 = snoise(correctedUV * 3.0 - uTime * 0.12);
  float noise3 = snoise(correctedUV * 0.8 + uTime * 0.05);

  // Animated color bands
  float band = sin(uv.y * 6.0 + uTime * 0.1) * 0.1 + 0.5;

  // Base gradient
  vec3 baseColor = mix(uColor1, vec3(0.15, 0.12, 0.1), uv.y);

  // Add noise layers with more intensity
  vec3 color = baseColor;
  color.rgb += vec3(0.08, 0.05, 0.03) * noise1;
  color.rgb += vec3(0.05, 0.03, 0.02) * noise2;
  color.rgb += vec3(0.03) * noise3;
  color.rgb += 0.05 * band;

  // Subtle purple/violet hints in the noise
  color = mix(color, vec3(0.3, 0.15, 0.4), noise1 * 0.15);

  // Vignette for depth
  float dist = distance(uv, vec2(0.5));
  color *= 1.0 - dist * 0.5;

  gl_FragColor = vec4(color, 1.0);
}
`;

export function ShaderBackground() {
  const meshRef = useRef<THREE.Mesh>(null);

  useEffect(() => {
    if (meshRef.current) {
      meshRef.current.rotation.z = -Math.PI / 2;
    }
  }, []);

  useFrame((state) => {
    if (meshRef.current?.material) {
      const material = meshRef.current.material as THREE.ShaderMaterial;
      material.uniforms.uTime.value = state.clock.elapsedTime;
      material.uniforms.uResolution.value.set(
        state.size.width,
        state.size.height
      );
    }
    // Keep plane sized to fill the viewport.
    // The -PI/2 rotation around Z swaps local X/Y axes,
    // so we pass height as X and width as Y to compensate.
    if (meshRef.current) {
      meshRef.current.scale.set(state.viewport.height, state.viewport.width, 1);
    }
  });

  return (
    <mesh ref={meshRef}>
      <planeGeometry args={[1, 1, 64, 64]} />
      <shaderMaterial
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={{
          uTime: { value: 0 },
          uColor1: { value: new THREE.Color("#0a0a0a") },
          uResolution: { value: new THREE.Vector2(1920, 1080) },
        }}
        depthWrite={false}
        depthTest={false}
      />
    </mesh>
  );
}

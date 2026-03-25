"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { RGBShiftShader } from "three/examples/jsm/shaders/RGBShiftShader.js";

export function AiHeroBackground() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || typeof window === "undefined") {
      return;
    }

    let frameId = 0;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#050811");

    const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
    camera.position.set(0, 0, 15);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.setClearColor("#050811", 1);
    container.appendChild(renderer.domElement);

    const pointCountX = 42;
    const pointCountY = 20;
    const totalPoints = pointCountX * pointCountY;
    const positions = new Float32Array(totalPoints * 3);
    const offsets = new Float32Array(totalPoints);

    let index = 0;
    for (let y = 0; y < pointCountY; y += 1) {
      for (let x = 0; x < pointCountX; x += 1) {
        const xPos = (x - pointCountX / 2) * 0.55;
        const yPos = (y - pointCountY / 2) * 0.55;
        positions[index * 3] = xPos;
        positions[index * 3 + 1] = yPos;
        positions[index * 3 + 2] = Math.sin(x * 0.35) * 0.25;
        offsets[index] = Math.random() * Math.PI * 2;
        index += 1;
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      color: new THREE.Color("#85a7ff"),
      size: 0.075,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const points = new THREE.Points(geometry, material);
    points.rotation.x = -0.4;
    scene.add(points);

    const ambient = new THREE.AmbientLight("#92a7ff", 0.7);
    scene.add(ambient);

    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));

    const bloomPass = new UnrealBloomPass(new THREE.Vector2(1, 1), 0.4, 0.9, 0.6);
    composer.addPass(bloomPass);

    const rgbShiftPass = new ShaderPass(RGBShiftShader);
    rgbShiftPass.uniforms["amount"].value = 0.00025;
    composer.addPass(rgbShiftPass);

    const handleResize = () => {
      const { clientWidth, clientHeight } = container;
      if (!clientWidth || !clientHeight) {
        return;
      }

      camera.aspect = clientWidth / clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(clientWidth, clientHeight, false);
      composer.setSize(clientWidth, clientHeight);
    };

    const clock = new THREE.Clock();
    const basePositions = positions.slice();

    const animate = () => {
      const elapsed = clock.getElapsedTime();
      const attribute = geometry.getAttribute("position") as THREE.BufferAttribute;

      for (let i = 0; i < totalPoints; i += 1) {
        const baseZ = basePositions[i * 3 + 2];
        attribute.array[i * 3 + 2] =
          baseZ +
          Math.sin(elapsed * 1.8 + offsets[i]) * 0.22 +
          Math.cos(elapsed * 0.8 + i * 0.12) * 0.05;
      }

      attribute.needsUpdate = true;
      points.rotation.z = elapsed * 0.025;
      points.position.y = Math.sin(elapsed * 0.4) * 0.15;
      composer.render();
      frameId = window.requestAnimationFrame(animate);
    };

    handleResize();
    animate();
    window.addEventListener("resize", handleResize);

    return () => {
      window.cancelAnimationFrame(frameId);
      window.removeEventListener("resize", handleResize);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return <div ref={containerRef} className="pointer-events-none absolute inset-0 z-0 opacity-55" aria-hidden="true" />;
}

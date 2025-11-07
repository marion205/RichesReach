/**
 * Orb Renderer for Web/PWA
 * Three.js-based Constellation Orb for web browsers
 * Progressive Web App compatible
 */

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface OrbRendererProps {
  netWorth: number;
  portfolioValue: number;
  bankBalance: number;
  onGesture?: (gesture: string) => void;
  width?: number;
  height?: number;
}

export const OrbRenderer: React.FC<OrbRendererProps> = ({
  netWorth,
  portfolioValue,
  bankBalance,
  onGesture,
  width = 400,
  height = 400,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const orbRef = useRef<THREE.Mesh | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (!mountRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8f9fa);
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(
      75,
      width / height,
      0.1,
      1000
    );
    camera.position.z = 5;
    cameraRef.current = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Calculate orb size based on net worth
    const orbSize = Math.max(0.5, Math.min(2.0, netWorth / 100000));
    const orbRadius = 1.0 * orbSize;

    // Create orb geometry
    const geometry = new THREE.SphereGeometry(orbRadius, 32, 32);
    
    // Create gradient material
    const material = new THREE.MeshPhongMaterial({
      color: 0x007aff,
      emissive: 0x001133,
      shininess: 100,
      transparent: true,
      opacity: 0.9,
    });

    const orb = new THREE.Mesh(geometry, material);
    orb.position.set(0, 0, 0);
    scene.add(orb);
    orbRef.current = orb;

    // Add glow effect
    const glowGeometry = new THREE.SphereGeometry(orbRadius * 1.1, 32, 32);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: 0x007aff,
      transparent: true,
      opacity: 0.3,
    });
    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    scene.add(glow);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x007aff, 1, 100);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    // Add satellites (representing positions)
    const satellites: THREE.Mesh[] = [];
    const numSatellites = Math.min(5, Math.floor(portfolioValue / 10000));
    
    for (let i = 0; i < numSatellites; i++) {
      const angle = (i / numSatellites) * Math.PI * 2;
      const satelliteGeometry = new THREE.SphereGeometry(0.1, 16, 16);
      const satelliteMaterial = new THREE.MeshPhongMaterial({
        color: 0x34c759,
        emissive: 0x003311,
      });
      const satellite = new THREE.Mesh(satelliteGeometry, satelliteMaterial);
      satellite.position.set(
        Math.cos(angle) * (orbRadius + 0.5),
        Math.sin(angle) * (orbRadius + 0.5),
        0
      );
      scene.add(satellite);
      satellites.push(satellite);
    }

    // Animation
    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);

      // Rotate orb
      if (orb) {
        orb.rotation.y += 0.01;
        orb.rotation.x += 0.005;
      }

      // Rotate satellites
      satellites.forEach((sat, index) => {
        const angle = (Date.now() / 1000 + index) * 0.5;
        const radius = orbRadius + 0.5;
        sat.position.x = Math.cos(angle) * radius;
        sat.position.y = Math.sin(angle) * radius;
        sat.rotation.y += 0.02;
      });

      // Pulse glow
      const pulse = Math.sin(Date.now() / 1000) * 0.1 + 1.0;
      glow.scale.set(pulse, pulse, pulse);

      renderer.render(scene, camera);
    };

    animate();
    setIsLoaded(true);

    // Gesture handlers
    let touchStartX = 0;
    let touchStartY = 0;
    let lastTap = 0;

    const handleTouchStart = (e: TouchEvent) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    };

    const handleTouchEnd = (e: TouchEvent) => {
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      const deltaX = touchEndX - touchStartX;
      const deltaY = touchEndY - touchStartY;

      // Detect gestures
      const now = Date.now();
      const timeSinceLastTap = now - lastTap;

      if (Math.abs(deltaX) < 10 && Math.abs(deltaY) < 10) {
        // Tap
        if (timeSinceLastTap < 300) {
          // Double tap
          onGesture?.('double_tap');
        } else {
          onGesture?.('tap');
        }
        lastTap = now;
      } else if (Math.abs(deltaX) > Math.abs(deltaY)) {
        // Swipe horizontal
        if (deltaX < -50) {
          onGesture?.('swipe_left');
        } else if (deltaX > 50) {
          onGesture?.('swipe_right');
        }
      }

      // Long press (simulated with touch duration)
      // Would need timer for actual long press
    };

    const handleMouseClick = () => {
      onGesture?.('tap');
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (e.deltaY < 0) {
        onGesture?.('pinch');
      }
    };

    const canvas = renderer.domElement;
    canvas.addEventListener('touchstart', handleTouchStart);
    canvas.addEventListener('touchend', handleTouchEnd);
    canvas.addEventListener('click', handleMouseClick);
    canvas.addEventListener('wheel', handleWheel, { passive: false });

    // Cleanup
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      canvas.removeEventListener('touchstart', handleTouchStart);
      canvas.removeEventListener('touchend', handleTouchEnd);
      canvas.removeEventListener('click', handleMouseClick);
      canvas.removeEventListener('wheel', handleWheel);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [netWorth, portfolioValue, bankBalance, width, height, onGesture]);

  return (
    <div
      ref={mountRef}
      style={{
        width: `${width}px`,
        height: `${height}px`,
        position: 'relative',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {!isLoaded && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            color: '#8E8E93',
            fontSize: '14px',
          }}
        >
          Loading orb...
        </div>
      )}
    </div>
  );
};

export default OrbRenderer;


import React, { useMemo, useRef } from 'react';
import { Stars, OrbitControls, Html, PerspectiveCamera } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import * as THREE from 'three';
import Planet from './Planet';

/**
 * SpaceScene — Phase 3.5 (Camera + Scale + Lighting Fix)
 * PerspectiveCamera with proper near/far to prevent clipping.
 * Sun at origin with emissive material + pointLight inside.
 * Solar System with normalized scale, exoplanets outward.
 */
export default function SpaceScene({ planets, selectedPlanet, onSelectPlanet }) {
    const starsRef = useRef();
    const sunRef = useRef();

    useFrame((state, delta) => {
        if (starsRef.current) {
            starsRef.current.rotation.y += delta * 0.005;
            starsRef.current.rotation.x += delta * 0.002;
        }
        // Sun gentle pulse
        if (sunRef.current) {
            const s = 1.0 + Math.sin(state.clock.elapsedTime * 0.5) * 0.02;
            sunRef.current.scale.setScalar(s);
        }
    });

    // ── Position planets: Solar System nearby, exoplanets far out ──
    const positions = useMemo(() => {
        const solarCount = planets.filter(p => p.is_solar).length;

        // Normalized Solar System positions (Sun radius=5, Earth at 30)
        const solarPositions = {
            Mercury: [12, 0, 3],
            Venus: [20, 1, -8],
            Earth: [30, 0, 5],
            Mars: [40, -1, -3],
            Jupiter: [60, 2, 10],
            Saturn: [80, -1, -8],
            Uranus: [100, 2, 5],
            Neptune: [120, -2, -10],
        };

        return planets.map((planet, i) => {
            if (planet.is_solar && solarPositions[planet.pl_name]) {
                return solarPositions[planet.pl_name];
            }
            // Exoplanets: golden-ratio spiral in deep space
            const exoIndex = i - solarCount;
            const angle = exoIndex * 0.618033 * Math.PI * 2;
            const armRadius = 160 + exoIndex * 12;
            const x = Math.cos(angle) * armRadius;
            const z = Math.sin(angle) * armRadius;
            const y = Math.sin(exoIndex * 1.7) * 30;
            return [x, y, z];
        });
    }, [planets]);

    return (
        <>
            {/* ── Camera — far clip at 50000 prevents clipping ── */}
            <PerspectiveCamera makeDefault position={[0, 20, 100]} near={0.01} far={50000} fov={55} />

            {/* Deep void */}
            <color attach="background" args={['#010008']} />

            {/* ── Starfield ── */}
            <group ref={starsRef}>
                <Stars radius={500} depth={300} count={5000} factor={8} saturation={0.3} fade speed={0.2} />
                <Stars radius={800} depth={400} count={3000} factor={4} saturation={0.1} fade speed={0.08} />
            </group>

            {/* ── Lighting (bright enough to show textures) ── */}
            <ambientLight intensity={0.6} color="#b8c0ff" />
            <hemisphereLight skyColor="#e0e8ff" groundColor="#1a1028" intensity={0.4} />
            {/* Sun's point light — bright, far-reaching */}
            <pointLight position={[0, 0, 0]} intensity={5} color="#fff4e0" distance={1500} decay={1} />
            {/* Rim fill lights for cinematic depth */}
            <pointLight position={[-100, 40, -80]} intensity={1} color="#6366f1" distance={500} />
            <pointLight position={[80, -30, 60]} intensity={0.6} color="#a855f7" distance={400} />

            {/* ── Sun (radius 5, emissive for Bloom interaction) ── */}
            <group ref={sunRef}>
                <mesh position={[0, 0, 0]}>
                    <sphereGeometry args={[5, 64, 64]} />
                    <meshStandardMaterial
                        color="#ffd54f"
                        emissive="#ff8f00"
                        emissiveIntensity={3}
                        toneMapped={false}
                    />
                </mesh>
                {/* Outer glow shell */}
                <mesh position={[0, 0, 0]}>
                    <sphereGeometry args={[7, 32, 32]} />
                    <meshBasicMaterial
                        color="#ffb74d"
                        transparent
                        opacity={0.08}
                        side={THREE.BackSide}
                        depthWrite={false}
                        blending={THREE.AdditiveBlending}
                    />
                </mesh>
            </group>

            {/* ── "SOL SYSTEM" label ── */}
            <Html position={[0, 9, 0]} center distanceFactor={20} sprite>
                <div style={{
                    fontFamily: 'Orbitron, monospace',
                    fontSize: '11px',
                    letterSpacing: '0.3em',
                    color: 'rgba(255,255,255,0.45)',
                    textShadow: '0 0 12px rgba(99,102,241,0.4)',
                    whiteSpace: 'nowrap',
                    pointerEvents: 'none',
                    userSelect: 'none',
                }}>
                    SOL SYSTEM
                </div>
            </Html>

            {/* ── Camera Controls ── */}
            <OrbitControls
                enablePan
                enableZoom
                enableRotate
                autoRotate
                autoRotateSpeed={0.05}
                maxDistance={2000}
                minDistance={5}
                enableDamping
                dampingFactor={0.05}
            />

            {/* ── Planets ── */}
            {planets.map((planet, i) => (
                <Planet
                    key={planet.pl_name || i}
                    data={planet}
                    position={positions[i]}
                    selected={selectedPlanet?.pl_name === planet.pl_name}
                    onClick={onSelectPlanet}
                />
            ))}

            {/* ── Cinematic Bloom ── */}
            <EffectComposer>
                <Bloom
                    intensity={1.2}
                    luminanceThreshold={0.2}
                    luminanceSmoothing={0.9}
                    radius={0.8}
                />
            </EffectComposer>
        </>
    );
}

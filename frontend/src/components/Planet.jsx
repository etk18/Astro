import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getPlanetMap, getCloudTexture } from '../utils/planetTextures';

/**
 * Planet — Procedural Textures (No External URLs)
 * Solar System planets use Canvas2D generated textures.
 * Exoplanets use temperature-driven meshStandardMaterial.
 */

// ── Planet radii (scaled for visibility, Sun=5) ──
const PLANET_RADIUS = {
    Mercury: 1.2, Venus: 2.0, Earth: 2.2, Mars: 1.5,
    Jupiter: 5.5, Saturn: 4.8, Uranus: 3.0, Neptune: 2.8,
};

// Temperature → color for exoplanets
function tempToMaterial(temp) {
    const t = Math.min(temp / 3000, 1);
    if (t < 0.15) return { color: '#6ba3d6', emissive: '#0a1828', roughness: 0.5 };
    if (t < 0.25) return { color: '#4a8aa0', emissive: '#0a1520', roughness: 0.6 };
    if (t < 0.4) return { color: '#3a7a55', emissive: '#0a1a10', roughness: 0.7 };
    if (t < 0.55) return { color: '#b08840', emissive: '#1a1208', roughness: 0.65 };
    if (t < 0.75) return { color: '#d05830', emissive: '#1a0a05', roughness: 0.55 };
    return { color: '#e83010', emissive: '#2a0805', roughness: 0.45 };
}

// ── Solar System Planet (Procedural Textured) ──
function SolarPlanet({ data, position, onClick, selected }) {
    const meshRef = useRef();
    const glowRef = useRef();
    const cloudRef = useRef();
    const selRingRef = useRef();

    const name = data.pl_name;
    const radius = PLANET_RADIUS[name] || 2.0;
    const isEarth = name === 'Earth';
    const isSaturn = name === 'Saturn';

    // Generate procedural PBR textures (cached)
    const pbr = useMemo(() => getPlanetMap(name), [name]);
    const cloudTex = useMemo(() => isEarth ? getCloudTexture() : null, [isEarth]);

    useFrame((state) => {
        const t = state.clock.elapsedTime;
        if (meshRef.current) meshRef.current.rotation.y += 0.002;
        if (cloudRef.current) cloudRef.current.rotation.y += 0.0035;
        if (glowRef.current) {
            const s = selected ? 1.0 + Math.sin(t * 3) * 0.05 : 1.0;
            glowRef.current.scale.setScalar(s);
        }
        if (selRingRef.current) selRingRef.current.rotation.z = t * 0.4;
    });

    const atmosphereColor = useMemo(() => {
        const colors = {
            Mercury: '#888888', Venus: '#e8c44a', Earth: '#4488ff',
            Mars: '#cc6633', Jupiter: '#d4a060', Saturn: '#dbc48e',
            Uranus: '#66ccdd', Neptune: '#3355bb',
        };
        return colors[name] || '#ffffff';
    }, [name]);

    return (
        <group position={position}>
            {/* Planet body */}
            <mesh
                ref={meshRef}
                onClick={(e) => { e.stopPropagation(); onClick(data); }}
                onPointerOver={(e) => { e.stopPropagation(); document.body.style.cursor = 'pointer'; }}
                onPointerOut={() => { document.body.style.cursor = 'default'; }}
            >
                <sphereGeometry args={[radius, 64, 64]} />
                <meshStandardMaterial
                    map={pbr?.map}
                    bumpMap={pbr?.bumpMap}
                    bumpScale={0.02}
                    roughnessMap={pbr?.roughnessMap}
                    roughness={isEarth ? 1 : 0.7} // Base roughness, overridden by map
                    metalness={0.05}
                    emissive={selected ? '#222244' : '#000000'}
                    emissiveIntensity={selected ? 0.8 : 0}
                />
            </mesh>

            {/* Earth cloud layer */}
            {isEarth && cloudTex && (
                <mesh ref={cloudRef}>
                    <sphereGeometry args={[radius * 1.012, 48, 48]} />
                    <meshStandardMaterial
                        map={cloudTex}
                        transparent
                        opacity={0.35}
                        depthWrite={false}
                        roughness={1}
                    />
                </mesh>
            )}

            {/* Atmospheric glow */}
            <mesh ref={glowRef}>
                <sphereGeometry args={[radius * 1.15, 32, 32]} />
                <meshBasicMaterial
                    color={atmosphereColor}
                    transparent
                    opacity={selected ? 0.18 : 0.05}
                    side={THREE.BackSide}
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </mesh>

            {/* Saturn's rings */}
            {isSaturn && (
                <mesh rotation={[Math.PI * 0.4, 0.15, 0]}>
                    <ringGeometry args={[radius * 1.3, radius * 2.1, 64]} />
                    <meshStandardMaterial
                        color="#c4a76c"
                        transparent opacity={0.5}
                        side={THREE.DoubleSide}
                        roughness={0.9}
                        depthWrite={false}
                    />
                </mesh>
            )}

            {/* Selection ring */}
            {selected && (
                <mesh ref={selRingRef} rotation={[Math.PI / 2, 0, 0]}>
                    <ringGeometry args={[radius * 1.5, radius * 1.6, 64]} />
                    <meshBasicMaterial
                        color="#6366f1"
                        transparent opacity={0.5}
                        side={THREE.DoubleSide}
                        depthWrite={false}
                        blending={THREE.AdditiveBlending}
                    />
                </mesh>
            )}
        </group>
    );
}

// ── Exoplanet (Procedural Color) ──
function ExoPlanet({ data, position, onClick, selected }) {
    const meshRef = useRef();
    const glowRef = useRef();
    const selRingRef = useRef();

    const temperature = data.pl_eqt || 800;
    const radius = Math.max(1.0, Math.min((data.pl_radj || 1) * 2.0, 6.0));
    const mat = tempToMaterial(temperature);

    const glowColor = useMemo(() => {
        const t = Math.min(temperature / 3000, 1);
        return new THREE.Color().setHSL(0.6 - t * 0.55, 0.8, 0.4 + t * 0.2);
    }, [temperature]);

    useFrame((state) => {
        if (meshRef.current) meshRef.current.rotation.y += 0.0015;
        if (glowRef.current) {
            const s = selected ? 1.0 + Math.sin(state.clock.elapsedTime * 3) * 0.05 : 1.0;
            glowRef.current.scale.setScalar(s);
        }
        if (selRingRef.current) selRingRef.current.rotation.z = state.clock.elapsedTime * 0.4;
    });

    return (
        <group position={position}>
            <mesh
                ref={meshRef}
                onClick={(e) => { e.stopPropagation(); onClick(data); }}
                onPointerOver={(e) => { e.stopPropagation(); document.body.style.cursor = 'pointer'; }}
                onPointerOut={() => { document.body.style.cursor = 'default'; }}
            >
                <sphereGeometry args={[radius, 48, 48]} />
                <meshStandardMaterial
                    color={mat.color}
                    emissive={selected ? mat.emissive : '#000000'}
                    emissiveIntensity={selected ? 1.5 : 0.3}
                    roughness={mat.roughness}
                    metalness={0.08}
                />
            </mesh>

            <mesh ref={glowRef}>
                <sphereGeometry args={[radius * 1.15, 24, 24]} />
                <meshBasicMaterial
                    color={glowColor}
                    transparent opacity={selected ? 0.15 : 0.04}
                    side={THREE.BackSide}
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </mesh>

            {selected && (
                <mesh ref={selRingRef} rotation={[Math.PI / 2, 0, 0]}>
                    <ringGeometry args={[radius * 1.5, radius * 1.6, 64]} />
                    <meshBasicMaterial
                        color="#6366f1"
                        transparent opacity={0.5}
                        side={THREE.DoubleSide}
                        depthWrite={false}
                        blending={THREE.AdditiveBlending}
                    />
                </mesh>
            )}
        </group>
    );
}

// ── Route to correct component ──
export default function Planet({ data, position, onClick, selected }) {
    if (data.is_solar) {
        return <SolarPlanet data={data} position={position} onClick={onClick} selected={selected} />;
    }
    return <ExoPlanet data={data} position={position} onClick={onClick} selected={selected} />;
}

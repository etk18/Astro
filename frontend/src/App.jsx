import React, { useState, useEffect, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import SpaceScene from './components/SpaceScene';
import Dashboard from './components/Dashboard';

export default function App() {
    const [planets, setPlanets] = useState([]);
    const [selectedPlanet, setSelectedPlanet] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPlanets = async () => {
            try {
                const res = await axios.get('/api/exoplanets');
                setPlanets(res.data);
                setLoading(false);
            } catch (err) {
                console.error('Failed to fetch exoplanets:', err);
                setError('Failed to contact mission control. Is the backend running?');
                setLoading(false);
            }
        };
        fetchPlanets();
    }, []);

    const solarCount = planets.filter(p => p.is_solar).length;
    const exoCount = planets.length - solarCount;

    return (
        <div className="relative w-full h-full">
            {/* ── 3D Canvas ── */}
            <Canvas
                gl={{ antialias: true, alpha: false, toneMapping: 3, toneMappingExposure: 1.5 }}
                style={{ position: 'absolute', inset: 0 }}
            >
                <Suspense fallback={null}>
                    {planets.length > 0 && (
                        <SpaceScene
                            planets={planets}
                            selectedPlanet={selectedPlanet}
                            onSelectPlanet={setSelectedPlanet}
                        />
                    )}
                </Suspense>
            </Canvas>

            {/* ── HUD Overlay ── */}
            <div className="absolute inset-0 pointer-events-none z-10">
                {/* Title */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3, duration: 0.8 }}
                    className="absolute top-6 left-6"
                >
                    <h1 className="flex items-center gap-3 text-3xl font-black tracking-[0.18em] text-white"
                        style={{ fontFamily: 'var(--font-display)', textShadow: '0 0 30px rgba(99,102,241,0.3)' }}>
                        <svg className="w-8 h-8 text-blue-500 animate-[spin_60s_linear_infinite]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <circle cx="12" cy="12" r="10" />
                            <ellipse cx="12" cy="12" rx="10" ry="3" />
                            <ellipse cx="12" cy="12" rx="3" ry="10" />
                            <path d="M2 12h20" />
                        </svg>
                        EXOLENS
                    </h1>
                    <p className="text-[10px] text-white/30 tracking-[0.3em] mt-0.5"
                        style={{ fontFamily: 'var(--font-display)' }}>
                        3D EXOPLANET EXPLORER
                    </p>
                </motion.div>

                {/* Status Bar */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 }}
                    className="absolute bottom-5 left-5 flex items-center gap-3"
                >
                    <div className="px-4 py-2 rounded-xl bg-black/40 backdrop-blur-xl border border-white/[0.06] flex items-center gap-2.5 pointer-events-auto">
                        <div className="relative">
                            <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                            <div className="absolute inset-0 w-1.5 h-1.5 rounded-full bg-green-400 animate-ping opacity-40" />
                        </div>
                        <span className="text-[10px] tracking-[0.15em] text-white/60"
                            style={{ fontFamily: 'var(--font-display)' }}>
                            {loading ? 'SCANNING...' : `${solarCount} LOCAL · ${exoCount} EXOPLANETS`}
                        </span>
                    </div>
                    {!selectedPlanet && !loading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 1.5 }}
                            className="px-4 py-2 rounded-xl bg-black/30 backdrop-blur-xl border border-white/[0.04] pointer-events-auto"
                        >
                            <span className="text-[10px] tracking-wider text-white/30"
                                style={{ fontFamily: 'var(--font-display)' }}>
                                CLICK A PLANET TO ANALYZE
                            </span>
                        </motion.div>
                    )}
                </motion.div>

                {/* Error Toast */}
                <AnimatePresence>
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 20 }}
                            className="absolute bottom-5 right-5 px-4 py-2.5 rounded-xl bg-red-950/50 backdrop-blur-xl border border-red-500/20 pointer-events-auto"
                        >
                            <p className="text-xs text-red-300/80">{error}</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* ── Dashboard Panel ── */}
            <Dashboard
                planet={selectedPlanet}
                onClose={() => setSelectedPlanet(null)}
            />
        </div>
    );
}

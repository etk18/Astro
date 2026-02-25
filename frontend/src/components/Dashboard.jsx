import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatInterface from './ChatInterface';

/**
 * Dashboard — Chatbot-First Layout
 * Planet info is a slim top bar. Chat dominates the full panel.
 */
export default function Dashboard({ planet, onClose }) {
    if (!planet) return null;

    const isSolar = planet.is_solar === true;
    const temp = planet.pl_eqt ? `${Math.round(planet.pl_eqt)}K` : '';
    const host = planet.hostname || '';

    return (
        <AnimatePresence>
            <motion.div
                key="dashboard"
                initial={{ x: '100%', opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: '100%', opacity: 0 }}
                transition={{ type: 'spring', damping: 28, stiffness: 200 }}
                className="fixed inset-y-0 right-0 w-[480px] z-50 flex flex-col
          bg-black/60 backdrop-blur-2xl border-l border-white/10
          shadow-[0_0_50px_rgba(0,0,0,0.5)]"
            >
                {/* ═══ Slim Planet Bar ═══ */}
                <div className="shrink-0 flex items-center justify-between px-5 py-3
          border-b border-white/[0.06] bg-white/[0.02]">
                    <div className="flex items-center gap-3 min-w-0">
                        {isSolar && (
                            <span className="text-[8px] px-1.5 py-0.5 rounded bg-blue-500/20
                text-blue-300 border border-blue-500/20 font-bold tracking-widest shrink-0">
                                SOL
                            </span>
                        )}
                        <h2 className="text-lg font-bold text-white truncate"
                            style={{ fontFamily: 'Orbitron, monospace' }}>
                            {planet.pl_name}
                        </h2>
                        <span className="text-[11px] text-gray-500 shrink-0">
                            {[host, temp, planet.discoverymethod].filter(Boolean).join(' · ')}
                        </span>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-500 hover:text-white shrink-0"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                            <path d="M18 6L6 18M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* ═══ Chat Interface (fills remaining space) ═══ */}
                <ChatInterface planetName={planet.pl_name} />
            </motion.div>
        </AnimatePresence>
    );
}

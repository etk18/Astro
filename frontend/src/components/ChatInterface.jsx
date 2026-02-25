import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

// ── SVG Icons ──
function SendIcon() {
    return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
    );
}

// Orbit/Star logo for AI Avatar
function OrbitIcon() {
    return (
        <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-white/5 border border-white/10">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" strokeWidth="1.5">
                <circle cx="12" cy="12" r="3" />
                <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(45 12 12)" />
                <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(-45 12 12)" />
            </svg>
        </div>
    );
}

// ── RAG Loading ──
const RAG_STAGES = [
    { text: 'Querying Vector Database...', duration: 1500 },
    { text: 'Analyzing Knowledge Chunks...', duration: 2000 },
    { text: 'Composing Science Brief...', duration: 3000 },
];

function LoadingIndicator() {
    const [stage, setStage] = useState(0);
    useEffect(() => {
        if (stage < RAG_STAGES.length - 1) {
            const t = setTimeout(() => setStage(s => s + 1), RAG_STAGES[stage].duration);
            return () => clearTimeout(t);
        }
    }, [stage]);

    return (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex gap-3">
            <OrbitIcon />
            <div className="flex flex-col gap-1 pr-4">
                <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" style={{ animationDelay: '200ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" style={{ animationDelay: '400ms' }} />
                </div>
                <span className="text-xs text-indigo-300 font-medium tracking-wide">
                    {RAG_STAGES[stage].text}
                </span>
            </div>
        </motion.div>
    );
}

/**
 * Premium ChatInterface
 * Modern SaaS aesthetic, strict glassmorphism, right/left bubble alignment.
 */
export default function ChatInterface({ planetName }) {
    const [messages, setMessages] = useState([{
        role: 'assistant',
        content: `Greetings, Commander. I'm your Science Officer with access to the ExoLens knowledge base. Ask me anything about ${planetName}.`,
    }]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const endRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

    useEffect(() => {
        setMessages([{
            role: 'assistant',
            content: `Greetings, Commander. I'm your Science Officer with access to the ExoLens knowledge base. Ask me anything about ${planetName} — atmosphere, habitability, orbital dynamics, or stellar characteristics.`,
        }]);
    }, [planetName]);

    const send = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;
        const q = input.trim();
        setMessages(prev => [...prev, { role: 'user', content: q }]);
        setInput('');
        setLoading(true);
        try {
            const res = await axios.post('/api/chat', { planet_name: planetName, question: q });
            setMessages(prev => [...prev, { role: 'assistant', content: res.data.answer }]);
        } catch {
            setMessages(prev => [...prev, { role: 'assistant', content: '⚠ Connection lost. Please verify the backend is running.' }]);
        } finally {
            setLoading(false);
            inputRef.current?.focus();
        }
    };

    const quickPrompts = [
        `Is ${planetName} habitable?`,
        `Describe the atmosphere`,
        `How was ${planetName} discovered?`,
    ];

    const hasConversation = messages.length > 1;

    return (
        <div className="flex flex-col flex-1 min-h-0 w-full p-5">

            {/* ═══ Header ═══ */}
            <div className="shrink-0 flex justify-between items-center border-b border-white/10 pb-4 mb-4">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_theme(colors.emerald.500)]" />
                    <span className="text-sm font-semibold text-gray-200 tracking-wide uppercase">
                        Science Officer
                    </span>
                </div>
                <span className="text-[10px] text-gray-500 uppercase tracking-widest font-medium">
                    RAG Core Online
                </span>
            </div>

            {/* ═══ Messages Area ═══ */}
            <div className="flex-1 overflow-y-auto scrollbar-hide min-h-0">
                <div className="flex flex-col space-y-6 pb-4">
                    <AnimatePresence>
                        {messages.map((msg, i) => (
                            <motion.div key={i}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, delay: i === 0 ? 0.1 : 0 }}
                                className={msg.role === 'user' ? 'self-end w-full' : 'self-start w-full'}
                            >
                                {msg.role === 'assistant' ? (
                                    // AI Message - Left aligned, no colored box wrapper
                                    <div className="flex gap-3 text-gray-200 text-sm leading-relaxed pr-4">
                                        <OrbitIcon />
                                        <div className="flex-1 pt-1 break-words">
                                            {msg.content}
                                        </div>
                                    </div>
                                ) : (
                                    // User Message - Right aligned, indigo bubble
                                    <div className="bg-indigo-600 text-white px-4 py-3 rounded-2xl rounded-br-sm ml-auto max-w-[85%] text-sm shadow-md">
                                        {msg.content}
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </AnimatePresence>
                    {loading && <LoadingIndicator />}
                    <div ref={endRef} />
                </div>
            </div>

            {/* ═══ Quick Prompts and Input Area Docked at Bottom ═══ */}
            <div className="shrink-0 pt-4 mt-auto">
                {!hasConversation && !loading && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="flex flex-wrap gap-2 mb-4 justify-center">
                        {quickPrompts.map((p, i) => (
                            <button key={i} onClick={() => setInput(p)}
                                className="px-4 py-2 rounded-full border border-white/20 text-xs text-gray-300 hover:bg-white/10 hover:text-white transition-all cursor-pointer backdrop-blur-md">
                                {p}
                            </button>
                        ))}
                    </motion.div>
                )}

                <form onSubmit={send} className="relative w-full">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={loading ? 'Processing...' : 'Message Science Officer...'}
                        disabled={loading}
                        className="w-full bg-white/5 border border-white/10 rounded-xl pl-4 pr-12 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all text-sm shadow-sm"
                    />
                    <button type="submit" disabled={loading || !input.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-indigo-400 hover:text-indigo-300 disabled:opacity-30 disabled:hover:text-indigo-400 transition-colors cursor-pointer">
                        <SendIcon />
                    </button>
                </form>
                <div className="text-center mt-3">
                    <span className="text-[10px] text-gray-500 tracking-wide font-medium">EXOLENS RAG V2.0</span>
                </div>
            </div>

        </div>
    );
}

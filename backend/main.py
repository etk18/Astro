"""
ExoLens — FastAPI Backend
═════════════════════════
Endpoints:
  GET  /api/exoplanets  → Fetches real exoplanet data from NASA TAP API
  POST /api/chat        → RAG-powered Science Officer chat
"""

import os
import subprocess
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from rag_engine import RAGEngine

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("exolens")

# ── RAG Engine singleton ──
rag = RAGEngine()


# ── ChromaDB path (checked on every cold start) ──
CHROMA_DB_PATH = str(Path(__file__).parent / "chroma_db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup hook with cold-start detection for Render's ephemeral filesystem.
    If ChromaDB is missing (server woke from sleep), auto-rebuild it.
    """
    logger.info("🚀 Server waking up! Checking memory banks...")

    # Check if ChromaDB exists and has data
    if not os.path.exists(CHROMA_DB_PATH) or not os.listdir(CHROMA_DB_PATH):
        logger.warning("⚠️ Vector Database missing (Cold Start). Rebuilding knowledge base...")
        try:
            subprocess.run(
                ["python", "ingest_nasa_data.py"],
                check=True,
                cwd=str(Path(__file__).parent),
            )
            logger.info("✅ Knowledge base rebuilt successfully!")
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
    else:
        logger.info(f"✅ Vector Database found at {CHROMA_DB_PATH}. RAG is ready!")

    # Initialize RAG engine (loads embeddings, connects to ChromaDB, inits LLM)
    rag.seed_knowledge()
    logger.info("✅ RAG Engine initialized.")

    yield
    logger.info("👋 ExoLens backend shutting down.")


app = FastAPI(
    title="ExoLens API",
    description="Backend for ExoLens 3D Exoplanet Explorer",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow all origins for cloud deployment) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────────────────────
# Solar System + NASA Exoplanet Archive
# ────────────────────────────────────────────────────────────────
NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

NASA_QUERY = """
SELECT TOP 50
    pl_name, hostname, pl_bmassj, pl_radj, pl_orbper,
    pl_eqt, sy_dist, disc_year, discoverymethod
FROM ps
WHERE pl_bmassj IS NOT NULL
  AND pl_radj IS NOT NULL
  AND pl_eqt IS NOT NULL
  AND sy_dist IS NOT NULL
  AND default_flag = 1
ORDER BY disc_year DESC
"""

# Our Solar System — placed at the center of the 3D map
SOLAR_SYSTEM = [
    {"pl_name": "Mercury",  "hostname": "Sun", "pl_bmassj": 0.000174, "pl_radj": 0.0354, "pl_orbper": 87.97,   "pl_eqt": 440,  "sy_dist": 0, "disc_year": None, "discoverymethod": "Solar System", "is_solar": True},
    {"pl_name": "Venus",    "hostname": "Sun", "pl_bmassj": 0.00256,  "pl_radj": 0.0869, "pl_orbper": 224.7,   "pl_eqt": 737,  "sy_dist": 0, "disc_year": None, "discoverymethod": "Solar System", "is_solar": True},
    {"pl_name": "Earth",    "hostname": "Sun", "pl_bmassj": 0.00315,  "pl_radj": 0.0892, "pl_orbper": 365.25,  "pl_eqt": 288,  "sy_dist": 0, "disc_year": None, "discoverymethod": "Solar System", "is_solar": True},
    {"pl_name": "Mars",     "hostname": "Sun", "pl_bmassj": 0.000338, "pl_radj": 0.0475, "pl_orbper": 687.0,   "pl_eqt": 210,  "sy_dist": 0, "disc_year": None, "discoverymethod": "Solar System", "is_solar": True},
    {"pl_name": "Jupiter",  "hostname": "Sun", "pl_bmassj": 1.0,      "pl_radj": 1.0,    "pl_orbper": 4332.59, "pl_eqt": 165,  "sy_dist": 0, "disc_year": None, "discoverymethod": "Solar System", "is_solar": True},
    {"pl_name": "Saturn",   "hostname": "Sun", "pl_bmassj": 0.299,    "pl_radj": 0.843,  "pl_orbper": 10759.2, "pl_eqt": 134,  "sy_dist": 0, "disc_year": None, "discoverymethod": "Solar System", "is_solar": True},
    {"pl_name": "Uranus",   "hostname": "Sun", "pl_bmassj": 0.0457,   "pl_radj": 0.358,  "pl_orbper": 30688.5, "pl_eqt": 76,   "sy_dist": 0, "disc_year": None, "discoverymethod": "Solar System", "is_solar": True},
    {"pl_name": "Neptune",  "hostname": "Sun", "pl_bmassj": 0.054,    "pl_radj": 0.346,  "pl_orbper": 60182.0, "pl_eqt": 72,   "sy_dist": 0, "disc_year": None, "discoverymethod": "Solar System", "is_solar": True},
]


@app.get("/api/exoplanets")
async def get_exoplanets():
    """
    Fetch Solar System + real exoplanet data from NASA.
    Solar System is prepended so it appears at the 3D center.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                NASA_TAP_URL,
                params={
                    "query": NASA_QUERY.strip(),
                    "format": "json",
                },
            )
            response.raise_for_status()
            exoplanets = response.json()
            # Mark exoplanets as non-solar
            for p in exoplanets:
                p["is_solar"] = False
            logger.info(f"📡 Fetched {len(exoplanets)} exoplanets from NASA Archive")
            # Solar System first, then exoplanets
            return SOLAR_SYSTEM + exoplanets
    except httpx.HTTPStatusError as e:
        logger.error(f"NASA API error: {e.response.status_code}")
        raise HTTPException(status_code=502, detail="NASA API returned an error")
    except httpx.RequestError as e:
        logger.error(f"NASA API connection error: {e}")
        raise HTTPException(status_code=503, detail="Cannot reach NASA API")
    except Exception as e:
        logger.error(f"Unexpected error fetching exoplanets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ────────────────────────────────────────────────────────────────
# Chat Endpoint (RAG Pipeline)
# ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    planet_name: str
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Science Officer chat endpoint.
    Uses RAG pipeline: ChromaDB retrieval → LLM generation.
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        answer = rag.query_and_generate(
            planet_name=req.planet_name,
            question=req.question,
        )
        return ChatResponse(answer=answer)
    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Science Officer is temporarily unavailable. Please try again.",
        )


# ── Health Check ──
@app.get("/api/health")
async def health():
    return {"status": "online", "service": "ExoLens API"}

"""
ExoLens — RAG Engine
════════════════════
Retrieval-Augmented Generation pipeline:
  1. ChromaDB local vector store with HuggingFace embeddings
  2. Knowledge base seeded from exoplanet science documents
  3. Groq (primary) / Gemini (fallback) for LLM generation
  4. LangChain orchestrates retrieval → prompt → generation
"""

import os
import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("exolens.rag")


class RAGEngine:
    """
    Manages the full RAG pipeline:
      - Embedding model: all-MiniLM-L6-v2 (local, no API needed)
      - Vector store: ChromaDB (local SQLite-backed)
      - LLM: Groq (primary) → Gemini (fallback)
    """

    def __init__(self):
        self.collection_name = "exoplanet_knowledge"
        self.embed_model = None
        self.chroma_client = None
        self.collection = None
        self.llm = None

    def _init_embeddings(self):
        """Load the local HuggingFace embedding model."""
        if self.embed_model is None:
            logger.info("Loading embedding model: all-MiniLM-L6-v2...")
            self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Embedding model loaded.")

    def _init_chroma(self):
        """Initialize ChromaDB persistent client."""
        if self.chroma_client is None:
            db_path = str(Path(__file__).parent / "chroma_db")
            self.chroma_client = chromadb.PersistentClient(path=db_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"✅ ChromaDB initialized at {db_path}")

    def _init_llm(self):
        """Initialize LLM — Groq primary, Gemini fallback."""
        if self.llm is not None:
            return

        # Read keys at runtime (after load_dotenv in main.py)
        groq_key = os.getenv("GROQ_API_KEY", "")
        google_key = os.getenv("GOOGLE_API_KEY", "")

        # Try Groq first
        if groq_key and groq_key != "your_groq_api_key_here":
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    api_key=groq_key,
                    temperature=0.3,
                    max_tokens=1024,
                )
                logger.info("✅ LLM initialized: Groq (llama-3.3-70b-versatile)")
                return
            except Exception as e:
                logger.warning(f"Groq init failed: {e}, trying Gemini fallback...")

        # Fallback to Gemini
        if google_key and google_key != "your_gemini_api_key_here":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=google_key,
                    temperature=0.3,
                    max_output_tokens=1024,
                )
                logger.info("✅ LLM initialized: Gemini (gemini-2.0-flash)")
                return
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

        logger.error("❌ No LLM available! Set GROQ_API_KEY or GOOGLE_API_KEY in .env")

    def seed_knowledge(self):
        """
        Load exoplanet knowledge documents into ChromaDB.
        Reads .txt files from the knowledge/ directory, splits into
        chunks, embeds them, and upserts into the vector store.
        """
        self._init_embeddings()
        self._init_chroma()
        self._init_llm()

        # Check if already seeded
        if self.collection.count() > 0:
            logger.info(f"Knowledge base already seeded ({self.collection.count()} chunks)")
            return

        knowledge_dir = Path(__file__).parent / "knowledge"
        if not knowledge_dir.exists():
            logger.warning("No knowledge/ directory found. Skipping seed.")
            return

        documents = []
        metadatas = []
        ids = []

        for filepath in sorted(knowledge_dir.glob("*.txt")):
            text = filepath.read_text(encoding="utf-8")
            topic = filepath.stem.replace("_", " ").title()

            # Split into ~500-char chunks with overlap
            chunks = self._chunk_text(text, chunk_size=500, overlap=50)
            for i, chunk in enumerate(chunks):
                doc_id = f"{filepath.stem}_{i}"
                documents.append(chunk)
                metadatas.append({"source": filepath.name, "topic": topic, "chunk": i})
                ids.append(doc_id)

        if documents:
            # Embed all chunks at once
            embeddings = self.embed_model.encode(documents).tolist()
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"✅ Seeded {len(documents)} chunks from {len(list(knowledge_dir.glob('*.txt')))} files")
        else:
            logger.warning("No .txt files found in knowledge/ directory")

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start = end - overlap
        return chunks

    def query_and_generate(self, planet_name: str, question: str) -> str:
        """
        Full RAG pipeline:
          1. Embed the question
          2. Retrieve relevant chunks from ChromaDB
          3. Build a grounded prompt with context
          4. Generate answer via LLM
        """
        self._init_embeddings()
        self._init_chroma()
        self._init_llm()

        if self.llm is None:
            return (
                "⚠ Science Officer offline — no LLM API key configured. "
                "Please set GROQ_API_KEY or GOOGLE_API_KEY in backend/.env"
            )

        # ── Step 1: Retrieve relevant context ──
        query_embedding = self.embed_model.encode(
            f"{planet_name} {question}"
        ).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=["documents", "metadatas"],
        )

        # Combine retrieved chunks into context
        context_chunks = results["documents"][0] if results["documents"] else []
        context = "\n\n".join(context_chunks) if context_chunks else "No specific knowledge available."

        # ── Step 2: Build grounded prompt ──
        system_prompt = (
            "You are the Science Officer aboard the ExoLens space observatory. "
            "You are an expert astrophysicist specializing in exoplanet science. "
            "Answer the user's question about the specified exoplanet using the "
            "provided scientific context. Be precise, educational, and engaging. "
            "If the context doesn't fully cover the question, use your general "
            "astrophysics knowledge but note when you're going beyond the provided data. "
            "Keep answers concise (2-4 paragraphs max). Use scientific terminology "
            "but explain complex concepts clearly."
        )

        user_prompt = (
            f"## Currently Selected Planet: {planet_name}\n\n"
            f"## Scientific Context (from knowledge base):\n{context}\n\n"
            f"## User's Question:\n{question}\n\n"
            f"Provide a scientifically grounded answer as the Science Officer."
        )

        # ── Step 3: Generate via LLM ──
        from langchain_core.messages import SystemMessage, HumanMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        return response.content

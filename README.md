# ExoLens 🌌

**ExoLens** is an immersive, 3D exoplanet exploration application built to visualize alien worlds and NASA discovery data. It combines cutting-edge WebGL graphics with a Retrieval-Augmented Generation (RAG) AI "Science Officer" to answer your questions about the cosmos.

## ✨ Features

- **Interactive 3D Solar System & Exoplanets:** Smooth navigation through space using `three.js` and `@react-three/fiber`. Planets are sized, positioned, and shaded based on real world data (mass, equilibrium temperature).
- **Procedural PBR Textures:** High-resolution (up to 2K) procedurally generated planet surfaces. Features distinct Base Color, Bump, and Roughness maps calculated entirely in-browser, creating stunning visual depth, shiny oceans, and matte continents.
- **Cinematic Shaders:** Custom GLSL shaders provide domain-warped FBM terrain, atmospheric Rayleigh scattering, polar ice caps, and subsurface lava cracks on extreme-heat worlds.
- **Post-Processing Pipeline:** Bloom effects and a dual-layer, 8000-point rotating starfield for deeply immersive space visuals.
- **AI Science Officer (RAG Chatbot):** Integrated with Groq AI and ChromaDB to ingest scientific documents. Ask questions about atmospheric composition, habitability, and discovery methods, and receive scientifically grounded answers.
- **Premium UI/UX:** A true modern SaaS interface. Featuring strict glassmorphism (`backdrop-blur-2xl`), a hidden scrollbar chat pane, and sophisticated layout alignment reminiscent of tools like ChatGPT and Claude.

## 🚀 Tech Stack

### Frontend
- **React 18** + **Vite**
- **Three.js** / `@react-three/fiber` / `@react-three/drei`
- **@react-three/postprocessing** (Cinematic Bloom & Lighting)
- **Tailwind CSS v4** (Modern styling, Glassmorphism)
- **Framer Motion** (Fluid UI animations and layout transitions)

### Backend
- **FastAPI** (High-performance Python API)
- **ChromaDB** (Vector Database for RAG context)
- **LangChain** + **HuggingFace Embeddings** (`all-MiniLM-L6-v2`)
- **Groq API** (Ultra-fast LLM inference)
- **httpx** (Fetching live NASA Exoplanet Archive data)

## 🛠️ Usage Local Development

### Prerequisites
- Node.js (v18+)
- Python 3.9+
- A Groq API Key

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend` folder and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
5. Pre-compute the RAG Vector Database (Optional but recommended):
   ```bash
   python rag_engine.py
   ```
6. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
   *The backend will run on `http://localhost:8000`.*

### Frontend Setup
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
   *The application will launch at `http://localhost:5173`.*

## 🎨 Design Philosophy
ExoLens was built with a strict adherence to **Premium Science-Fiction Aesthetics**. The chat console behaves like a high-end command interface. Procedural textures guarantee that no user downloads massive gigabytes of image textures; every terrestrial detail, cloud layer, and gas giant band is mathematically calculated on the fly in the canvas.

## 📝 License
MIT License

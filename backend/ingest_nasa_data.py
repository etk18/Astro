#!/usr/bin/env python3
"""
ExoLens — NASA Exoplanet Data Ingestion Script
═══════════════════════════════════════════════
Fetches detailed descriptions of the top 50 most famous exoplanets,
chunks text with LangChain's RecursiveCharacterTextSplitter,
embeds with HuggingFace all-MiniLM-L6-v2, and stores in ChromaDB.

Usage:
    cd backend
    python ingest_nasa_data.py
"""

import os
import sys
import logging
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(message)s")
logger = logging.getLogger("exolens.ingest")

# ── ChromaDB config ──
CHROMA_DB_PATH = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "exoplanet_knowledge"

# ────────────────────────────────────────────────────────────────
# Famous Exoplanet Encyclopedia
# ────────────────────────────────────────────────────────────────
# Curated scientific descriptions of the most notable exoplanets.
# These provide rich context for the RAG Science Officer.

FAMOUS_EXOPLANETS = [
    {
        "name": "TRAPPIST-1b",
        "text": (
            "TRAPPIST-1b is the innermost planet of the TRAPPIST-1 system, a remarkable "
            "collection of seven Earth-sized rocky planets orbiting an ultracool M-dwarf star "
            "39 light-years away in the constellation Aquarius. TRAPPIST-1b has a mass of "
            "approximately 1.02 Earth masses and a radius of 1.12 Earth radii. It orbits "
            "extremely close to its host star at just 0.011 AU with an orbital period of only "
            "1.51 days. Due to its proximity to the star, TRAPPIST-1b receives about 4 times "
            "the irradiation Earth receives from the Sun, making its equilibrium temperature "
            "around 400 K (127°C). JWST observations in 2023 confirmed that TRAPPIST-1b lacks "
            "a substantial atmosphere, ruling out thick CO2 or water vapor envelopes. The planet "
            "is likely tidally locked, with one hemisphere perpetually facing the star. Its "
            "surface may resemble a bare, airless rocky world similar to Mercury."
        ),
    },
    {
        "name": "TRAPPIST-1e",
        "text": (
            "TRAPPIST-1e is widely considered the most potentially habitable planet in the "
            "TRAPPIST-1 system. With a mass of 0.69 Earth masses and a radius of 0.92 Earth "
            "radii, it has a density consistent with a rocky, iron-rich composition. TRAPPIST-1e "
            "orbits within the conservative habitable zone of its star at 0.029 AU with a period "
            "of 6.1 days. Its equilibrium temperature is estimated at 251 K (-22°C), comparable "
            "to Mars but potentially warmer with a greenhouse atmosphere. The planet's Earth "
            "Similarity Index (ESI) of ~0.85 makes it one of the most Earth-like worlds ever "
            "discovered. Climate models suggest that with a modest atmosphere, TRAPPIST-1e could "
            "sustain liquid water on its surface, particularly on the substellar hemisphere if "
            "tidally locked. The TRAPPIST-1 system's resonant chain architecture — where "
            "planetary orbital periods form near-perfect integer ratios — suggests the planets "
            "formed farther out and migrated inward through the protoplanetary disk."
        ),
    },
    {
        "name": "TRAPPIST-1f",
        "text": (
            "TRAPPIST-1f orbits near the outer edge of the habitable zone at 0.038 AU with a "
            "period of 9.2 days. It has a mass of 1.04 Earth masses and radius of 1.05 Earth "
            "radii. Its equilibrium temperature of about 219 K (-54°C) is below freezing, but "
            "a greenhouse atmosphere with CO2 could warm the surface above the melting point of "
            "water. TRAPPIST-1f has a notably low density (about 60% of Earth's), suggesting a "
            "significant water/ice content — potentially up to 20% of its mass. This makes it "
            "a strong candidate for an ocean world, with a deep global ocean potentially hundreds "
            "of kilometers deep. High-pressure ice phases (ice VI, VII) may form at the bottom, "
            "separating the liquid ocean from the rocky mantle."
        ),
    },
    {
        "name": "Proxima Centauri b",
        "text": (
            "Proxima Centauri b is the closest known exoplanet to Earth, orbiting Proxima "
            "Centauri, the nearest star to the Sun at just 4.24 light-years away. Discovered "
            "in 2016 via the radial velocity method, it has a minimum mass of 1.17 Earth masses "
            "and orbits within the habitable zone at 0.049 AU with a period of 11.2 days. "
            "However, Proxima Centauri is an active M-dwarf flare star that produces intense "
            "X-ray and UV radiation bursts. A massive superflare observed in 2018 was 100 times "
            "more powerful than the largest solar flares, potentially stripping away any "
            "atmosphere the planet may have had. If Proxima b retains an atmosphere, it is "
            "likely tidally locked, and habitability would depend on efficient atmospheric heat "
            "redistribution. The planet cannot be studied via the transit method as it does not "
            "cross in front of its star from Earth's perspective."
        ),
    },
    {
        "name": "Kepler-186f",
        "text": (
            "Kepler-186f was the first Earth-sized planet discovered in the habitable zone of "
            "another star. Found by the Kepler space telescope in 2014, it orbits a cool M1 "
            "dwarf star 580 light-years away. With a radius of 1.17 Earth radii, it sits at "
            "the outer edge of the habitable zone at 0.43 AU, receiving about one-third the "
            "stellar flux Earth gets from the Sun. Its orbital period is 129.9 days. The "
            "planet's mass has not been directly measured but is estimated at 1.4-3.8 Earth "
            "masses depending on composition. Kepler-186f's discovery was a landmark moment "
            "in exoplanet science, proving that Earth-sized planets exist in habitable zones. "
            "However, the planet's host star is dimmer than the Sun, so the irradiance at "
            "Kepler-186f's orbit is similar to what Mars receives. A dense CO2 atmosphere "
            "could potentially warm the surface enough for liquid water."
        ),
    },
    {
        "name": "Kepler-442b",
        "text": (
            "Kepler-442b is a super-Earth with a radius of 1.34 Earth radii and an estimated "
            "mass of 2.3 Earth masses, orbiting a K-type orange dwarf star 1,206 light-years "
            "away. It sits comfortably within the habitable zone at 0.41 AU with an orbital "
            "period of 112.3 days. Its equilibrium temperature is estimated at about 233 K "
            "(-40°C), which with a modest greenhouse effect could allow surface liquid water. "
            "Kepler-442b has one of the highest Earth Similarity Indices (ESI ~0.84) among "
            "known exoplanets. Its host star is a K-type star, which many astrobiologists "
            "consider potentially more favorable for life than Sun-like G-type stars due to "
            "their longer lifetimes (20-30 billion years), lower flare activity, and wider "
            "stable habitable zones."
        ),
    },
    {
        "name": "51 Pegasi b",
        "text": (
            "51 Pegasi b (also known as Dimidium) holds the distinction of being the first "
            "exoplanet ever discovered orbiting a Sun-like star, announced by Michel Mayor and "
            "Didier Queloz in 1995 — a discovery that earned them the 2019 Nobel Prize in "
            "Physics. This hot Jupiter has a minimum mass of 0.47 Jupiter masses and orbits "
            "incredibly close to its G-type host star at just 0.052 AU, completing an orbit "
            "in only 4.23 days. Its equilibrium temperature exceeds 1,200 K. The discovery of "
            "51 Peg b was revolutionary because it challenged prevailing theories of planet "
            "formation, which predicted giant planets could only form far from their stars "
            "like Jupiter. This led to the development of planetary migration theory, which "
            "explains how gas giants can spiral inward through gravitational interactions with "
            "the protoplanetary disk."
        ),
    },
    {
        "name": "HD 209458 b",
        "text": (
            "HD 209458 b (nicknamed Osiris) was the first exoplanet observed transiting its "
            "host star and the first exoplanet with a detected atmosphere. A hot Jupiter with "
            "0.69 Jupiter masses and 1.38 Jupiter radii, it orbits a Sun-like star 157 "
            "light-years away with a period of 3.52 days. In 2001, the Hubble Space Telescope "
            "detected sodium in its atmosphere — the first-ever atmospheric detection on an "
            "exoplanet. Subsequent observations revealed hydrogen, oxygen, and carbon escaping "
            "from the planet's atmosphere at a rate of 10,000 tonnes per second, forming a "
            "comet-like tail. This hydrodynamic atmospheric escape is driven by the intense "
            "stellar radiation the planet receives. HD 209458 b's inflated radius (larger "
            "than expected for its mass) remains a puzzle, with proposed explanations including "
            "tidal heating, ohmic dissipation, and kinetic energy deposition from stellar winds."
        ),
    },
    {
        "name": "WASP-121b",
        "text": (
            "WASP-121b is an ultra-hot Jupiter orbiting an F6V star 881 light-years away. "
            "With a mass of 1.18 Jupiter masses and an inflated radius of 1.81 Jupiter radii, "
            "it is so close to its star (0.025 AU, period 1.27 days) that it is being tidally "
            "distorted into an egg shape, on the verge of Roche lobe overflow. Its dayside "
            "temperature exceeds 2,500 K — hot enough to vaporize iron and other metals. JWST "
            "and Hubble observations have detected water vapor, iron, magnesium, chromium, and "
            "vanadium in its atmosphere. The planet exhibits a strong temperature inversion on "
            "its dayside, where the upper atmosphere is hotter than the lower layers due to "
            "absorption by metal oxides (TiO, VO). Phase curve observations reveal that heat "
            "redistribution from dayside to nightside is inefficient, creating extreme "
            "temperature contrasts. On the nightside, temperatures drop enough for iron and "
            "corundum (sapphire/ruby mineral) clouds to condense, making WASP-121b a world "
            "where it rains liquid gems."
        ),
    },
    {
        "name": "WASP-39b",
        "text": (
            "WASP-39b is a hot Saturn (0.28 Jupiter masses, 1.27 Jupiter radii) orbiting a "
            "G-type star 700 light-years away with a period of 4.06 days. It became famous in "
            "2022 when JWST produced the first-ever detection of carbon dioxide (CO2) in an "
            "exoplanet atmosphere, marking a historic milestone in atmospheric characterization. "
            "The JWST Early Release Science program also detected water vapor, sodium, potassium, "
            "and sulfur dioxide (SO2) in WASP-39b's atmosphere. The detection of SO2 was "
            "particularly significant as it is produced by photochemistry — UV light from the "
            "star driving chemical reactions in the upper atmosphere — the first evidence of "
            "photochemistry on an exoplanet. WASP-39b's atmosphere appears largely cloud-free, "
            "making it an exceptionally good target for transmission spectroscopy."
        ),
    },
    {
        "name": "GJ 1214 b",
        "text": (
            "GJ 1214 b is one of the best-studied sub-Neptune exoplanets. With a mass of 6.55 "
            "Earth masses and radius of 2.68 Earth radii, it orbits an M-dwarf star 48 "
            "light-years away with a period of 1.58 days. Its density (1.87 g/cm³) is too low "
            "for a purely rocky composition and too high for a hydrogen-dominated atmosphere, "
            "suggesting a water-rich composition — possibly a true 'water world' with a steam "
            "atmosphere overlying a deep ocean or supercritical water layer. For years, "
            "transmission spectroscopy showed a featureless flat spectrum, indicating high-altitude "
            "aerosol clouds blocking deeper atmospheric layers. JWST observations in 2023 finally "
            "penetrated these clouds, revealing a water-rich and methane-poor atmosphere with "
            "evidence of haze produced by photochemistry."
        ),
    },
    {
        "name": "55 Cancri e",
        "text": (
            "55 Cancri e (Janssen) is a super-Earth lava world orbiting an extremely close "
            "0.015 AU from its G-type host star (period 0.74 days). With a mass of 7.99 Earth "
            "masses and radius of 1.88 Earth radii, its surface temperature exceeds 2,500 K on "
            "the dayside. The planet is tidally locked, creating a permanent dayside hot enough "
            "to melt most rocks and a comparatively cooler nightside. JWST observations in 2024 "
            "detected emission from a substantial atmosphere dominated by CO2 and CO, the first "
            "confirmed atmosphere on a rocky super-Earth. Heat redistribution between the day "
            "and nightsides suggests a thick atmosphere cycling volatile gases. The planet's "
            "dayside likely features vast magma oceans, and the atmosphere may contain vaporized "
            "rock components including silicon monoxide and metal vapors."
        ),
    },
    {
        "name": "K2-18 b",
        "text": (
            "K2-18 b is a sub-Neptune orbiting in the habitable zone of an M-dwarf star 124 "
            "light-years away. With a mass of 8.63 Earth masses and radius of 2.61 Earth radii, "
            "it's classified as a 'Hycean' world candidate — a planet with a hydrogen-rich "
            "atmosphere potentially overlying a liquid water ocean. JWST observations in 2023 "
            "detected methane (CH4) and carbon dioxide (CO2) in its atmosphere while finding "
            "low levels of ammonia (NH3), consistent with a water ocean beneath a hydrogen "
            "envelope. Most controversially, the JWST data suggested a tentative detection of "
            "dimethyl sulfide (DMS), a molecule primarily produced by marine phytoplankton on "
            "Earth. If confirmed, DMS would be a potential biosignature, though the detection "
            "remains uncertain and debated. K2-18 b orbits at 0.15 AU with a period of 32.9 "
            "days and has an equilibrium temperature of about 255 K."
        ),
    },
    {
        "name": "TOI-700 d",
        "text": (
            "TOI-700 d is an Earth-sized planet orbiting in the habitable zone of a small, cool "
            "M2 dwarf star 101.4 light-years away. Discovered by NASA's TESS mission in 2020, "
            "it has a radius of 1.19 Earth radii and orbits at 0.163 AU with a period of 37.4 "
            "days. TOI-700 d receives about 86% of the stellar energy that Earth receives from "
            "the Sun. Climate models show it could support surface liquid water under a range "
            "of atmospheric compositions. In 2023, TESS also discovered TOI-700 e, another "
            "Earth-sized planet in the optimistic habitable zone, making TOI-700 a particularly "
            "interesting multi-planet system. The host star is relatively quiet for an M-dwarf, "
            "with no observed flares during the first 11 months of TESS monitoring."
        ),
    },
    {
        "name": "LHS 1140 b",
        "text": (
            "LHS 1140 b is a rocky super-Earth orbiting in the habitable zone of a quiet "
            "M4.5 dwarf star 49 light-years away. With a mass of 5.6 Earth masses and radius "
            "of 1.73 Earth radii, its high density (7.5 g/cm³) indicates a large iron core "
            "composing up to 70% of the planet's mass. JWST observations in 2024 detected "
            "hints of an atmosphere with potential nitrogen (N2) content, which would be "
            "remarkable for a planet orbiting an M-dwarf. LHS 1140 b orbits at 0.094 AU with "
            "a period of 24.7 days. Its host star is one of the least active M-dwarfs known, "
            "making it an ideal target for atmospheric characterization. If confirmed, the "
            "nitrogen-rich atmosphere would strongly favor habitability, as nitrogen is a key "
            "atmospheric buffer gas on Earth."
        ),
    },
    {
        "name": "HR 8799 b",
        "text": (
            "HR 8799 b is the outermost of four directly imaged giant planets orbiting the "
            "young A5/F0 star HR 8799, located 129 light-years away. With a mass of about 5-7 "
            "Jupiter masses and an orbital distance of 68 AU, it takes approximately 460 years "
            "to complete one orbit. The entire HR 8799 system was imaged in 2008-2010, marking "
            "the first multi-planet system captured by direct imaging. The planets are young "
            "(~30 million years old) and still glowing from the heat of formation, making them "
            "visible in infrared. Spectroscopy of HR 8799 b has revealed water vapor, methane, "
            "and carbon monoxide in its atmosphere, with non-equilibrium chemistry indicating "
            "strong vertical mixing. The system also contains two debris belts analogous to the "
            "asteroid belt and Kuiper belt in our Solar System."
        ),
    },
    {
        "name": "Beta Pictoris b",
        "text": (
            "Beta Pictoris b is a directly imaged gas giant orbiting the young A6V star Beta "
            "Pictoris, 63 light-years away. The planet has a mass of about 11 Jupiter masses "
            "and orbits at 9-10 AU with a period of approximately 21 years. Beta Pic b was "
            "one of the first exoplanets to be directly imaged (2008) and the first to have "
            "its rotation rate measured — it spins at approximately 25 km/s at the equator, "
            "making it rotate faster than any planet in our Solar System (Jupiter rotates at "
            "12.6 km/s). The planet is embedded in a massive debris disk that extends hundreds "
            "of AU from the star. A second planet, Beta Pictoris c, was later discovered at "
            "2.7 AU. The system is only about 23 million years old, providing a snapshot of "
            "planetary system evolution in its earliest stages."
        ),
    },
    {
        "name": "Kepler-452b",
        "text": (
            "Kepler-452b was dubbed 'Earth's older cousin' when discovered in 2015. It orbits "
            "a G2V star (the same spectral type as the Sun) at a distance of 1.05 AU — nearly "
            "identical to Earth's orbital distance — with a period of 384.8 days. Its radius "
            "of 1.63 Earth radii places it near the boundary between super-Earths and mini-"
            "Neptunes. The host star Kepler-452 is about 6 billion years old (1.5 billion years "
            "older than the Sun), giving Kepler-452b more time for potential biological evolution. "
            "However, at 1,402 light-years away, it is too distant for detailed atmospheric "
            "characterization with current technology. The planet receives about 10% more stellar "
            "flux than Earth, and models suggest it could be experiencing a runaway greenhouse "
            "effect, similar to what Venus may have undergone."
        ),
    },
    {
        "name": "Kepler-22b",
        "text": (
            "Kepler-22b was the first planet confirmed by the Kepler mission to orbit within "
            "the habitable zone of a Sun-like (G5V) star. Located 635 light-years away, it has "
            "a radius of 2.38 Earth radii and an orbital period of 289.9 days at 0.849 AU from "
            "its star. Its equilibrium temperature is about 262 K (-11°C) assuming an albedo "
            "similar to Earth's. The planet's size places it in the sub-Neptune category, and "
            "its mass has not been precisely measured, with estimates ranging from 9 to 36 Earth "
            "masses. If it has a rocky composition, its surface gravity could be about twice "
            "Earth's. If it has a large water or gas envelope, it could be a mini-Neptune with "
            "no solid surface. Kepler-22b's discovery in 2011 demonstrated that Sun-like stars "
            "host planets in their habitable zones."
        ),
    },
    {
        "name": "Kepler-16b",
        "text": (
            "Kepler-16b is the first confirmed circumbinary planet — a world orbiting two stars "
            "simultaneously, famously compared to Luke Skywalker's home planet Tatooine from "
            "Star Wars. The planet is a Saturn-mass gas giant (0.33 Jupiter masses) orbiting a "
            "pair of K and M dwarf stars 245 light-years away. It orbits the binary at 0.7 AU "
            "with a period of 228.8 days. Despite being near the habitable zone, Kepler-16b is "
            "a gas giant unlikely to support life. However, if it has large rocky moons, those "
            "moons could potentially be habitable. The planet's existence demonstrated that "
            "planet formation can occur in the dynamically complex environment of a binary "
            "system, where gravitational perturbations from two stars were thought to prevent "
            "planetesimal accretion."
        ),
    },
    {
        "name": "PSR B1257+12 b",
        "text": (
            "PSR B1257+12 b (Draugr) is one of the first exoplanets ever discovered (1992) and "
            "remains one of the strangest. It orbits a millisecond pulsar — a rapidly rotating "
            "neutron star — rather than a normal star. With a mass of only 0.02 Earth masses "
            "(about twice the mass of the Moon), it is one of the least massive exoplanets known. "
            "The pulsar PSR B1257+12 hosts at least three planets, all detected via precise "
            "timing of the pulsar's radio pulses. The origin of these pulsar planets is debated: "
            "they may have formed from a disk of material created when the pulsar's companion "
            "star was destroyed, or they could be remnants of a pre-existing planetary system "
            "that survived the supernova explosion. These worlds are bathed in intense radiation "
            "from the pulsar and are considered uninhabitable."
        ),
    },
    {
        "name": "HAT-P-7b",
        "text": (
            "HAT-P-7b is a massive hot Jupiter (1.78 Jupiter masses, 1.43 Jupiter radii) "
            "orbiting an F-type star 1,044 light-years away with a period of 2.2 days. It is "
            "notable for having a retrograde orbit — it orbits in the opposite direction to its "
            "star's rotation — providing evidence for violent gravitational scattering in its "
            "history. Kepler observations revealed changing reflectivity on the planet's dayside, "
            "interpreted as variable cloud cover driven by powerful equatorial jets. The clouds "
            "on HAT-P-7b are likely made of corundum (aluminum oxide, the mineral that forms "
            "rubies and sapphires). Wind speeds in its atmosphere are estimated to exceed "
            "8,000 km/h, driving the cloud patterns to shift on timescales of days."
        ),
    },
    {
        "name": "GJ 367 b",
        "text": (
            "GJ 367 b is an ultra-short-period planet orbiting an M1 dwarf star 31 light-years "
            "away, completing one orbit in just 7.7 hours. With a mass of 0.55 Earth masses and "
            "a radius of 0.72 Earth radii (smaller than Earth), it has an extremely high density "
            "of 8.1 g/cm³ — about 46% denser than Earth. This indicates GJ 367 b has a massive "
            "iron core making up approximately 86% of its total radius, similar in proportional "
            "size to Mercury's core. The planet's dayside temperature exceeds 1,500 K, likely "
            "creating a molten iron-silicate surface. GJ 367 b may be the exposed iron core of "
            "a once-larger planet that lost its mantle through stellar irradiation or a giant "
            "impact event."
        ),
    },
    {
        "name": "WASP-76b",
        "text": (
            "WASP-76b is an ultra-hot Jupiter famous for its 'iron rain.' Orbiting an F7 star "
            "634 light-years away at just 0.033 AU (period 1.81 days), its dayside temperature "
            "reaches 2,400 K — hot enough to vaporize iron. High-resolution spectroscopy "
            "detected iron vapor (Fe I) concentrated on the planet's evening terminator (the "
            "boundary between dayside and nightside), but absent from the morning terminator. "
            "This asymmetry reveals that iron vaporizes on the scorching dayside, is carried to "
            "the nightside by powerful winds (estimated at 5-10 km/s), condenses into iron "
            "droplets as temperatures fall below 1,800 K on the nightside, and rains down as "
            "liquid iron before being recirculated. The planet has a mass of 0.92 Jupiter masses "
            "but an inflated radius of 1.83 Jupiter radii."
        ),
    },
    {
        "name": "CoRoT-7b",
        "text": (
            "CoRoT-7b was the first rocky exoplanet with a measured density, confirmed in 2009. "
            "With a mass of 4.73 Earth masses and radius of 1.58 Earth radii, its density of "
            "6.6 g/cm³ is consistent with an Earth-like rocky/iron composition. It orbits a "
            "G9V star 489 light-years away at just 0.017 AU with a period of 0.85 days. The "
            "planet's dayside temperature is estimated at 2,600 K, hot enough to maintain a "
            "permanent magma ocean. Its atmosphere (if any survives the intense stellar "
            "irradiation) would consist of vaporized rock — sodium, potassium, silicon monoxide, "
            "and iron vapor. CoRoT-7b demonstrates that rocky planets can exist in extreme "
            "environments previously thought exclusive to gas giants."
        ),
    },
    {
        "name": "Kepler-10b",
        "text": (
            "Kepler-10b was the first confirmed rocky planet discovered by the Kepler space "
            "telescope (2011). With a mass of 4.56 Earth masses and radius of 1.47 Earth radii, "
            "its density of 8.8 g/cm³ makes it one of the densest super-Earths known, suggesting "
            "a large iron core similar to Mercury. It orbits a G-type star 608 light-years away "
            "at 0.017 AU with an ultra-short period of 0.84 days. The dayside temperature "
            "exceeds 1,800 K. Kepler-10b is far too hot for habitability but provided critical "
            "confirmation that small, rocky worlds are common in the galaxy."
        ),
    },
    {
        "name": "Kepler-62f",
        "text": (
            "Kepler-62f is a super-Earth orbiting in the habitable zone of a K2V star 1,200 "
            "light-years away. With a radius of 1.41 Earth radii and an orbital period of 267.3 "
            "days at 0.718 AU, it receives about 41% of Earth's stellar flux. Climate models "
            "suggest that with a CO2-rich atmosphere (3 to 5 bars of CO2), Kepler-62f could "
            "maintain surface temperatures above freezing across much of its surface. Its mass "
            "has not been measured but is estimated at 2.8 Earth masses assuming a rocky "
            "composition. Kepler-62f is part of a five-planet system, with another potentially "
            "habitable super-Earth, Kepler-62e, orbiting closer in."
        ),
    },
    {
        "name": "Kepler-438b",
        "text": (
            "Kepler-438b held the record for highest Earth Similarity Index (ESI ~0.88) when "
            "discovered in 2015. It has a radius of 1.12 Earth radii and orbits in the habitable "
            "zone of an M-dwarf star 472 light-years away with a period of 35.2 days. However, "
            "subsequent studies revealed that the host star produces powerful superflares roughly "
            "every 100 days, each releasing 10 times more energy than the most powerful solar "
            "flares. These flares likely strip away any atmosphere Kepler-438b might have, "
            "severely diminishing its habitability prospects despite its favorable orbital "
            "position. This discovery highlighted the importance of considering stellar activity "
            "when assessing exoplanet habitability."
        ),
    },
    {
        "name": "Kepler-90",
        "text": (
            "The Kepler-90 system holds the record for most known planets around a single star "
            "other than the Sun — eight confirmed planets. The system orbits a G0 star 2,545 "
            "light-years away. The eighth planet, Kepler-90i, was discovered in 2017 using "
            "machine learning applied to Kepler data, marking one of the first AI-assisted "
            "exoplanet discoveries. Remarkably, the entire Kepler-90 system is compressed "
            "within an orbital radius equivalent to Earth's distance from the Sun. The system "
            "includes rocky inner planets and gas giants further out, mirroring the architecture "
            "of our Solar System in miniature."
        ),
    },
    {
        "name": "HD 189733 b",
        "text": (
            "HD 189733 b is one of the most extensively studied hot Jupiters, orbiting a K1V "
            "star 64.5 light-years away with a period of 2.22 days. With 1.14 Jupiter masses "
            "and 1.14 Jupiter radii, it has a strikingly blue color — not from water oceans but "
            "from silicate particles (glass) in its atmosphere that scatter blue light via "
            "Rayleigh scattering. Wind speeds on HD 189733 b reach 8,700 km/h (5,400 mph), and "
            "the temperature difference between dayside (~1,200 K) and nightside (~970 K) "
            "creates violent weather. The planet's atmosphere contains water vapor, methane, CO2, "
            "and CO. It effectively rains molten glass sideways across the planet, driven by the "
            "supersonic equatorial jet stream."
        ),
    },
    {
        "name": "Gliese 581 g",
        "text": (
            "Gliese 581 g (if confirmed) would be one of the most Earth-like planets ever "
            "discovered. Announced in 2010, it orbits in the middle of the habitable zone of "
            "the M3V red dwarf Gliese 581, 20.4 light-years away. With an estimated mass of "
            "3.1 Earth masses, orbital period of 36.6 days, and equilibrium temperature near "
            "228 K, it was considered the strongest candidate for habitability at the time. "
            "However, its existence has been disputed by independent reanalyses of the radial "
            "velocity data, and it remains unconfirmed. The controversy surrounding Gliese 581 g "
            "highlighted the challenges of detecting small planets via radial velocity and the "
            "importance of independent confirmation in exoplanet science."
        ),
    },
    {
        "name": "KELT-9b",
        "text": (
            "KELT-9b is the hottest known exoplanet, with a dayside temperature of approximately "
            "4,600 K — hotter than most stars. It orbits a B9.5/A0 star that is itself extremely "
            "hot (10,170 K surface temperature). With a mass of 2.88 Jupiter masses and radius "
            "of 1.89 Jupiter radii, KELT-9b orbits at just 0.035 AU with a period of 1.48 days. "
            "At such extreme temperatures, molecules cannot exist and the atmosphere consists of "
            "atomized hydrogen, ionized metals, and potentially even dissociated water. Iron and "
            "titanium have been spectroscopically confirmed in its atmosphere as individual atoms "
            "rather than compounds. The planet is losing mass at a rate that could completely "
            "evaporate it within a few billion years."
        ),
    },
    {
        "name": "GJ 1132 b",
        "text": (
            "GJ 1132 b is a rocky planet orbiting an M-dwarf star just 41 light-years away. "
            "With a mass of 1.66 Earth masses and radius of 1.16 Earth radii, it is one of the "
            "nearest Earth-sized worlds amenable to atmospheric study. Hubble observations "
            "suggested a thick atmosphere containing hydrogen cyanide (HCN) and methane, "
            "though JWST follow-up data has yet to confirm these detections definitively. If "
            "GJ 1132 b does possess an atmosphere, it may be a secondary atmosphere outgassed "
            "from volcanic activity, as the original primordial atmosphere was likely stripped "
            "by the star's early high UV activity. The planet orbits at 0.015 AU with a period "
            "of 1.63 days and has a dayside temperature of about 580 K."
        ),
    },
    {
        "name": "Tau Ceti e",
        "text": (
            "Tau Ceti e is a super-Earth candidate orbiting Tau Ceti, one of the closest Sun-like "
            "stars at just 11.9 light-years away. With an estimated minimum mass of 3.93 Earth "
            "masses, it orbits at 0.538 AU with a period of 162.9 days, placing it in the inner "
            "edge of the habitable zone. Tau Ceti is a G8V star, slightly smaller and cooler than "
            "the Sun. However, the star is known to have a massive debris disk — about 10 times "
            "the mass of our Solar System's Kuiper Belt — which means Tau Ceti e may be subjected "
            "to intense bombardment from comets and asteroids, potentially making its surface "
            "inhospitable. The planet was detected via radial velocity and has not been confirmed "
            "via transit."
        ),
    },
    {
        "name": "Wolf 1061 c",
        "text": (
            "Wolf 1061 c is a rocky super-Earth orbiting in the habitable zone of an M3V red "
            "dwarf star located just 14.1 light-years from Earth — making it one of the closest "
            "potentially habitable exoplanets known. It has a minimum mass of 3.41 Earth masses "
            "and orbits at 0.084 AU with a period of 17.9 days. Its equilibrium temperature is "
            "estimated at 223 K (-50°C), which could be warmed to habitable temperatures with "
            "a greenhouse atmosphere. The Wolf 1061 system contains at least three planets, "
            "with planet b too hot and planet d too cold for liquid water, while planet c sits "
            "in the sweet spot. Its proximity makes it a promising target for future atmospheric "
            "characterization with next-generation telescopes."
        ),
    },
    {
        "name": "Ross 128 b",
        "text": (
            "Ross 128 b is a temperate Earth-mass planet orbiting the quiet red dwarf Ross 128, "
            "located 11 light-years from Earth. With a minimum mass of 1.35 Earth masses, it "
            "orbits at 0.049 AU with a period of 9.9 days. Despite its close orbit, Ross 128 b "
            "receives only 1.38 times Earth's stellar flux because its host star is very dim. "
            "Its equilibrium temperature is estimated at 213-280 K depending on atmospheric "
            "assumptions. Crucially, Ross 128 is one of the quietest M-dwarfs known — it shows "
            "no evidence of flare activity, making Ross 128 b one of the best candidates for "
            "habitability around a red dwarf. The planet is currently the second-closest "
            "temperate world after Proxima Centauri b."
        ),
    },
    {
        "name": "Kepler-1649c",
        "text": (
            "Kepler-1649c is one of the most Earth-like exoplanets in terms of both size and "
            "temperature. It has a radius of 1.06 Earth radii and receives 75% of Earth's "
            "stellar flux from its M5V host star 301 light-years away. Its orbital period is "
            "19.5 days at 0.0649 AU. Interestingly, Kepler-1649c was initially missed by "
            "automated planet-detection algorithms and was discovered in 2020 by the Kepler "
            "False Positive Working Group during a manual review of rejected signals. This "
            "highlights the fact that automated pipelines can miss genuine planet signals. The "
            "planet has a near 9:4 orbital resonance with its inner companion Kepler-1649b."
        ),
    },
    {
        "name": "HAT-P-11b",
        "text": (
            "HAT-P-11b is a Neptune-sized exoplanet orbiting a K4 dwarf star 123 light-years "
            "away. With a mass of 26.7 Earth masses and radius of 4.73 Earth radii, it has a "
            "relatively long period for a hot planet: 4.89 days at 0.053 AU. HAT-P-11b is "
            "notably the first Neptune-sized exoplanet with a clear atmosphere detected — "
            "Hubble observations revealed strong water absorption features without cloud "
            "interference, allowing the first precise measurement of water abundance in a "
            "Neptune-class atmosphere. The planet also has a significantly oblique orbit "
            "(misaligned with the star's rotation axis), suggesting a history of gravitational "
            "interaction with other bodies in the system."
        ),
    },
    {
        "name": "TYC 8998-760-1 b",
        "text": (
            "TYC 8998-760-1 b is part of the first directly imaged multi-planet system around "
            "a Sun-like star. Captured by ESO's Very Large Telescope in 2020, the system shows "
            "two gas giants orbiting a young (17 million years old) solar analog 300 light-years "
            "away. Planet b has a mass of about 14 Jupiter masses and orbits at 160 AU, while "
            "planet c has about 6 Jupiter masses at 320 AU. These enormous orbital distances "
            "allowed direct imaging despite the planets' relative faintness. The system provides "
            "a rare glimpse of a young planetary system in its early evolution, potentially "
            "analogous to the early Solar System before the giant planets migrated to their "
            "current positions."
        ),
    },
    {
        "name": "GJ 504 b",
        "text": (
            "GJ 504 b (also known as Kappa Andromedae b) is a directly imaged gas giant with "
            "the distinction of being one of the lowest-mass planets directly imaged around a "
            "Sun-like star. Orbiting a G0V star 57 light-years away at approximately 43.5 AU, "
            "it has an estimated mass of 4 Jupiter masses. Most remarkably, GJ 504 b has a "
            "magenta/dark pink color in near-infrared observations, making it one of the most "
            "visually distinctive exoplanets. Its color arises from its relatively cool "
            "temperature (~510 K) for a directly imaged planet, where atmospheric methane "
            "absorption and cloud-free conditions produce the unique pink hue."
        ),
    },
    {
        "name": "Upsilon Andromedae d",
        "text": (
            "Upsilon Andromedae d is a massive gas giant (10.25 Jupiter masses) orbiting an "
            "F8V star 44 light-years away at 2.53 AU with a period of 1,276 days. It is part "
            "of the first multi-planet system discovered around a main-sequence star other than "
            "the Sun (1999). The system has four known planets, with planet d's highly eccentric "
            "orbit (e=0.32) causing dramatic seasonal temperature variations. Infrared phase "
            "curve observations by the Spitzer Space Telescope showed that the planet's "
            "brightest (hottest) point is offset by about 80° from the substellar point, "
            "indicating extreme atmospheric dynamics and heat transport."
        ),
    },
    {
        "name": "Kepler-11",
        "text": (
            "The Kepler-11 system is a remarkable example of a compact multi-planet system. "
            "Six planets (b through g) orbit a Sun-like G-type star 2,000 light-years away, "
            "with the inner five planets orbiting within 0.25 AU — closer than Mercury is to "
            "the Sun. All six planets are larger than Earth (radii 1.8-4.2 Earth radii) but "
            "have surprisingly low densities, indicating thick gaseous envelopes surrounding "
            "small rocky or icy cores. The system's discovery in 2011 challenged models of "
            "planet formation and packing, as the tightly packed configuration requires precise "
            "orbital dynamics to remain stable over billions of years."
        ),
    },
    {
        "name": "TOI-1452 b",
        "text": (
            "TOI-1452 b is a super-Earth that may be the best candidate for a true ocean world "
            "discovered to date. Orbiting an M4-dwarf star 100 light-years away in the Draco "
            "constellation, it has a mass of 4.82 Earth masses and radius of 1.67 Earth radii. "
            "Its density of 5.6 g/cm³ is consistent with up to 30% of its mass being water — "
            "an enormous proportion that would create a global ocean hundreds of kilometers deep. "
            "The planet orbits at 0.061 AU with a period of 11.1 days. Interior models suggest "
            "the water layer may extend from a liquid surface ocean through high-pressure ice "
            "phases (ice VI, VII) down to a rocky core. TOI-1452 b is an excellent JWST target "
            "for searching for water vapor in its atmosphere."
        ),
    },
    {
        "name": "WASP-17b",
        "text": (
            "WASP-17b holds the distinction of being one of the largest and most inflated "
            "exoplanets ever discovered. Despite having only about half the mass of Jupiter "
            "(0.49 Jupiter masses), its radius is 1.89 Jupiter radii — nearly twice Jupiter's "
            "diameter — giving it a density of just 0.06 g/cm³, comparable to styrofoam. The "
            "planet orbits a retrograde orbit around an F6 star 1,000 light-years away with a "
            "period of 3.74 days. JWST observations in 2024 detected quartz (SiO2) crystals "
            "in its atmosphere — the first detection of silica clouds on any exoplanet. These "
            "quartz nanocrystals, about 10 nanometers in size, float in the planet's upper "
            "atmosphere at temperatures around 1,400 K."
        ),
    },
    {
        "name": "GJ 3470 b",
        "text": (
            "GJ 3470 b is a 'warm Neptune' orbiting an M1.5 dwarf star 96 light-years away. "
            "With a mass of 13.9 Earth masses and radius of 4.57 Earth radii, it orbits at "
            "0.036 AU with a period of 3.34 days. The planet is notable for its rapid "
            "atmospheric mass loss — Hubble observations detected a massive cloud of hydrogen "
            "gas escaping the planet, evaporating at a rate 100 times faster than GJ 436 b. "
            "This makes GJ 3470 b a planet in transition — over billions of years, it may lose "
            "its entire gaseous envelope, transforming from a warm Neptune into a bare rocky "
            "super-Earth. This process, called photoevaporation, is believed to be responsible "
            "for the observed 'radius valley' between super-Earths and sub-Neptunes."
        ),
    },
    {
        "name": "Kepler-7b",
        "text": (
            "Kepler-7b is one of the lowest-density exoplanets known, with a mass of only 0.44 "
            "Jupiter masses but a radius of 1.61 Jupiter radii, giving it a density less than "
            "that of styrofoam (0.14 g/cm³). It was one of the first five planets confirmed by "
            "the Kepler mission. Most significantly, Kepler-7b was the first exoplanet to have "
            "its cloud map created — Kepler observations showed asymmetric reflectivity across "
            "the planet's disk, revealing clouds predominantly on the western hemisphere of the "
            "dayside. This was the first direct observational evidence of cloud distribution "
            "patterns on an exoplanet and confirmed theoretical predictions about atmospheric "
            "circulation on tidally locked hot Jupiters."
        ),
    },
    {
        "name": "KOI-5Ab",
        "text": (
            "KOI-5Ab is a planet orbiting in a triple star system. It was one of the very first "
            "planet candidates identified by Kepler (the second candidate found) but took over "
            "a decade to confirm due to the complexity of the three-star system. The planet is "
            "a sub-Neptune with a radius of about 7 Earth radii, orbiting the primary star "
            "KOI-5A (a G-type star) every 5 days. The orbit of KOI-5Ab is misaligned with both "
            "the binary orbital plane and the tertiary star's orbit, suggesting the gravitational "
            "influence of the companion stars 'kicked' the planet into an oblique orbit. KOI-5 "
            "illustrates how multi-star systems can create unusual planetary architectures."
        ),
    },
]


def main():
    """Main ingestion pipeline."""
    logger.info("═" * 60)
    logger.info("  ExoLens — NASA Exoplanet Data Ingestion")
    logger.info("═" * 60)

    # ── 1. Initialize embedding model ──
    logger.info("Loading embedding model: all-MiniLM-L6-v2...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("✅ Embedding model loaded.")

    # ── 2. Initialize ChromaDB ──
    logger.info(f"Initializing ChromaDB at: {CHROMA_DB_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"✅ ChromaDB ready. Current count: {collection.count()} chunks")

    # ── 3. Chunk text with LangChain's RecursiveCharacterTextSplitter ──
    logger.info("Chunking exoplanet descriptions...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_documents = []
    all_metadatas = []
    all_ids = []

    for planet in FAMOUS_EXOPLANETS:
        chunks = text_splitter.split_text(planet["text"])
        for i, chunk in enumerate(chunks):
            doc_id = f"planet_{planet['name'].lower().replace(' ', '_')}_{i}"
            all_documents.append(chunk)
            all_metadatas.append({
                "planet_name": planet["name"],
                "source": "NASA Exoplanet Encyclopedia (curated)",
                "chunk_index": i,
                "total_chunks": len(chunks),
            })
            all_ids.append(doc_id)

    logger.info(f"Created {len(all_documents)} chunks from {len(FAMOUS_EXOPLANETS)} exoplanets")

    # ── 4. Also ingest existing knowledge base files ──
    knowledge_dir = Path(__file__).parent / "knowledge"
    if knowledge_dir.exists():
        for filepath in sorted(knowledge_dir.glob("*.txt")):
            text = filepath.read_text(encoding="utf-8")
            topic = filepath.stem.replace("_", " ").title()
            chunks = text_splitter.split_text(text)
            for i, chunk in enumerate(chunks):
                doc_id = f"kb_{filepath.stem}_{i}"
                all_documents.append(chunk)
                all_metadatas.append({
                    "planet_name": "general",
                    "source": filepath.name,
                    "topic": topic,
                    "chunk_index": i,
                })
                all_ids.append(doc_id)
        logger.info(f"Total chunks after knowledge base: {len(all_documents)}")

    # ── 5. Generate embeddings ──
    logger.info("Generating embeddings (this may take a moment)...")
    embeddings = embed_model.encode(
        all_documents,
        show_progress_bar=True,
        batch_size=32,
    ).tolist()
    logger.info(f"✅ Generated {len(embeddings)} embeddings")

    # ── 6. Upsert into ChromaDB ──
    logger.info("Upserting into ChromaDB...")
    # ChromaDB has a batch limit, so we chunk the upserts
    BATCH_SIZE = 100
    for start in range(0, len(all_documents), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(all_documents))
        collection.upsert(
            ids=all_ids[start:end],
            embeddings=embeddings[start:end],
            documents=all_documents[start:end],
            metadatas=all_metadatas[start:end],
        )
    logger.info(f"✅ Upserted {len(all_documents)} chunks into ChromaDB")

    # ── 7. Verify ──
    final_count = collection.count()
    logger.info("═" * 60)
    logger.info(f"  ✅ Ingestion complete! ChromaDB now has {final_count} chunks")
    logger.info("═" * 60)

    # Quick test query
    test_query = "Tell me about habitable planets"
    test_embedding = embed_model.encode(test_query).tolist()
    results = collection.query(
        query_embeddings=[test_embedding],
        n_results=3,
        include=["documents", "metadatas"],
    )
    logger.info("\n🔍 Test query: '%s'", test_query)
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        logger.info(f"  Result {i+1} [{meta.get('planet_name', meta.get('topic', 'N/A'))}]: {doc[:100]}...")


if __name__ == "__main__":
    main()

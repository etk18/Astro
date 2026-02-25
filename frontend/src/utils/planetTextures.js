import * as THREE from 'three';

/**
 * Procedural Planet Texture Generator (High-Res + PBR Maps)
 * Generates Base Color, Bump, and Roughness maps simultaneously.
 */

function hash(x, y) {
    let n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
    return n - Math.floor(n);
}

function smoothNoise(x, y) {
    const ix = Math.floor(x), iy = Math.floor(y);
    const fx = x - ix, fy = y - iy;
    const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
    const a = hash(ix, iy), b = hash(ix + 1, iy);
    const c = hash(ix, iy + 1), d = hash(ix + 1, iy + 1);
    return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy;
}

function fbm(x, y, octaves = 8) {
    let val = 0, amp = 0.5, freq = 1;
    for (let i = 0; i < octaves; i++) {
        val += amp * smoothNoise(x * freq, y * freq);
        amp *= 0.5;
        freq *= 2.1;
    }
    return val;
}

function lerp(a, b, t) { return a + (b - a) * Math.max(0, Math.min(1, t)); }
function lerpColor(r1, g1, b1, r2, g2, b2, t) {
    return [lerp(r1, r2, t), lerp(g1, g2, t), lerp(b1, b2, t)];
}

// ── Master Generator for PBR Maps ──
function generatePBRTextures(width, height, pixelFn) {
    const c1 = document.createElement('canvas'); c1.width = width; c1.height = height;
    const c2 = document.createElement('canvas'); c2.width = width; c2.height = height;
    const c3 = document.createElement('canvas'); c3.width = width; c3.height = height;

    const ctx1 = c1.getContext('2d');
    const ctx2 = c2.getContext('2d');
    const ctx3 = c3.getContext('2d');

    const img1 = ctx1.createImageData(width, height);
    const img2 = ctx2.createImageData(width, height);
    const img3 = ctx3.createImageData(width, height);

    const d1 = img1.data, d2 = img2.data, d3 = img3.data;

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const u = x / width;
            const v = y / height;
            const { color: [r, g, b], bump, roughness } = pixelFn(u, v, x, y);

            const idx = (y * width + x) * 4;

            // Color
            d1[idx] = Math.max(0, Math.min(255, Math.round(r)));
            d1[idx + 1] = Math.max(0, Math.min(255, Math.round(g)));
            d1[idx + 2] = Math.max(0, Math.min(255, Math.round(b)));
            d1[idx + 3] = 255;

            // Bump map (grayscale)
            const bVal = Math.max(0, Math.min(255, Math.round(bump)));
            d2[idx] = d2[idx + 1] = d2[idx + 2] = bVal; d2[idx + 3] = 255;

            // Roughness map (grayscale)
            const rVal = Math.max(0, Math.min(255, Math.round(roughness)));
            d3[idx] = d3[idx + 1] = d3[idx + 2] = rVal; d3[idx + 3] = 255;
        }
    }

    ctx1.putImageData(img1, 0, 0);
    ctx2.putImageData(img2, 0, 0);
    ctx3.putImageData(img3, 0, 0);

    const t1 = new THREE.CanvasTexture(c1);
    const t2 = new THREE.CanvasTexture(c2);
    const t3 = new THREE.CanvasTexture(c3);

    t1.colorSpace = THREE.SRGBColorSpace;
    // Bump and Roughness should be linear

    [t1, t2, t3].forEach(t => {
        t.wrapS = THREE.ClampToEdgeWrapping;
        t.wrapT = THREE.ClampToEdgeWrapping;
        t.needsUpdate = true;
    });

    return { map: t1, bumpMap: t2, roughnessMap: t3 };
}

// ═══════════════════════════════════════════
// Per-Planet Texture Generators
// Higher resolution + Bump/Roughness outputs
// ═══════════════════════════════════════════

function mercuryTexture() {
    return generatePBRTextures(1024, 512, (u, v) => {
        const n = fbm(u * 12 + 1.3, v * 6 + 0.7, 7);
        const craterNoise = fbm(u * 30, v * 15, 5);
        const craters = Math.max(0, 1 - Math.abs(craterNoise - 0.5) * 5);

        // High-frequency detail
        const detail = fbm(u * 50, v * 25, 4) * 0.1;

        const base = 95 + n * 70;
        const r = base + craters * 15 + detail * 50;
        const g = base - 5 + craters * 10 + detail * 50;
        const b = base - 15 + detail * 50;

        const height = n * 0.5 - craters * 0.2 + detail;
        return {
            color: [r, g, b],
            bump: height * 255,
            roughness: 200 + n * 30 + craters * 50 // Very rough globally
        };
    });
}

function venusTexture() {
    return generatePBRTextures(1024, 512, (u, v) => {
        const n1 = fbm(u * 8 + 2.1, v * 4 + 1.5, 6);
        const n2 = fbm(u * 16 + n1 * 2, v * 8 + n1, 5);
        const swirl = n1 * 0.6 + n2 * 0.4;

        const detail = fbm(u * 30, v * 15, 4) * 0.15;
        const val = swirl + detail;

        const r = 210 + val * 40;
        const g = 170 + val * 35;
        const b = 90 + val * 20;

        return {
            color: [r, g, b],
            bump: val * 128 + 128, // Soft clouds, subtle bump
            roughness: 180 - val * 60 // Swirls are slightly smoother
        };
    });
}

function earthTexture() {
    return generatePBRTextures(2048, 1024, (u, v) => { // 2K Resolution
        const lat = Math.abs(v - 0.5) * 2;

        const continental = fbm(u * 6 + 0.5, v * 3 + 0.2, 7);
        const detail = fbm(u * 25 + 3.1, v * 12 + 2.7, 6) * 0.4;
        const micro = fbm(u * 100, v * 50, 4) * 0.1;
        const elevation = continental + detail + micro;

        const isOcean = elevation < 0.52;
        const isShallowOcean = elevation >= 0.49 && elevation < 0.52;

        let r, g, b, bump, roughness;

        if (lat > 0.88) {
            // Polar ice
            const iceBlend = (lat - 0.88) / 0.12;
            const iceNoise = fbm(u * 20, v * 10, 5) * 0.2;
            r = lerp(210, 250, iceBlend + iceNoise);
            g = lerp(220, 255, iceBlend + iceNoise);
            b = lerp(230, 255, iceBlend + iceNoise);
            bump = 140 + iceNoise * 100;
            roughness = 120 + iceNoise * 50; // Ice is somewhat shiny
        } else if (isOcean) {
            const depth = (0.52 - elevation) / 0.25;
            if (isShallowOcean) {
                r = 30; g = 120; b = 160;
            } else {
                r = lerp(10, 5, depth);
                g = lerp(60, 20, depth);
                b = lerp(140, 70, depth);
            }
            bump = 100 + micro * 20; // Ocean very flat
            roughness = 30 + micro * 40; // Very shiny (water)
        } else {
            const landHeight = (elevation - 0.52) / 0.48;
            if (lat > 0.7) {
                [r, g, b] = lerpColor(110, 130, 100, 160, 160, 140, landHeight);
            } else if (lat > 0.35) {
                [r, g, b] = lerpColor(35, 90, 25, 80, 110, 45, landHeight);
            } else if (lat > 0.15) {
                [r, g, b] = lerpColor(70, 120, 50, 180, 150, 80, landHeight);
            } else {
                const desertNoise = fbm(u * 10 + 5, v * 5, 5);
                if (desertNoise > 0.52) {
                    [r, g, b] = lerpColor(190, 165, 110, 210, 185, 130, landHeight);
                } else {
                    [r, g, b] = lerpColor(20, 80, 15, 50, 110, 30, landHeight);
                }
            }

            if (landHeight > 0.65) {
                const mt = (landHeight - 0.65) / 0.35;
                r = lerp(r, 180, mt); g = lerp(g, 175, mt); b = lerp(b, 160, mt);
            }

            bump = 128 + landHeight * 127; // High bump for land/mountains
            roughness = 200 + landHeight * 50; // Very rough for land
        }

        return { color: [r, g, b], bump, roughness };
    });
}

function earthCloudsTexture() {
    // Simple single map for clouds (no PBR needed for the cloud shell, just alpha)
    const c = document.createElement('canvas'); c.width = 2048; c.height = 1024;
    const ctx = c.getContext('2d');
    const img = ctx.createImageData(2048, 1024);
    const d = img.data;

    for (let y = 0; y < 1024; y++) {
        for (let x = 0; x < 2048; x++) {
            const u = x / 2048, v = y / 1024;
            const n1 = fbm(u * 8 + 1.0, v * 4 + 0.5, 6);
            const n2 = fbm(u * 15 + 3.0, v * 8 + 2.0, 5);
            const cloud = Math.max(0, (n1 * 0.7 + n2 * 0.3) - 0.35) * 3.0; // Puffy clouds

            const idx = (y * 2048 + x) * 4;
            const val = Math.min(255, cloud * 255);
            d[idx] = d[idx + 1] = d[idx + 2] = 255;
            d[idx + 3] = val; // Store in alpha
        }
    }
    ctx.putImageData(img, 0, 0);
    const tex = new THREE.CanvasTexture(c);
    tex.wrapS = THREE.ClampToEdgeWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.needsUpdate = true;
    return tex;
}

function marsTexture() {
    return generatePBRTextures(1024, 512, (u, v) => {
        const lat = Math.abs(v - 0.5) * 2;
        const n = fbm(u * 9 + 0.8, v * 5 + 1.2, 7);
        const detail = fbm(u * 30 + 4, v * 15 + 3, 5) * 0.3;
        const micro = fbm(u * 80, v * 40, 3) * 0.1;
        const elev = n + detail + micro;

        let r = 180 + elev * 50, g = 85 + elev * 35, b = 45 + elev * 20;

        if (elev < 0.45) { // Mare
            r -= 50; g -= 25; b -= 10;
        }

        let roughness = 220 + elev * 35; // Mars is very dusty/rough

        if (lat > 0.90) { // Ice caps
            const ice = (lat - 0.90) / 0.10;
            r = lerp(r, 240, ice); g = lerp(g, 235, ice); b = lerp(b, 230, ice);
            roughness = lerp(roughness, 150, ice); // Smoother ice
        }

        return {
            color: [r, g, b],
            bump: elev * 255,
            roughness
        };
    });
}

function jupiterTexture() {
    return generatePBRTextures(1024, 512, (u, v) => {
        const bandY = v * 20;
        const band = Math.sin(bandY * Math.PI) * 0.5 + 0.5;
        const turbulence = fbm(u * 12 + band * 0.8, v * 3 + 0.3, 6) * 0.3;
        const micro = fbm(u * 40, v * 10, 4) * 0.1;
        const bandVal = band + turbulence + micro;

        const spotDist = Math.sqrt((u - 0.6) ** 2 * 3.5 + (v - 0.68) ** 2 * 18);
        const isSpot = spotDist < 0.10;

        let r, g, b;
        if (isSpot) {
            const spotN = fbm(u * 40, v * 20, 5);
            r = 200 + spotN * 30; g = 90 + spotN * 20; b = 60 + spotN * 15;
        } else {
            [r, g, b] = lerpColor(210, 180, 130, 170, 115, 70, bandVal);
            if (bandVal > 0.75) { r += 30; g += 30; b += 25; }
        }

        return {
            color: [r, g, b],
            bump: bandVal * 60 + 100, // Very soft bump for gas giant bands
            roughness: 140 - bandVal * 40 // Slightly glossy gas
        };
    });
}

function saturnTexture() {
    return generatePBRTextures(1024, 512, (u, v) => {
        const bandY = v * 15;
        const band = Math.sin(bandY * Math.PI) * 0.5 + 0.5;
        const turb = fbm(u * 10 + 1.5, v * 2 + 0.8, 5) * 0.2;
        const val = band + turb;

        const [r, g, b] = lerpColor(230, 210, 160, 200, 175, 120, val);

        return {
            color: [r + 5, g, b - 5],
            bump: val * 40 + 128,
            roughness: 150 - val * 30
        };
    });
}

function uranusTexture() {
    return generatePBRTextures(1024, 512, (u, v) => {
        const n = fbm(u * 8 + 2.0, v * 6 + 1.0, 5);
        const band = Math.sin(v * 10 * Math.PI) * 0.05;
        const r = 150 + n * 40 + band * 25;
        const g = 210 + n * 30 + band * 20;
        const b = 230 + n * 25;
        return {
            color: [r, g, b],
            bump: n * 30 + 128,
            roughness: 120 // Smooth icy gas
        };
    });
}

function neptuneTexture() {
    return generatePBRTextures(1024, 512, (u, v) => {
        const n = fbm(u * 10 + 3.0, v * 5 + 2.0, 6);
        const storm = fbm(u * 25 + 1, v * 15 + 3, 5);

        let r = 50 + n * 40, g = 80 + n * 50, b = 190 + n * 50;

        const spotDist = Math.sqrt((u - 0.35) ** 2 * 3 + (v - 0.4) ** 2 * 12);
        if (spotDist < 0.08) { r -= 25; g -= 20; b -= 15; }

        if (storm > 0.75) { r += 40; g += 45; b += 35; }

        return {
            color: [r, g, b],
            bump: n * 60 + storm * 40 + 100,
            roughness: 110 // Glossy ice giant
        };
    });
}

// ── Texture Cache ──
const textureCache = {};

export function getPlanetMap(name) {
    if (textureCache[name]) return textureCache[name];

    const generators = {
        Mercury: mercuryTexture, Venus: venusTexture, Earth: earthTexture, Mars: marsTexture,
        Jupiter: jupiterTexture, Saturn: saturnTexture, Uranus: uranusTexture, Neptune: neptuneTexture,
    };

    if (generators[name]) {
        textureCache[name] = generators[name]();
        return textureCache[name];
    }
    return null;
}

export function getCloudTexture() {
    if (textureCache['_clouds']) return textureCache['_clouds'];
    textureCache['_clouds'] = earthCloudsTexture();
    return textureCache['_clouds'];
}

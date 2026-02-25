// ═══════════════════════════════════════════════════════════════
// ExoLens — Planet Fragment Shader (Phase 3 Overhaul)
// ═══════════════════════════════════════════════════════════════
// Realistic planet rendering with:
//   - Multi-band temperature color palette
//   - Domain-warped FBM for surface features
//   - Rayleigh/Mie atmospheric scattering approximation
//   - Subsurface lava glow for hot worlds
//   - Polar ice with gradient falloff
//   - Proper diffuse + specular lighting
// ═══════════════════════════════════════════════════════════════

uniform float u_time;
uniform float u_temperature;
uniform float u_mass;
uniform float u_radius;

varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;
varying vec3 vWorldNormal;
varying float vDisplacement;
varying float vElevation;

// ── Noise (shared with vertex) ──
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 10.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
    i.z + vec4(0.0, i1.z, i2.z, 1.0))
  + i.y + vec4(0.0, i1.y, i2.y, 1.0))
  + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3  ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}

float fbm(vec3 p, int octaves) {
  float value = 0.0;
  float amplitude = 0.5;
  float frequency = 1.0;
  for (int i = 0; i < 8; i++) {
    if (i >= octaves) break;
    value += amplitude * snoise(p * frequency);
    frequency *= 2.2;
    amplitude *= 0.45;
  }
  return value;
}

// ── Temperature → Color Palette ──
// 7-stop gradient for realistic planetary appearances
vec3 temperatureColor(float t, float noise) {
  // Deep ice
  vec3 frozen   = vec3(0.55, 0.72, 0.95);
  // Cool blue-gray
  vec3 cold     = vec3(0.25, 0.42, 0.65);
  // Temperate teal
  vec3 cool     = vec3(0.12, 0.55, 0.52);
  // Earth-like green/brown
  vec3 temperate = mix(
    vec3(0.18, 0.52, 0.22),  // Land green
    vec3(0.45, 0.35, 0.20),  // Terrain brown
    smoothstep(-0.1, 0.3, noise)  // Noise drives land/water boundary
  );
  // Warm amber
  vec3 warm     = vec3(0.85, 0.55, 0.15);
  // Hot orange-red
  vec3 hot      = vec3(0.92, 0.28, 0.08);
  // Extreme magma
  vec3 extreme  = vec3(0.95, 0.12, 0.05);

  vec3 color = frozen;
  color = mix(color, cold,      smoothstep(0.0,  0.12, t));
  color = mix(color, cool,      smoothstep(0.12, 0.22, t));
  color = mix(color, temperate, smoothstep(0.22, 0.38, t));
  color = mix(color, warm,      smoothstep(0.38, 0.55, t));
  color = mix(color, hot,       smoothstep(0.55, 0.75, t));
  color = mix(color, extreme,   smoothstep(0.75, 1.0,  t));

  return color;
}

// ── Atmospheric Scattering Approximation ──
// Rayleigh: short wavelengths (blue) scatter more at the limb
// Mie: forward scattering creates a bright halo near the star
vec3 atmosphericScattering(vec3 viewDir, vec3 normal, vec3 lightDir, float tempNorm) {
  // Fresnel term: how much we see the atmosphere at the edge
  float fresnel = 1.0 - max(dot(viewDir, normal), 0.0);
  fresnel = pow(fresnel, 2.5);

  // Rayleigh scattering color (blue for cold, shifted for hot)
  vec3 rayleighColor = mix(
    vec3(0.15, 0.35, 0.95),  // Earth-like blue scattering
    vec3(0.95, 0.45, 0.15),  // Hot orange haze
    smoothstep(0.3, 0.8, tempNorm)
  );

  // Mie scattering: forward scatter near the light source
  float miePhase = max(dot(viewDir, -lightDir), 0.0);
  miePhase = pow(miePhase, 8.0) * 0.3;

  // Combine Rayleigh limb glow + Mie forward scatter
  float atmosphereThickness = 0.4 + (1.0 - tempNorm) * 0.4;  // Cold = thicker atmo
  vec3 atmosphere = rayleighColor * fresnel * atmosphereThickness;
  atmosphere += rayleighColor * miePhase * 0.5;

  return atmosphere;
}

void main() {
  float tempNorm = clamp(u_temperature / 3000.0, 0.0, 1.0);

  // ── Surface Noise ──
  vec3 noiseCoord = vPosition * 2.5 + vec3(0.0, 0.0, u_time * 0.02);
  float surfaceNoise = fbm(noiseCoord, 6);
  float detailNoise = snoise(vPosition * 10.0 + u_time * 0.05) * 0.15;

  // ── Base Color ──
  vec3 baseColor = temperatureColor(tempNorm, surfaceNoise);

  // ── Surface Modulation ──
  float modulation = 0.2 + clamp(u_mass, 0.0, 1.0) * 0.3;
  vec3 surfaceColor = baseColor * (1.0 + (surfaceNoise + detailNoise) * modulation);

  // ── Gas Giant Bands (for high-mass planets) ──
  if (u_mass > 0.1) {
    float bandFreq = 6.0 + u_mass * 4.0;
    float bands = sin(vWorldNormal.y * bandFreq + surfaceNoise * 3.0 + u_time * 0.03);
    bands = bands * 0.5 + 0.5;
    vec3 bandColor = mix(baseColor * 0.7, baseColor * 1.3, bands);
    float bandStrength = smoothstep(0.1, 0.5, u_mass);
    surfaceColor = mix(surfaceColor, bandColor, bandStrength * 0.5);
  }

  // ── Lava Cracks (hot planets) ──
  if (tempNorm > 0.55) {
    float crackNoise = snoise(vPosition * 12.0 + u_time * 0.08);
    float crack = smoothstep(0.25, 0.55, crackNoise);
    float crackIntensity = (tempNorm - 0.55) * 2.2;
    vec3 lavaGlow = vec3(1.0, 0.35, 0.02) * crack * crackIntensity;
    // Subsurface glow: lava light bleeds through surface
    float subsurface = smoothstep(0.15, 0.45, crackNoise) * crackIntensity * 0.3;
    surfaceColor += lavaGlow + vec3(0.8, 0.2, 0.0) * subsurface;
  }

  // ── Polar Ice (cold planets) ──
  if (tempNorm < 0.3) {
    float polar = abs(vWorldNormal.y);
    float iceNoise = snoise(vPosition * 5.0) * 0.15;
    float iceCap = smoothstep(0.5, 0.85, polar + iceNoise);
    vec3 iceColor = mix(vec3(0.75, 0.88, 1.0), vec3(0.95, 0.97, 1.0), polar);
    float iceStrength = (1.0 - tempNorm / 0.3) * 0.85;
    surfaceColor = mix(surfaceColor, iceColor, iceCap * iceStrength);
  }

  // ── Lighting ──
  vec3 lightDir = normalize(vec3(5.0, 3.0, 5.0));
  vec3 viewDir = normalize(cameraPosition - vPosition);
  vec3 halfDir = normalize(lightDir + viewDir);

  // Diffuse (Lambert)
  float diffuse = max(dot(vNormal, lightDir), 0.0);
  // Wrap lighting for softer terminator
  float wrapDiffuse = (diffuse + 0.2) / 1.2;

  // Specular (Blinn-Phong) — subtle for rocky, strong for icy
  float specPower = mix(32.0, 128.0, smoothstep(0.0, 0.25, 1.0 - tempNorm));
  float specular = pow(max(dot(vNormal, halfDir), 0.0), specPower);
  float specIntensity = mix(0.05, 0.3, smoothstep(0.0, 0.25, 1.0 - tempNorm));

  // Ambient (darker for space realism)
  float ambient = 0.06;

  surfaceColor *= (ambient + wrapDiffuse * 0.9);
  surfaceColor += vec3(1.0, 0.95, 0.9) * specular * specIntensity;

  // ── Atmospheric Scattering ──
  vec3 atmosphere = atmosphericScattering(viewDir, vNormal, lightDir, tempNorm);
  surfaceColor += atmosphere;

  // ── Night Side City Lights (Earth-like temperate planets) ──
  if (tempNorm > 0.2 && tempNorm < 0.4 && u_mass < 0.01) {
    float nightSide = 1.0 - smoothstep(-0.1, 0.2, dot(vNormal, lightDir));
    float cityNoise = snoise(vPosition * 30.0);
    float cities = smoothstep(0.6, 0.8, cityNoise) * nightSide;
    surfaceColor += vec3(1.0, 0.85, 0.4) * cities * 0.15;
  }

  gl_FragColor = vec4(surfaceColor, 1.0);
}

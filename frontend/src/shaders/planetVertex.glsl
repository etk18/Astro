// ═══════════════════════════════════════════════════════════════
// ExoLens — Planet Vertex Shader (Phase 3 Overhaul)
// ═══════════════════════════════════════════════════════════════
// Multi-layered FBM noise for realistic terrain displacement.
// Domain warping creates organic continent-like features.
// Mass controls roughness; time animates tectonic drift.
// ═══════════════════════════════════════════════════════════════

uniform float u_time;
uniform float u_mass;
uniform float u_temperature;

varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vPosition;
varying vec3 vWorldNormal;
varying float vDisplacement;
varying float vElevation;

// ── Simplex 3D Noise ──
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

// ── Multi-layered FBM with domain warping ──
// Layer 1: large continental shapes (low freq)
// Layer 2: mid-scale terrain features
// Layer 3: fine surface detail
// Domain warping feeds noise output back as input offset,
// creating realistic organic swirl patterns.
float fbm(vec3 p, int octaves) {
  float value = 0.0;
  float amplitude = 0.5;
  float frequency = 1.0;
  for (int i = 0; i < 8; i++) {
    if (i >= octaves) break;
    value += amplitude * snoise(p * frequency);
    frequency *= 2.2;   // Slightly > 2 for richer detail
    amplitude *= 0.45;  // Steeper falloff for cleaner shapes
  }
  return value;
}

float domainWarpedFBM(vec3 p) {
  // First pass: large-scale warping
  vec3 q = vec3(
    fbm(p + vec3(0.0, 0.0, 0.0), 4),
    fbm(p + vec3(5.2, 1.3, 2.8), 4),
    fbm(p + vec3(1.7, 9.2, 3.4), 4)
  );
  // Second pass: warp by first result for organic shapes
  vec3 r = vec3(
    fbm(p + 4.0 * q + vec3(1.7, 9.2, 0.0), 6),
    fbm(p + 4.0 * q + vec3(8.3, 2.8, 0.0), 6),
    fbm(p + 4.0 * q + vec3(3.1, 5.7, 0.0), 6)
  );
  return fbm(p + 3.0 * r, 6);
}

void main() {
  vUv = uv;
  vNormal = normalize(normalMatrix * normal);
  vWorldNormal = normalize((modelMatrix * vec4(normal, 0.0)).xyz);

  // ── Terrain Displacement ──
  // Slow tectonic drift via time animation
  vec3 noisePos = position * 1.8 + vec3(u_time * 0.015, u_time * 0.01, u_time * 0.02);

  // Domain-warped FBM for continent-like features
  float noise = domainWarpedFBM(noisePos);

  // Displacement strength proportional to mass
  // Rocky planets (low mass) get subtle terrain
  // Gas giants (high mass) get dramatic atmospheric bands
  float displacementStrength = 0.01 + clamp(u_mass, 0.0, 1.0) * 0.08;
  vec3 displaced = position + normal * noise * displacementStrength;

  vDisplacement = noise;
  vElevation = noise * displacementStrength;
  vPosition = (modelMatrix * vec4(displaced, 1.0)).xyz;

  gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
}

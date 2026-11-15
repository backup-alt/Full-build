(function () {
  'use strict';

const stage = document.getElementById('stage');
const canvas = document.getElementById('scene');
const fallback = document.getElementById('stageFallback');
const statusHud = document.getElementById('trackStatus');
const statusText = document.getElementById('statusText');
const gazeReadout = document.getElementById('gazeReadout');
const bubble = document.getElementById('greetBubble');
const bubbleText = document.getElementById('bubbleText');
const cursorOrb = document.getElementById('cursorOrb');

const reduceMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
let reducedMotion = reduceMotionQuery.matches;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

function smoothstep(edge0, edge1, value) {
  const t = clamp((value - edge0) / (edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

function formatDegrees(value) {
  const rounded = Math.round(value);
  return `${rounded >= 0 ? '+' : '\u2212'}${Math.abs(rounded).toString().padStart(2, '0')}\u00b0`;
}

function showFallback(error) {
  if (error) console.error('Sentinel failed to start:', error);
  stage.classList.add('is-fallback', 'is-ready');
  fallback.hidden = false;
  statusText.textContent = 'Offline';
  gazeReadout.textContent = 'Gaze vector unavailable';
}

function makeEnvironmentTexture() {
  const textureCanvas = document.createElement('canvas');
  textureCanvas.width = 1024;
  textureCanvas.height = 512;
  const context = textureCanvas.getContext('2d');

  const base = context.createLinearGradient(0, 0, 0, 512);
  base.addColorStop(0, '#16263c');
  base.addColorStop(0.38, '#0a1220');
  base.addColorStop(0.7, '#060a12');
  base.addColorStop(1, '#160c20');
  context.fillStyle = base;
  context.fillRect(0, 0, 1024, 512);

  const blob = (x, y, radius, color) => {
    const gradient = context.createRadialGradient(x, y, 0, x, y, radius);
    gradient.addColorStop(0, color);
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    context.fillStyle = gradient;
    context.fillRect(x - radius, y - radius, radius * 2, radius * 2);
  };

  blob(178, 132, 210, 'rgba(112, 240, 255, 0.95)');
  blob(790, 176, 250, 'rgba(255, 70, 191, 0.82)');
  blob(510, 28, 180, 'rgba(255, 255, 255, 0.92)');
  blob(538, 330, 290, 'rgba(36, 94, 153, 0.48)');
  blob(110, 410, 180, 'rgba(255, 150, 214, 0.2)');

  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.mapping = THREE.EquirectangularReflectionMapping;
  return texture;
}

function makeGlowTexture() {
  const textureCanvas = document.createElement('canvas');
  textureCanvas.width = 128;
  textureCanvas.height = 128;
  const context = textureCanvas.getContext('2d');
  const gradient = context.createRadialGradient(64, 64, 0, 64, 64, 64);
  gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
  gradient.addColorStop(0.24, 'rgba(255, 255, 255, 0.72)');
  gradient.addColorStop(0.52, 'rgba(255, 255, 255, 0.16)');
  gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
  context.fillStyle = gradient;
  context.fillRect(0, 0, 128, 128);
  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}


function makeDecalTexture(label) {
  const textureCanvas = document.createElement('canvas');
  textureCanvas.width = 256;
  textureCanvas.height = 128;
  const context = textureCanvas.getContext('2d');
  context.clearRect(0, 0, 256, 128);
  context.font = '700 82px "JetBrains Mono", monospace';
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillStyle = '#9df8ff';
  context.fillText(label, 128, 58);
  context.fillStyle = 'rgba(157, 248, 255, 0.55)';
  context.fillRect(58, 105, 140, 3);
  const texture = new THREE.CanvasTexture(textureCanvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  return texture;
}

function addMesh(parent, geometry, material, position, rotation, scale) {
  const mesh = new THREE.Mesh(geometry, material);
  if (position) mesh.position.set(position[0], position[1], position[2]);
  if (rotation) mesh.rotation.set(rotation[0], rotation[1], rotation[2]);
  if (scale) mesh.scale.set(scale[0], scale[1], scale[2]);
  parent.add(mesh);
  return mesh;
}

function addGlow(parent, texture, color, scale, position, opacity) {
  const material = new THREE.SpriteMaterial({
    map: texture,
    color,
    transparent: true,
    opacity,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false
  });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(scale, scale, 1);
  sprite.position.set(position[0], position[1], position[2]);
  parent.add(sprite);
  return sprite;
}

function dashedCircle(radius, segments, material) {
  const vertices = [];
  for (let i = 0; i < segments; i += 1) {
    if (i % 3 === 0) continue;
    const start = (i / segments) * Math.PI * 2;
    const end = ((i + 1) / segments) * Math.PI * 2;
    vertices.push(Math.cos(start) * radius, Math.sin(start) * radius, 0);
    vertices.push(Math.cos(end) * radius, Math.sin(end) * radius, 0);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  return new THREE.LineSegments(geometry, material);
}

function boot() {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance'
  });

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(33, 1, 0.1, 80);
  camera.position.set(0, 1.1, 7.5);
  camera.lookAt(0, 0.55, 0);

  const environment = makeEnvironmentTexture();
  const glowTexture = makeGlowTexture();
  scene.environment = environment;

  scene.add(new THREE.HemisphereLight(0x98ecff, 0x1a0a29, 0.95));

  const keyLight = new THREE.DirectionalLight(0xfff6ef, 2.9);
  keyLight.position.set(3.6, 5.4, 4.6);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(1024, 1024);
  keyLight.shadow.camera.near = 0.5;
  keyLight.shadow.camera.far = 14;
  keyLight.shadow.camera.left = -3.4;
  keyLight.shadow.camera.right = 3.4;
  keyLight.shadow.camera.top = 4.4;
  keyLight.shadow.camera.bottom = -3.2;
  keyLight.shadow.bias = -0.0004;
  keyLight.shadow.normalBias = 0.025;
  scene.add(keyLight);
  scene.add(keyLight.target);
  keyLight.target.position.set(0, 0.2, 0);

  const rimLight = new THREE.DirectionalLight(0xff4fc8, 3.4);
  rimLight.position.set(-4.4, 2.2, -2.7);
  scene.add(rimLight);

  const fillLight = new THREE.DirectionalLight(0x45d9ff, 2.3);
  fillLight.position.set(4.3, 1.4, 2.6);
  scene.add(fillLight);

  const topLight = new THREE.PointLight(0x8ff8ff, 16, 6, 2);
  topLight.position.set(0, 2.8, 1.4);
  scene.add(topLight);

  const backLight = new THREE.PointLight(0xff4fc8, 14, 6, 2);
  backLight.position.set(-1.5, 1.8, -1.4);
  scene.add(backLight);

  const shellMaterial = new THREE.MeshStandardMaterial({
    color: 0xd9e3ec,
    metalness: 0.68,
    roughness: 0.26,
    envMapIntensity: 1.3
  });

  const brightShellMaterial = new THREE.MeshStandardMaterial({
    color: 0xf2f7fb,
    metalness: 0.32,
    roughness: 0.36,
    envMapIntensity: 1.05
  });

  const suitMaterial = new THREE.MeshStandardMaterial({
    color: 0x1a2938,
    metalness: 0.48,
    roughness: 0.48,
    envMapIntensity: 0.9
  });

  const darkMaterial = new THREE.MeshStandardMaterial({
    color: 0x0a121c,
    metalness: 0.86,
    roughness: 0.27,
    envMapIntensity: 1.2
  });

  const visorMaterial = new THREE.MeshPhysicalMaterial({
    color: 0x03080f,
    metalness: 0.9,
    roughness: 0.055,
    clearcoat: 1,
    clearcoatRoughness: 0.06,
    envMapIntensity: 2.5
  });

  const cyanMaterial = new THREE.MeshStandardMaterial({
    color: 0x0b2a33,
    emissive: 0x4fe8ff,
    emissiveIntensity: 3.4,
    metalness: 0.42,
    roughness: 0.28
  });

  const magentaMaterial = new THREE.MeshStandardMaterial({
    color: 0x2b0a22,
    emissive: 0xff4fc8,
    emissiveIntensity: 2.6,
    metalness: 0.4,
    roughness: 0.3
  });

  const coreMaterial = new THREE.MeshStandardMaterial({
    color: 0x0b2a33,
    emissive: 0x60f4ff,
    emissiveIntensity: 3.4,
    metalness: 0.35,
    roughness: 0.22
  });

  const eyeMaterial = new THREE.MeshBasicMaterial({
    color: 0xdcfeff,
    toneMapped: false
  });

  const decalTexture = makeDecalTexture('01');
  const decalMaterial = new THREE.MeshBasicMaterial({
    map: decalTexture,
    transparent: true,
    opacity: 0.92,
    depthWrite: false,
    toneMapped: false
  });

  const lineCyanMaterial = new THREE.LineBasicMaterial({
    color: 0x83f5ff,
    transparent: true,
    opacity: 0.2,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false
  });

  const haloMaterial = new THREE.MeshBasicMaterial({
    color: 0x99f8ff,
    transparent: true,
    opacity: 0.34,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false
  });

  const haloMagentaMaterial = new THREE.MeshBasicMaterial({
    color: 0xff74d6,
    transparent: true,
    opacity: 0.22,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false
  });

  const rig = new THREE.Group();
  scene.add(rig);

  const figure = new THREE.Group();
  rig.add(figure);

  const body = new THREE.Group();
  figure.add(body);

  addMesh(body, new THREE.CapsuleGeometry(0.23, 0.22, 8, 22), suitMaterial, [0, -0.17, 0], [0, 0, Math.PI / 2], [1, 1, 0.84]);
  addMesh(body, new THREE.CylinderGeometry(0.32, 0.34, 0.075, 30), darkMaterial, [0, -0.035, 0], null, [1.08, 1, 0.78]);
  addMesh(body, new THREE.BoxGeometry(0.12, 0.055, 0.035), cyanMaterial, [0, -0.035, 0.245]);

  addMesh(body, new THREE.CapsuleGeometry(0.31, 0.38, 12, 28), suitMaterial, [0, 0.47, 0], null, [1.2, 1, 0.8]);
  addMesh(body, new THREE.SphereGeometry(0.38, 34, 26), shellMaterial, [0, 0.61, 0.1], null, [1.16, 1.14, 0.62]);
  addMesh(body, new THREE.SphereGeometry(0.3, 28, 22), brightShellMaterial, [0, 0.28, 0.12], null, [1.04, 0.58, 0.58]);

  addMesh(body, new THREE.TorusGeometry(0.135, 0.017, 12, 48), darkMaterial, [0, 0.66, 0.345]);
  addMesh(body, new THREE.TorusGeometry(0.108, 0.012, 10, 40), cyanMaterial, [0, 0.66, 0.352]);
  addMesh(body, new THREE.SphereGeometry(0.066, 22, 18), coreMaterial, [0, 0.66, 0.36]);
  addGlow(body, glowTexture, 0x54efff, 0.82, [0, 0.66, 0.42], 0.58);

  for (let i = 0; i < 3; i += 1) {
    addMesh(body, new THREE.BoxGeometry(0.075, 0.011, 0.018), i === 1 ? magentaMaterial : darkMaterial, [-0.2, 0.32 + i * 0.048, 0.337]);
  }

  addMesh(body, new THREE.BoxGeometry(0.028, 0.16, 0.014), cyanMaterial, [0.24, 0.56, 0.34]);
  addMesh(body, new THREE.SphereGeometry(0.032, 12, 10), magentaMaterial, [0.24, 0.455, 0.342]);
  addMesh(body, new THREE.PlaneGeometry(0.155, 0.078), decalMaterial, [0.205, 0.805, 0.301]);
  addMesh(body, new THREE.BoxGeometry(0.013, 0.23, 0.012), darkMaterial, [-0.26, 0.54, 0.286], [0, -0.24, 0.18]);
  addMesh(body, new THREE.BoxGeometry(0.013, 0.23, 0.012), darkMaterial, [0.26, 0.54, 0.286], [0, 0.24, -0.18]);

  for (let i = 0; i < 4; i += 1) {
    const angle = Math.PI / 4 + i * Math.PI / 2;
    addMesh(
      body,
      new THREE.CylinderGeometry(0.013, 0.013, 0.012, 10),
      i % 2 === 0 ? darkMaterial : cyanMaterial,
      [Math.cos(angle) * 0.212, 0.66 + Math.sin(angle) * 0.212, 0.325],
      [Math.PI / 2, 0, 0]
    );
  }

  addMesh(body, new THREE.BoxGeometry(0.46, 0.56, 0.18), darkMaterial, [0, 0.64, -0.31], null, [1, 1, 1]);
  addMesh(body, new THREE.BoxGeometry(0.34, 0.06, 0.025), shellMaterial, [0, 0.87, -0.405]);
  addMesh(body, new THREE.BoxGeometry(0.3, 0.035, 0.02), cyanMaterial, [0, 0.79, -0.407]);

  for (const side of [-1, 1]) {
    addMesh(body, new THREE.CylinderGeometry(0.062, 0.072, 0.32, 18), darkMaterial, [side * 0.16, 0.4, -0.35]);
    addMesh(body, new THREE.CylinderGeometry(0.072, 0.052, 0.055, 18), cyanMaterial, [side * 0.16, 0.222, -0.35]);
    addMesh(body, new THREE.TorusGeometry(0.075, 0.008, 8, 24), magentaMaterial, [side * 0.16, 0.31, -0.35], [Math.PI / 2, 0, 0]);
  }

  addMesh(body, new THREE.CylinderGeometry(0.125, 0.145, 0.19, 22), suitMaterial, [0, 1.11, 0]);
  addMesh(body, new THREE.TorusGeometry(0.142, 0.018, 10, 32), darkMaterial, [0, 1.175, 0], [Math.PI / 2, 0, 0]);
  addMesh(body, new THREE.TorusGeometry(0.154, 0.009, 8, 32), cyanMaterial, [0, 1.07, 0], [Math.PI / 2, 0, 0]);

  for (const side of [-1, 1]) {
    addMesh(body, new THREE.SphereGeometry(0.178, 26, 20), shellMaterial, [side * 0.555, 0.92, 0], null, [0.88, 0.8, 1.04]);
    addMesh(body, new THREE.BoxGeometry(0.08, 0.012, 0.05), side === 1 ? cyanMaterial : magentaMaterial, [side * 0.57, 0.955, 0.145]);
  }

  const head = new THREE.Group();
  head.position.set(0, 1.47, 0);
  body.add(head);

  addMesh(head, new THREE.SphereGeometry(0.41, 48, 36), shellMaterial, null, null, [1.02, 1.07, 0.98]);
  addMesh(
    head,
    new THREE.SphereGeometry(
      0.418,
      48,
      32,
      Math.PI * 0.22,
      Math.PI * 0.56,
      Math.PI * 0.26,
      Math.PI * 0.44
    ),
    visorMaterial
  );
  addMesh(head, new THREE.TorusGeometry(0.414, 0.009, 8, 64, Math.PI * 0.52), darkMaterial, [0, 0.01, 0], [0, 0, Math.PI * 0.24]);

  const eyes = new THREE.Group();
  eyes.position.set(0, 0.025, 0);
  head.add(eyes);

  for (const side of [-1, 1]) {
    addMesh(eyes, new THREE.CapsuleGeometry(0.029, 0.072, 6, 14), eyeMaterial, [side * 0.132, 0.035, 0.404], [0, 0, Math.PI / 2]);
    addGlow(eyes, glowTexture, 0x7df7ff, 0.21, [side * 0.132, 0.035, 0.43], 0.62);
  }

  addMesh(eyes, new THREE.BoxGeometry(0.1, 0.009, 0.012), darkMaterial, [0, -0.112, 0.407]);
  addMesh(eyes, new THREE.BoxGeometry(0.038, 0.008, 0.014), magentaMaterial, [0, -0.162, 0.395]);

  for (const side of [-1, 1]) {
    addMesh(head, new THREE.CylinderGeometry(0.105, 0.105, 0.065, 24), darkMaterial, [side * 0.43, -0.005, -0.005], [0, 0, Math.PI / 2]);
    addMesh(head, new THREE.TorusGeometry(0.084, 0.009, 8, 28), side === 1 ? cyanMaterial : magentaMaterial, [side * 0.466, -0.005, -0.005], [0, Math.PI / 2, 0]);
  }

  const antenna = new THREE.Group();
  antenna.position.set(0.3, 0.33, -0.07);
  antenna.rotation.z = -0.28;
  antenna.rotation.x = -0.06;
  head.add(antenna);
  addMesh(antenna, new THREE.CylinderGeometry(0.008, 0.011, 0.29, 10), darkMaterial, [0, 0.145, 0]);
  addMesh(antenna, new THREE.SphereGeometry(0.026, 14, 12), magentaMaterial, [0, 0.3, 0]);
  addGlow(antenna, glowTexture, 0xff5ccf, 0.2, [0, 0.3, 0], 0.62);

  addMesh(head, new THREE.BoxGeometry(0.045, 0.015, 0.29), cyanMaterial, [0, 0.435, -0.035], [0.2, 0, 0]);

  function buildArm(side) {
    const arm = new THREE.Group();
    arm.position.set(side * 0.565, 0.9, 0);
    arm.rotation.z = side * 0.15;
    arm.rotation.x = 0.02;
    body.add(arm);

    addMesh(arm, new THREE.SphereGeometry(0.135, 24, 18), suitMaterial, [0, 0.005, 0]);
    addMesh(arm, new THREE.CapsuleGeometry(0.093, 0.27, 8, 18), shellMaterial, [0, -0.2, 0]);
    addMesh(arm, new THREE.CylinderGeometry(0.098, 0.092, 0.055, 18), darkMaterial, [0, -0.365, 0]);

    const elbow = new THREE.Group();
    elbow.position.set(0, -0.405, 0);
    elbow.rotation.x = -0.12;
    arm.add(elbow);

    addMesh(elbow, new THREE.SphereGeometry(0.103, 22, 16), suitMaterial);
    addMesh(elbow, new THREE.CapsuleGeometry(0.078, 0.22, 8, 18), shellMaterial, [0, -0.16, 0]);
    addMesh(elbow, new THREE.CylinderGeometry(0.086, 0.08, 0.06, 18), darkMaterial, [0, -0.3, 0]);
    addMesh(elbow, new THREE.SphereGeometry(0.095, 20, 16), darkMaterial, [0, -0.37, 0.01], null, [1, 0.94, 1.16]);
    addMesh(elbow, new THREE.BoxGeometry(0.055, 0.012, 0.03), cyanMaterial, [0, -0.405, 0.095]);

    arm.userData.elbow = elbow;
    arm.userData.baseZ = arm.rotation.z;
    arm.userData.baseX = arm.rotation.x;
    elbow.userData.baseZ = elbow.rotation.z;
    elbow.userData.baseX = elbow.rotation.x;
    return arm;
  }

  function buildLeg(side) {
    const leg = new THREE.Group();
    leg.position.set(side * 0.235, -0.27, 0);
    leg.rotation.z = side * 0.025;
    figure.add(leg);

    addMesh(leg, new THREE.SphereGeometry(0.145, 24, 18), shellMaterial, [0, -0.04, 0], null, [0.9, 0.76, 0.95]);
    addMesh(leg, new THREE.CapsuleGeometry(0.14, 0.32, 8, 20), suitMaterial, [0, -0.28, 0], null, [1, 1, 0.95]);
    addMesh(leg, new THREE.TorusGeometry(0.112, 0.01, 8, 26), cyanMaterial, [0, -0.31, 0], [Math.PI / 2, 0, 0]);

    const knee = new THREE.Group();
    knee.position.set(0, -0.58, 0);
    knee.rotation.x = 0.035;
    leg.add(knee);

    addMesh(knee, new THREE.SphereGeometry(0.132, 22, 18), suitMaterial);
    addMesh(knee, new THREE.SphereGeometry(0.122, 20, 16), shellMaterial, [0, -0.01, 0.045], null, [0.98, 1.02, 0.55]);
    addMesh(knee, new THREE.CapsuleGeometry(0.12, 0.26, 8, 20), shellMaterial, [0, -0.2, 0]);
    addMesh(knee, new THREE.CylinderGeometry(0.1, 0.11, 0.055, 18), darkMaterial, [0, -0.36, 0]);
    addMesh(knee, new THREE.BoxGeometry(0.25, 0.13, 0.36), darkMaterial, [0, -0.49, 0.055]);
    addMesh(knee, new THREE.BoxGeometry(0.26, 0.035, 0.39), darkMaterial, [0, -0.565, 0.055]);
    addMesh(knee, new THREE.BoxGeometry(0.19, 0.055, 0.1), shellMaterial, [0, -0.5, 0.225]);
    addMesh(knee, new THREE.BoxGeometry(0.045, 0.012, 0.16), cyanMaterial, [0, -0.425, 0.11]);

    return leg;
  }

  const armLeft = buildArm(-1);
  const armRight = buildArm(1);
  buildLeg(-1);
  buildLeg(1);

  figure.traverse((object) => {
    if (object.isMesh) {
      object.castShadow = true;
      object.receiveShadow = true;
    }
  });

  const platform = new THREE.Group();
  platform.position.y = -1.47;
  rig.add(platform);

  const platformMaterial = new THREE.MeshStandardMaterial({
    color: 0x111a25,
    metalness: 0.76,
    roughness: 0.44,
    envMapIntensity: 0.9
  });

  addMesh(platform, new THREE.CylinderGeometry(1.5, 1.56, 0.15, 72), darkMaterial, [0, -0.085, 0]);
  const platformTop = addMesh(platform, new THREE.CylinderGeometry(1.42, 1.45, 0.035, 72), platformMaterial, [0, 0.008, 0]);
  platformTop.receiveShadow = true;
  addMesh(platform, new THREE.TorusGeometry(1.405, 0.009, 8, 120), haloMaterial, [0, 0.03, 0], [Math.PI / 2, 0, 0]);
  addMesh(platform, new THREE.TorusGeometry(1.08, 0.006, 6, 100), haloMagentaMaterial, [0, 0.03, 0], [Math.PI / 2, 0, 0]);
  addMesh(platform, new THREE.TorusGeometry(0.78, 0.005, 6, 80), lineCyanMaterial, [0, 0.031, 0], [Math.PI / 2, 0, 0]);

  for (let i = 0; i < 48; i += 1) {
    const angle = (i / 48) * Math.PI * 2;
    const length = i % 6 === 0 ? 0.075 : 0.035;
    addMesh(
      platform,
      new THREE.BoxGeometry(0.009, 0.004, length),
      i % 12 === 0 ? cyanMaterial : darkMaterial,
      [Math.cos(angle) * 1.24, 0.029, Math.sin(angle) * 1.24],
      [0, Math.PI / 2 - angle, 0]
    );
  }

  for (let i = 0; i < 4; i += 1) {
    const angle = (i / 4) * Math.PI * 2 + Math.PI / 4;
    addMesh(
      platform,
      new THREE.BoxGeometry(0.035, 0.012, 0.18),
      i % 2 === 0 ? cyanMaterial : magentaMaterial,
      [Math.cos(angle) * 1.48, 0.035, Math.sin(angle) * 1.48],
      [0, Math.PI / 2 - angle, 0]
    );
  }

  const platformGlow = new THREE.Mesh(
    new THREE.PlaneGeometry(5, 5),
    new THREE.MeshBasicMaterial({
      map: glowTexture,
      color: 0x2bb9e0,
      transparent: true,
      opacity: 0.32,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
      toneMapped: false
    })
  );
  platformGlow.rotation.x = -Math.PI / 2;
  platformGlow.position.y = -1.435;
  rig.add(platformGlow);

  const halo = new THREE.Group();
  halo.position.set(0, 0.46, -0.95);
  rig.add(halo);
  addMesh(halo, new THREE.TorusGeometry(1.96, 0.0055, 8, 220), haloMaterial, null, [0, 0, -0.17]);
  addMesh(halo, new THREE.TorusGeometry(1.74, 0.0045, 8, 200), haloMagentaMaterial, null, [0.13, 0, 0.23]);
  const haloDashes = dashedCircle(2.26, 210, lineCyanMaterial);
  haloDashes.position.z = -0.01;
  halo.add(haloDashes);

  const orbit = new THREE.Mesh(new THREE.TorusGeometry(0.9, 0.004, 6, 130), lineCyanMaterial);
  orbit.position.set(0, 0.5, 0);
  orbit.rotation.set(1.27, 0.16, 0.1);
  rig.add(orbit);

  const shardShellMaterial = new THREE.MeshStandardMaterial({
    color: 0x6e8496,
    metalness: 0.85,
    roughness: 0.3,
    envMapIntensity: 1
  });

  const shards = [];
  for (let i = 0; i < 11; i += 1) {
    const angle = (i / 11) * Math.PI * 2 + 0.35;
    const radius = 1.78 + (i % 4) * 0.24;
    const size = 0.032 + (i % 5) * 0.012;
    const useBox = i % 3 !== 0;
    const geometry = useBox
      ? new THREE.BoxGeometry(size, size * 2.4, size * 0.24)
      : new THREE.OctahedronGeometry(size * 1.1, 0);
    const material = i % 5 === 0 ? cyanMaterial : i % 7 === 0 ? magentaMaterial : shardShellMaterial;
    const shard = new THREE.Mesh(geometry, material);
    shard.position.set(
      Math.cos(angle) * radius,
      -0.8 + ((i * 0.73) % 2.5),
      Math.sin(angle) * radius * 0.52 - 0.38
    );
    shard.rotation.set(angle * 0.7, angle, angle * 0.4);
    rig.add(shard);
    shards.push({
      mesh: shard,
      angle,
      radius,
      baseY: shard.position.y,
      speed: 0.08 + (i % 5) * 0.025,
      phase: i * 0.7
    });
  }

  const particleCount = window.matchMedia('(pointer: fine)').matches ? 440 : 230;
  const particlePositions = new Float32Array(particleCount * 3);
  const particleColors = new Float32Array(particleCount * 3);
  const palette = [
    new THREE.Color(0x8ff9ff),
    new THREE.Color(0xff6ed7),
    new THREE.Color(0xe9f6ff),
    new THREE.Color(0x409fc9)
  ];

  for (let i = 0; i < particleCount; i += 1) {
    particlePositions[i * 3] = (Math.random() - 0.5) * 9;
    particlePositions[i * 3 + 1] = Math.random() * 5.2 - 2;
    particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 7 - 0.4;
    const color = palette[Math.floor(Math.random() * palette.length)];
    const brightness = 0.35 + Math.random() * 0.65;
    particleColors[i * 3] = color.r * brightness;
    particleColors[i * 3 + 1] = color.g * brightness;
    particleColors[i * 3 + 2] = color.b * brightness;
  }

  const particleGeometry = new THREE.BufferGeometry();
  particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
  particleGeometry.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));
  const particles = new THREE.Points(
    particleGeometry,
    new THREE.PointsMaterial({
      size: 0.045,
      map: glowTexture,
      transparent: true,
      opacity: 0.74,
      vertexColors: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true
    })
  );
  scene.add(particles);

  const pointer = {
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
    active: false
  };

  window.addEventListener('pointermove', (event) => {
    const rect = stage.getBoundingClientRect();
    const normalizedX = (event.clientX - (rect.left + rect.width / 2)) / (rect.width / 2);
    const normalizedY = (event.clientY - (rect.top + rect.height / 2)) / (rect.height / 2);
    pointer.targetX = clamp(normalizedX, -1.35, 1.35);
    pointer.targetY = clamp(normalizedY, -1.35, 1.35);
    pointer.active = true;
  }, { passive: true });

  document.addEventListener('pointerleave', () => {
    pointer.targetX = 0;
    pointer.targetY = 0;
    pointer.active = false;
  });

  window.addEventListener('blur', () => {
    pointer.targetX = 0;
    pointer.targetY = 0;
    pointer.active = false;
  });

  window.addEventListener('pointerup', (event) => {
    if (event.pointerType !== 'touch') return;
    pointer.targetX = 0;
    pointer.targetY = 0;
    pointer.active = false;
  });

  window.addEventListener('pointercancel', (event) => {
    if (event.pointerType !== 'touch') return;
    pointer.targetX = 0;
    pointer.targetY = 0;
    pointer.active = false;
  });

  const stagePointer = {
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
    visible: false,
    initialized: false
  };

  stage.addEventListener('pointermove', (event) => {
    const rect = stage.getBoundingClientRect();
    stagePointer.targetX = event.clientX - rect.left;
    stagePointer.targetY = event.clientY - rect.top;
    stagePointer.visible = event.pointerType !== 'touch';
    if (!stagePointer.initialized) {
      stagePointer.x = stagePointer.targetX;
      stagePointer.y = stagePointer.targetY;
      stagePointer.initialized = true;
    }
    if (stagePointer.visible) stage.classList.add('orb-active');
    stage.classList.add('is-engaged');
  }, { passive: true });

  stage.addEventListener('pointerleave', () => {
    stagePointer.visible = false;
    stage.classList.remove('orb-active');
  });

  let greetStartedAt = -100;
  let bubbleTimer = 0;
  let greetCount = 0;
  const greetMessages = [
    'Hello, operator. I see you.',
    'Gaze locked. Good to meet you.',
    'Right back at you, operator.',
    'Signal received. I am listening.'
  ];

  function greet() {
    const now = performance.now() / 1000;
    if (now - greetStartedAt < 0.8) return;
    greetStartedAt = now;
    greetCount += 1;
    bubbleText.textContent = greetMessages[(greetCount - 1) % greetMessages.length];
    bubble.classList.add('is-visible');
    bubble.setAttribute('aria-hidden', 'false');
    stage.classList.add('is-greeting', 'orb-click');
    window.clearTimeout(bubbleTimer);
    bubbleTimer = window.setTimeout(() => {
      bubble.classList.remove('is-visible');
      bubble.setAttribute('aria-hidden', 'true');
      stage.classList.remove('is-greeting');
    }, 3900);
    window.setTimeout(() => stage.classList.remove('orb-click'), 280);
  }

  document.querySelectorAll('.js-greet').forEach((button) => {
    button.addEventListener('click', greet);
  });

  stage.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return;
    greet();
  });

  let currentStatus = '';
  function updateStatus(text, active, greeting) {
    if (text !== currentStatus) {
      statusText.textContent = text;
      currentStatus = text;
    }
    statusHud.classList.toggle('is-active', active);
    statusHud.classList.toggle('is-greeting', greeting);
  }

  function resize() {
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    if (!width || !height) return;
    const aspect = width / height;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    camera.aspect = aspect;
    camera.fov = aspect < 0.85 ? 35 : 33;
    camera.position.z = aspect < 0.75 ? 8.9 : aspect < 0.95 ? 8.15 : 7.5;
    camera.updateProjectionMatrix();
  }

  if ('ResizeObserver' in window) {
    const observer = new ResizeObserver(resize);
    observer.observe(stage);
  } else {
    window.addEventListener('resize', resize);
  }
  resize();

  const clock = new THREE.Clock();
  const bootAt = performance.now();
  let elapsed = 0;
  let hudElapsed = 0;
  let nextBlink = 2.2 + Math.random() * 2.5;
  let blinkStartedAt = -1;
  let ready = false;

  function animate() {
    const delta = Math.min(clock.getDelta(), 0.05);
    elapsed += delta;
    const t = elapsed;
    const idle = reducedMotion ? 0 : 1;
    const greetAge = performance.now() / 1000 - greetStartedAt;
    const greeting = greetAge >= 0 && greetAge < 3 ? greetAge : -1;
    const greetEnvelope = greeting >= 0
      ? smoothstep(0, 0.5, greetAge) * (1 - smoothstep(2.15, 3, greetAge))
      : 0;

    pointer.x = THREE.MathUtils.damp(pointer.x, pointer.targetX, 9, delta);
    pointer.y = THREE.MathUtils.damp(pointer.y, pointer.targetY, 9, delta);

    head.rotation.y = THREE.MathUtils.damp(head.rotation.y, pointer.x * 0.76 + Math.sin(t * 0.5) * 0.012 * idle + greetEnvelope * 0.1, 9, delta);
    head.rotation.x = THREE.MathUtils.damp(head.rotation.x, pointer.y * 0.34 + Math.cos(t * 0.62) * 0.008 * idle, 9, delta);
    head.rotation.z = THREE.MathUtils.damp(head.rotation.z, -pointer.x * 0.06 - greetEnvelope * 0.11, 7, delta);

    body.rotation.y = THREE.MathUtils.damp(body.rotation.y, pointer.x * 0.17, 5, delta);
    body.rotation.x = THREE.MathUtils.damp(body.rotation.x, pointer.y * 0.04, 5, delta);
    body.rotation.z = THREE.MathUtils.damp(body.rotation.z, -pointer.x * 0.016, 4, delta);
    body.position.y = Math.sin(t * 1.05 + 0.4) * 0.006 * idle;

    figure.rotation.y = THREE.MathUtils.damp(figure.rotation.y, pointer.x * 0.07, 3.2, delta);
    figure.position.y = THREE.MathUtils.damp(figure.position.y, Math.sin(t) * 0.012 * idle, 3, delta);

    const introProgress = clamp((performance.now() - bootAt) / 1500, 0, 1);
    const introEase = 1 - Math.pow(1 - introProgress, 3);
    const figureScale = reducedMotion ? 1 : 0.955 + 0.045 * introEase;
    figure.scale.setScalar(figureScale);

    eyes.position.x = THREE.MathUtils.damp(eyes.position.x, pointer.x * 0.018, 12, delta);
    eyes.position.y = THREE.MathUtils.damp(eyes.position.y, -pointer.y * 0.014, 12, delta);

    if (t > nextBlink && blinkStartedAt < 0) {
      blinkStartedAt = t;
      nextBlink = t + 2.4 + Math.random() * 4.2;
    }

    let eyeOpen = 1;
    if (blinkStartedAt >= 0) {
      const blinkProgress = (t - blinkStartedAt) / 0.17;
      if (blinkProgress >= 1) {
        blinkStartedAt = -1;
      } else {
        eyeOpen = 1 - Math.sin(blinkProgress * Math.PI) * 0.92;
      }
    }
    eyes.scale.y = THREE.MathUtils.damp(eyes.scale.y, eyeOpen, 30, delta);

    const armSway = Math.sin(t * 1.1) * 0.012 * idle;
    if (greetEnvelope > 0.001) {
      armRight.rotation.z = armRight.userData.baseZ + 2.08 * greetEnvelope;
      armRight.rotation.x = armRight.userData.baseX - 0.22 * greetEnvelope;
      armRight.userData.elbow.rotation.z = armRight.userData.elbow.userData.baseZ + Math.sin(greetAge * 12) * 0.5 * greetEnvelope;
      armRight.userData.elbow.rotation.x = armRight.userData.elbow.userData.baseX - 0.12 * greetEnvelope;
    } else {
      armRight.rotation.z = THREE.MathUtils.damp(armRight.rotation.z, armRight.userData.baseZ + armSway, 7, delta);
      armRight.rotation.x = THREE.MathUtils.damp(armRight.rotation.x, armRight.userData.baseX, 7, delta);
      armRight.userData.elbow.rotation.z = THREE.MathUtils.damp(armRight.userData.elbow.rotation.z, armRight.userData.elbow.userData.baseZ, 7, delta);
      armRight.userData.elbow.rotation.x = THREE.MathUtils.damp(armRight.userData.elbow.rotation.x, armRight.userData.elbow.userData.baseX, 7, delta);
    }

    armLeft.rotation.z = armLeft.userData.baseZ - armSway * 0.7;
    armLeft.rotation.x = armLeft.userData.baseX + Math.sin(t * 0.9 + 1) * 0.012 * idle;

    rig.rotation.y = THREE.MathUtils.damp(rig.rotation.y, pointer.x * 0.035, 2.5, delta);
    rig.position.x = THREE.MathUtils.damp(rig.position.x, pointer.x * 0.05, 2.5, delta);
    rig.position.y = THREE.MathUtils.damp(rig.position.y, -pointer.y * 0.028, 2.5, delta);

    camera.position.x = THREE.MathUtils.damp(camera.position.x, pointer.x * 0.085, 2, delta);
    camera.position.y = THREE.MathUtils.damp(camera.position.y, 1.1 - pointer.y * 0.045, 2, delta);
    camera.lookAt(0, 0.55, 0);

    halo.rotation.z = Math.sin(t * 0.09) * 0.08;
    halo.rotation.x = Math.sin(t * 0.12) * 0.03;
    haloMaterial.opacity = 0.3 + Math.sin(t * 0.8) * 0.06 + greetEnvelope * 0.32;
    haloMagentaMaterial.opacity = 0.18 + Math.sin(t * 0.65 + 1.4) * 0.05 + greetEnvelope * 0.18;

    orbit.rotation.z = t * 0.12;
    orbit.rotation.x = 1.27 + Math.sin(t * 0.3) * 0.05;

    coreMaterial.emissiveIntensity = 3.4 + Math.sin(t * 2.1) * 0.35 + greetEnvelope * 2.4;
    topLight.intensity = 16 + Math.sin(t * 1.7) * 1.2 + greetEnvelope * 9;
    backLight.intensity = 14 + Math.sin(t * 1.3 + 0.8) * 1.4 + greetEnvelope * 5;

    shards.forEach((shard) => {
      shard.mesh.position.y = shard.baseY + Math.sin(t * 0.55 + shard.phase) * 0.09 * idle;
      shard.mesh.rotation.y += delta * shard.speed;
      shard.mesh.rotation.x += delta * shard.speed * 0.6;
    });

    particles.rotation.y = t * 0.012 * (idle ? 1 : 0.15);
    particles.rotation.x = Math.sin(t * 0.05) * 0.025 * idle;

    if (stagePointer.visible) {
      stagePointer.x = THREE.MathUtils.damp(stagePointer.x, stagePointer.targetX, 20, delta);
      stagePointer.y = THREE.MathUtils.damp(stagePointer.y, stagePointer.targetY, 20, delta);
      cursorOrb.style.transform = `translate3d(${stagePointer.x}px, ${stagePointer.y}px, 0) translate(-50%, -50%)`;
    }

    hudElapsed += delta;
    if (hudElapsed > 0.09) {
      hudElapsed = 0;
      const totalYaw = THREE.MathUtils.radToDeg(head.rotation.y + body.rotation.y + figure.rotation.y);
      const totalPitch = THREE.MathUtils.radToDeg(-head.rotation.x);
      gazeReadout.textContent = `Yaw ${formatDegrees(totalYaw)} / Pitch ${formatDegrees(totalPitch)}`;
      const isGreeting = greetEnvelope > 0.08;
      updateStatus(
        isGreeting ? 'Greeting' : pointer.active ? 'Gaze lock' : 'Idle scan',
        pointer.active && !isGreeting,
        isGreeting
      );
    }

    renderer.render(scene, camera);

    if (!ready) {
      ready = true;
      window.requestAnimationFrame(() => stage.classList.add('is-ready'));
    }
  }

  reduceMotionQuery.addEventListener?.('change', (event) => {
    reducedMotion = event.matches;
  });

  canvas.addEventListener('webglcontextlost', (event) => {
    event.preventDefault();
    renderer.setAnimationLoop(null);
    showFallback(new Error('WebGL context lost'));
  });

  renderer.setAnimationLoop(animate);
}

try {
  boot();
} catch (error) {
  showFallback(error);
}
})();

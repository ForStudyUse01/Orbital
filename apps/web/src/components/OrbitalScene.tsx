import { Line, OrbitControls, Stars, useTexture } from "@react-three/drei";
import { Canvas, type ThreeEvent, useThree } from "@react-three/fiber";
import { memo, Suspense, useEffect, useMemo } from "react";
import {
  AdditiveBlending,
  BackSide,
  CanvasTexture,
  SRGBColorSpace,
  NormalBlending,
} from "three";
import type { ObjectCategory, Position } from "../types";

// A soft round sprite for each tracked object — reads as a tiny glowing
// marker rather than a hard-edged square GL point, at zero per-object cost.
function createPointSprite() {
  const canvas = document.createElement("canvas");
  canvas.width = 32;
  canvas.height = 32;
  const context = canvas.getContext("2d");
  if (!context) return undefined;
  const gradient = context.createRadialGradient(16, 16, 0, 16, 16, 16);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(.4, "rgba(255,255,255,.9)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, 32, 32);
  return new CanvasTexture(canvas);
}

const EARTH_DAY_MAP = "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg";
const EARTH_NIGHT_MAP = "https://unpkg.com/three-globe/example/img/earth-night.jpg";
const EARTH_BUMP_MAP = "https://unpkg.com/three-globe/example/img/earth-topology.png";
const EARTH_SPECULAR_MAP = "https://unpkg.com/three-globe/example/img/earth-water.png";

export type CameraPreset = "globe" | "leo" | "polar" | "system";

interface OrbitalSceneProps {
  positions: Position[];
  selectedId?: number;
  onSelect: (position?: Position) => void;
  renderingMode: "objects" | "density";
  autoRotate: boolean;
  showGuides: boolean;
  showAtmosphere: boolean;
  showStars: boolean;
  simulationSpeed: number;
  cameraPreset: CameraPreset;
}

const categoryColors: Record<ObjectCategory, [number, number, number]> = {
  active_payload: [0.24, 0.95, 0.65],
  inactive_payload: [1, 0.76, 0.2],
  debris: [1, 0.27, 0.31],
  rocket_body: [0.25, 0.55, 1],
  unknown: [0.67, 0.55, 0.95],
};

// Real NASA Blue Marble / Black Marble photographic imagery (via the three-globe
// asset CDN), not a stylized illustration — the night map's city lights read
// clearly against this scene's dark-space background.
function Earth({ showAtmosphere }: { showAtmosphere: boolean }) {
  const [dayMap, nightMap, bumpMap, specularMap] = useTexture([
    EARTH_DAY_MAP, EARTH_NIGHT_MAP, EARTH_BUMP_MAP, EARTH_SPECULAR_MAP,
  ]);
  useEffect(() => {
    dayMap.colorSpace = SRGBColorSpace;
    nightMap.colorSpace = SRGBColorSpace;
    [dayMap, nightMap].forEach((texture) => { texture.anisotropy = 4; });
  }, [dayMap, nightMap]);

  return <group>
    <mesh>
      <sphereGeometry args={[1, 96, 96]} />
      <meshPhongMaterial
        map={dayMap} bumpMap={bumpMap} bumpScale={.012}
        specularMap={specularMap} specular="#1b2a38" shininess={7}
        emissiveMap={nightMap} emissive="#ffe6b0" emissiveIntensity={1.1}
      />
    </mesh>
    {showAtmosphere && <mesh scale={1.025}>
      <sphereGeometry args={[1, 48, 24]} />
      <shaderMaterial transparent side={BackSide} blending={AdditiveBlending} depthWrite={false}
        vertexShader={`
          varying vec3 vNormal;
          varying vec3 vView;
          void main() {
            vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
            vNormal = normalize(normalMatrix * normal);
            vView = normalize(-viewPosition.xyz);
            gl_Position = projectionMatrix * viewPosition;
          }
        `}
        fragmentShader={`
          varying vec3 vNormal;
          varying vec3 vView;
          void main() {
            float rim = pow(1.0 - abs(dot(normalize(vNormal), normalize(vView))), 3.0);
            gl_FragColor = vec4(0.18, 0.62, 1.0, rim * 0.62);
          }
        `} />
    </mesh>}
  </group>;
}

function orbitalCircle(radius: number, inclination = 0) {
  return Array.from({ length: 129 }, (_, index) => {
    const phase = index / 128 * Math.PI * 2;
    return [Math.cos(phase) * radius, Math.sin(phase) * radius * Math.sin(inclination), Math.sin(phase) * radius * Math.cos(inclination)] as [number, number, number];
  });
}

function OrbitalGuides() {
  const guides = useMemo(() => [
    { radius: 1.063, inclination: 0, color: "#52d6bd" },
    { radius: 1.125, inclination: .9, color: "#5b8ee6" },
    { radius: 1.251, inclination: 1.7, color: "#efbb61" },
    { radius: 6.61, inclination: 0, color: "#8b76d9" },
  ], []);
  return <group>{guides.map((guide, index) => <Line key={index} points={orbitalCircle(guide.radius, guide.inclination)} color={guide.color} transparent opacity={index === 3 ? .14 : .22} lineWidth={.55} />)}</group>;
}

const OrbitalPoints = memo(function OrbitalPoints({ positions, onSelect, renderingMode }: Pick<OrbitalSceneProps, "positions" | "onSelect" | "renderingMode">) {
  const [coords, colors] = useMemo(() => {
    const xyz = new Float32Array(positions.length * 3);
    const rgb = new Float32Array(positions.length * 3);
    positions.forEach((position, index) => {
      xyz.set([position.x, position.y, position.z], index * 3);
      rgb.set(categoryColors[position.category], index * 3);
    });
    return [xyz, rgb];
  }, [positions]);
  const sprite = useMemo(createPointSprite, []);
  useEffect(() => () => sprite?.dispose(), [sprite]);
  const handleClick = (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation();
    if (typeof event.index === "number") onSelect(positions[event.index]);
  };
  return <points onClick={handleClick} onPointerOver={() => { document.body.style.cursor = "pointer"; }} onPointerOut={() => { document.body.style.cursor = ""; }}>
    <bufferGeometry><bufferAttribute attach="attributes-position" args={[coords, 3]} /><bufferAttribute attach="attributes-color" args={[colors, 3]} /></bufferGeometry>
    <pointsMaterial map={sprite} alphaTest={.1} size={renderingMode === "density" ? 5 : 3} sizeAttenuation={false} vertexColors transparent opacity={renderingMode === "density" ? .22 : .95} depthWrite={false} blending={renderingMode === "density" ? AdditiveBlending : NormalBlending} />
  </points>;
});

const cameraPositions: Record<CameraPreset, [number, number, number]> = {
  globe: [0, .35, 3.2], leo: [0, 1.15, 4.6], polar: [.01, 4.4, .01], system: [0, 4.3, 9.2],
};

function CameraRig({ preset }: { preset: CameraPreset }) {
  const { camera, size } = useThree();
  useEffect(() => {
    camera.position.set(...cameraPositions[preset]);
    // Keep the entire globe visible in narrow panels and on phones.
    const aspect = size.width / Math.max(size.height, 1);
    const minimumDistance = 1.32 / Math.sin(Math.atan(Math.tan(Math.PI / 8) * Math.min(aspect, 1)));
    if (camera.position.length() < minimumDistance) camera.position.setLength(minimumDistance);
    camera.up.set(0, 1, 0);
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
  }, [camera, preset, size.width, size.height]);
  return null;
}

export function OrbitalScene(props: OrbitalSceneProps) {
  return <div className="orbital-scene" aria-label={`Interactive 3D orbital environment showing ${props.positions.length.toLocaleString()} objects`}>
    <Canvas frameloop={props.autoRotate && props.simulationSpeed > 0 ? "always" : "demand"} gl={{ antialias: false, powerPreference: "high-performance" }} raycaster={{ params: { Points: { threshold: .015 }, Line: { threshold: .01 }, Mesh: {}, LOD: {}, Sprite: {} } }} camera={{ position: cameraPositions.globe, fov: 45, near: .02, far: 120 }} dpr={1} onPointerMissed={() => props.onSelect(undefined)}>
      <color attach="background" args={["#01060c"]} />
      <fog attach="fog" args={["#01060c", 12, 42]} />
      <ambientLight intensity={.16} />
      <directionalLight position={[5, 2.5, 4]} intensity={2.4} color="#fff6e8" />
      <directionalLight position={[-4, -1, -3]} intensity={.22} color="#2469b7" />
      {props.showStars && <Stars radius={75} depth={45} count={700} factor={1.5} saturation={.35} fade speed={0} />}
      <Suspense fallback={null}><Earth showAtmosphere={props.showAtmosphere} /></Suspense>
      {props.showGuides && <OrbitalGuides />}
      <OrbitalPoints positions={props.positions} onSelect={props.onSelect} renderingMode={props.renderingMode} />
      <CameraRig preset={props.cameraPreset} />
      <OrbitControls enablePan={false} minDistance={1.42} maxDistance={15} autoRotate={props.autoRotate} autoRotateSpeed={.22 * props.simulationSpeed} dampingFactor={.055} enableDamping />
    </Canvas>
    <div className="scene-scale"><span>Reference body</span><strong>Earth · 6,378 km radius</strong></div>
    <div className="scene-compass" aria-hidden="true"><span>N</span><i /></div>
    <div className="scene-help">Drag to orbit · Scroll to zoom · Select any object</div>
  </div>;
}

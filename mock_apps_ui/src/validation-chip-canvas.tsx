import { useLayoutEffect, useRef, useState } from "react";
import { Minus, Plus, RotateCcw, RotateCw } from "lucide-react";

export type ChipRegion = "context" | "compute" | "io";
export type ChipScopeMode = "before" | "after" | "changes";

type Props = {
  region: ChipRegion;
  mode: ChipScopeMode;
  onRegionChange: (region: ChipRegion) => void;
};

type Point = { x: number; y: number };
type ProjectedPoint = Point & { depth: number };
type HitArea = { points: Point[]; region: ChipRegion };
type Camera = { yaw: number; pitch: number; zoom: number };
type CameraAction = "left" | "right" | "top" | "in" | "out";

// This is a conceptual block layout, not an engineering floorplan. The palette
// follows the approved light source-app preview; geometry never represents data.
const palette = {
  paper: "#ffffff",
  canvas: "#f6f8fa",
  ink: "#243247",
  muted: "#617184",
  line: "#d8e0e8",
  grid: "#e7edf2",
  board: "#e5ebef",
  block: "#f8fafb",
  side: "#c6d1da",
  trace: "#a5b7c6",
  before: "#607e9c",
  after: "#007f83",
  beforeSoft: "#e7edf4",
  afterSoft: "#d7eeee",
};

const REGION_NAMES: Record<ChipRegion, string> = {
  context: "context and memory paths",
  compute: "compute array",
  io: "I/O and scheduling",
};
const MIN_ZOOM = 0.65;
const MAX_ZOOM = 1.35;
const clampZoom = (value: number) =>
  Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, value));

function renderChip(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  camera: Camera,
  region: ChipRegion,
  mode: ChipScopeMode,
): HitArea[] {
  const hitAreas: HitArea[] = [];
  const { yaw, pitch, zoom } = camera;
  const rawProject = (x: number, y: number, z: number): ProjectedPoint => {
    const u = x * Math.cos(yaw) - y * Math.sin(yaw);
    const v = x * Math.sin(yaw) + y * Math.cos(yaw);
    return {
      x: u,
      y: v * Math.sin(pitch) - z * Math.cos(pitch),
      depth: v * Math.cos(pitch) + z * Math.sin(pitch),
    };
  };
  // Fit the rotated chip, including its pins and raised hotspots, in the space
  // between the stage labels and camera. Zoom above 1 remains a deliberate crop.
  const bounds = [-218, 218].flatMap((x) =>
    [-166, 166].flatMap((y) => [-8, 24].map((z) => rawProject(x, y, z))),
  );
  const minX = Math.min(...bounds.map((point) => point.x));
  const maxX = Math.max(...bounds.map((point) => point.x));
  const minY = Math.min(...bounds.map((point) => point.y));
  const maxY = Math.max(...bounds.map((point) => point.y));
  const scale =
    Math.min(
      Math.max(1, width - 52) / (maxX - minX),
      Math.max(1, height - 97) / (maxY - minY),
    ) * zoom;
  const project = (x: number, y: number, z = 0): ProjectedPoint => {
    const point = rawProject(x, y, z);
    return {
      x: width / 2 + (point.x - (minX + maxX) / 2) * scale,
      y: (height + 7) / 2 + (point.y - (minY + maxY) / 2) * scale,
      depth: point.depth,
    };
  };
  const path = (
    points: Point[],
    fill: string | null,
    stroke = palette.line,
    lineWidth = 1,
    dash: number[] = [],
  ) => {
    ctx.beginPath();
    points.forEach((point, index) =>
      index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y),
    );
    ctx.closePath();
    if (fill) {
      ctx.fillStyle = fill;
      ctx.fill();
    }
    ctx.strokeStyle = stroke;
    ctx.lineWidth = lineWidth;
    ctx.setLineDash(dash);
    ctx.stroke();
    ctx.setLineDash([]);
  };
  const line = (
    points: Point[],
    color: string,
    lineWidth = 1,
    dash: number[] = [],
  ) => {
    ctx.beginPath();
    points.forEach((point, index) =>
      index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y),
    );
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.setLineDash(dash);
    ctx.stroke();
    ctx.setLineDash([]);
  };
  const corners = (x: number, y: number, w: number, h: number) => [
    [x, y],
    [x + w, y],
    [x + w, y + h],
    [x, y + h],
  ];
  const rect = (
    x: number,
    y: number,
    w: number,
    h: number,
    z: number,
    fill: string,
    stroke = palette.line,
    lineWidth = 1,
  ) => {
    const points = corners(x, y, w, h).map(([a, b]) => project(a, b, z));
    path(points, fill, stroke, lineWidth);
    return points;
  };
  const box = (
    x: number,
    y: number,
    w: number,
    h: number,
    z: number,
    thickness: number,
    fill: string,
    stroke = palette.line,
  ) => {
    const base = corners(x, y, w, h);
    const bottom = base.map(([a, b]) => project(a, b, z));
    const top = base.map(([a, b]) => project(a, b, z + thickness));
    const sides = base
      .map((_, index) => ({
        points: [
          bottom[index],
          bottom[(index + 1) % 4],
          top[(index + 1) % 4],
          top[index],
        ],
        depth: (bottom[index].depth + bottom[(index + 1) % 4].depth) / 2,
      }))
      .sort((a, b) => a.depth - b.depth);
    sides.forEach((side) => path(side.points, palette.side));
    path(top, fill, stroke);
    return top;
  };
  const activeColor = (id: ChipRegion) =>
    id === "io" || mode === "before" ? palette.before : palette.after;
  const focusFill = (id: ChipRegion) =>
    region !== id
      ? palette.block
      : id === "io" || mode === "before"
        ? palette.beforeSoft
        : palette.afterSoft;
  const mark = (
    x: number,
    y: number,
    z: number,
    number: string,
    id: ChipRegion,
  ) => {
    const point = project(x, y, z);
    ctx.fillStyle = region === id ? activeColor(id) : palette.paper;
    ctx.strokeStyle = activeColor(id);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(point.x, point.y, 12, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = region === id ? palette.paper : palette.ink;
    ctx.font = "500 11px ui-monospace, monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(number, point.x, point.y);
    hitAreas.push({
      points: [
        { x: point.x - 18, y: point.y - 18 },
        { x: point.x + 18, y: point.y - 18 },
        { x: point.x + 18, y: point.y + 18 },
        { x: point.x - 18, y: point.y + 18 },
      ],
      region: id,
    });
  };

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = palette.canvas;
  ctx.fillRect(0, 0, width, height);
  for (let x = 0; x < width; x += 24)
    line(
      [
        { x, y: 0 },
        { x, y: height },
      ],
      palette.grid,
      0.6,
    );
  for (let y = 0; y < height; y += 24)
    line(
      [
        { x: 0, y },
        { x: width, y },
      ],
      palette.grid,
      0.6,
    );

  box(-204, -148, 408, 296, -8, 8, palette.board);
  for (let index = 0; index < 32; index++) {
    const x = -185 + index * 12;
    line([project(x, -151, -3), project(x, -161, -3)], palette.trace, 1.2);
    line([project(x, 151, -3), project(x, 161, -3)], palette.trace, 1.2);
  }
  for (let index = 0; index < 22; index++) {
    const y = -132 + index * 12;
    line([project(-206, y, -3), project(-215, y, -3)], palette.trace, 1.2);
    line([project(206, y, -3), project(215, y, -3)], palette.trace, 1.2);
  }
  for (const side of [-1, 1]) {
    for (let index = 0; index < 13; index++) {
      const y = -78 + index * 12;
      line(
        [
          project(side * 166, y, 1),
          project(side * 114, y, 1),
          project(side * 104, y + 7, 1),
          project(side * 86, y + 7, 1),
        ],
        palette.trace,
        0.7,
      );
    }
  }
  for (let index = 0; index < 9; index++) {
    const x = -84 + index * 21;
    line(
      [
        project(x, 64, 1),
        project(x, 82, 1),
        project(x + 6, 90, 1),
        project(x + 6, 105, 1),
      ],
      palette.trace,
      0.8,
    );
  }

  for (const side of [-1, 1]) {
    for (let row = 0; row < 3; row++) {
      const x = side < 0 ? -176 : 128;
      const y = -108 + row * 74;
      const points = box(
        x,
        y,
        48,
        62,
        2,
        9,
        focusFill("context"),
        region === "context" ? activeColor("context") : palette.line,
      );
      hitAreas.push({ points, region: "context" });
      for (let detail = 1; detail < 6; detail++)
        line(
          [
            project(x + 7, y + detail * 9, 11.3),
            project(x + 41, y + detail * 9, 11.3),
          ],
          palette.trace,
          0.6,
        );
    }
  }
  hitAreas.push({
    points: box(
      -104,
      -101,
      208,
      174,
      2,
      5,
      focusFill("compute"),
      region === "compute" ? activeColor("compute") : palette.line,
    ),
    region: "compute",
  });
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 5; col++) {
      const x = -97 + col * 40;
      const y = -94 + row * 40;
      rect(
        x,
        y,
        33,
        33,
        7.5,
        region === "compute" ? focusFill("compute") : palette.board,
        palette.trace,
        0.8,
      );
      for (let detail = 0; detail < 3; detail++)
        line(
          [
            project(x + 5, y + 9 + detail * 7, 8),
            project(x + 28, y + 9 + detail * 7, 8),
          ],
          palette.trace,
          0.6,
        );
    }
  }
  hitAreas.push({
    points: box(
      -104,
      103,
      208,
      28,
      2,
      6,
      focusFill("io"),
      region === "io" ? activeColor("io") : palette.line,
    ),
    region: "io",
  });
  for (let index = 0; index < 8; index++)
    rect(-95 + index * 24, 109, 17, 15, 8.2, palette.board, palette.trace, 0.7);

  if (region === "context" || mode === "changes") {
    for (const side of [-1, 1]) {
      line(
        [
          project(side * 149, -91, 13),
          project(side * 114, -91, 13),
          project(side * 100, -62, 10),
          project(side * 80, -62, 10),
        ],
        activeColor("context"),
        2.5,
      );
      if (mode === "changes")
        line(
          [
            project(side * 149, -79, 13),
            project(side * 115, -79, 13),
            project(side * 104, -52, 10),
            project(side * 80, -52, 10),
          ],
          palette.before,
          1.5,
          [3, 3],
        );
      if (mode !== "before") {
        for (let row = 1; row <= 2; row++)
          line(
            [
              project(side * 149, -91 + row * 74, 13),
              project(side * 114, -91 + row * 74, 13),
              project(side * 100, -62 + row * 52, 10),
              project(side * 80, -62 + row * 52, 10),
            ],
            palette.after,
            2,
          );
      }
    }
  }
  if (region === "compute")
    path(
      [
        project(-108, -105, 11),
        project(108, -105, 11),
        project(108, 78, 11),
        project(-108, 78, 11),
      ],
      null,
      activeColor("compute"),
      2,
      [4, 3],
    );
  if (region === "io") {
    for (let index = 0; index < 4; index++)
      line(
        [project(-63 + index * 42, 70, 12), project(-63 + index * 42, 114, 12)],
        palette.before,
        2,
      );
  }
  mark(-153, -42, 24, "01", "context");
  mark(0, -10, 24, "02", "compute");
  mark(0, 115, 22, "03", "io");

  ctx.font = "11px ui-monospace, monospace";
  ctx.textBaseline = "middle";
  ctx.textAlign = "left";
  ctx.fillStyle = palette.muted;
  ctx.fillText("X", 44, height - 26);
  ctx.fillText("Y", 22, height - 49);
  line(
    [
      { x: 24, y: height - 25 },
      { x: 39, y: height - 25 },
    ],
    palette.muted,
  );
  line(
    [
      { x: 24, y: height - 25 },
      { x: 24, y: height - 41 },
    ],
    palette.muted,
  );
  return hitAreas;
}

function regionAt(point: Point, hitAreas: HitArea[]): ChipRegion | null {
  for (let index = hitAreas.length - 1; index >= 0; index--) {
    const { points, region } = hitAreas[index];
    let inside = false;
    for (let a = 0, b = points.length - 1; a < points.length; b = a++) {
      if (
        points[a].y > point.y !== points[b].y > point.y &&
        point.x <
          ((points[b].x - points[a].x) * (point.y - points[a].y)) /
            (points[b].y - points[a].y) +
            points[a].x
      )
        inside = !inside;
    }
    if (inside) return region;
  }
  return null;
}

export function ValidationChipCanvas({ region, mode, onRegionChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const propsRef = useRef({ region, mode, onRegionChange });
  const drawRef = useRef<(() => void) | null>(null);
  const cameraActionRef = useRef<((action: CameraAction) => void) | null>(null);
  const [topView, setTopView] = useState(false);
  const [zoom, setZoom] = useState(1);

  // Native canvas listeners always see the latest controlled selection/callback.
  useLayoutEffect(() => {
    propsRef.current = { region, mode, onRegionChange };
    drawRef.current?.();
  }, [region, mode, onRegionChange]);

  useLayoutEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const camera: Camera = { yaw: -0.3, pitch: 0.87, zoom: 1 };
    let width = 0;
    let height = 0;
    let hitAreas: HitArea[] = [];
    let pointer: { id: number; x: number; y: number; travel: number } | null =
      null;
    const draw = () => {
      if (width > 0 && height > 0)
        hitAreas = renderChip(
          ctx,
          width,
          height,
          camera,
          propsRef.current.region,
          propsRef.current.mode,
        );
    };
    const syncCamera = () => {
      setTopView(camera.pitch > 1.45);
      setZoom(camera.zoom);
      draw();
    };
    const resize = () => {
      const bounds = canvas.getBoundingClientRect();
      width = bounds.width;
      height = bounds.height;
      const density = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = Math.round(width * density);
      canvas.height = Math.round(height * density);
      ctx.setTransform(density, 0, 0, density, 0, 0);
      draw();
    };
    const localPoint = (event: PointerEvent) => {
      const bounds = canvas.getBoundingClientRect();
      return { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
    };
    const pointerDown = (event: PointerEvent) => {
      if (!event.isPrimary || event.button !== 0 || pointer) return;
      pointer = {
        id: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        travel: 0,
      };
      canvas.setPointerCapture(event.pointerId);
      canvas.style.cursor = "grabbing";
    };
    const pointerMove = (event: PointerEvent) => {
      if (pointer && event.pointerId === pointer.id) {
        const dx = event.clientX - pointer.x;
        const dy = event.clientY - pointer.y;
        pointer.travel += Math.abs(dx) + Math.abs(dy);
        camera.yaw += dx * 0.008;
        camera.pitch = Math.max(
          0.35,
          Math.min(Math.PI / 2, camera.pitch + dy * 0.006),
        );
        pointer.x = event.clientX;
        pointer.y = event.clientY;
        syncCamera();
      } else if (!pointer)
        canvas.style.cursor = regionAt(localPoint(event), hitAreas)
          ? "pointer"
          : "grab";
    };
    const releasePointer = () => {
      const id = pointer?.id;
      pointer = null;
      if (id !== undefined && canvas.hasPointerCapture(id))
        canvas.releasePointerCapture(id);
      canvas.style.cursor = "grab";
    };
    const pointerUp = (event: PointerEvent) => {
      if (!pointer || event.pointerId !== pointer.id) return;
      const selected =
        pointer.travel < 5 ? regionAt(localPoint(event), hitAreas) : null;
      releasePointer();
      if (selected) propsRef.current.onRegionChange(selected);
    };
    const pointerCancel = (event: PointerEvent) => {
      if (pointer?.id === event.pointerId) releasePointer();
    };
    const wheel = (event: WheelEvent) => {
      event.preventDefault();
      const unit =
        event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? height : 1;
      camera.zoom = clampZoom(camera.zoom - event.deltaY * unit * 0.001);
      syncCamera();
    };
    drawRef.current = draw;
    cameraActionRef.current = (action) => {
      if (action === "left") camera.yaw -= 0.22;
      if (action === "right") camera.yaw += 0.22;
      if (action === "in") camera.zoom = clampZoom(camera.zoom + 0.1);
      if (action === "out") camera.zoom = clampZoom(camera.zoom - 0.1);
      if (action === "top")
        camera.pitch = camera.pitch > 1.45 ? 0.87 : Math.PI / 2;
      syncCamera();
    };
    canvas.addEventListener("pointerdown", pointerDown);
    canvas.addEventListener("pointermove", pointerMove);
    canvas.addEventListener("pointerup", pointerUp);
    canvas.addEventListener("pointercancel", pointerCancel);
    canvas.addEventListener("lostpointercapture", pointerCancel);
    canvas.addEventListener("wheel", wheel, { passive: false });
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();
    return () => {
      observer.disconnect();
      canvas.removeEventListener("pointerdown", pointerDown);
      canvas.removeEventListener("pointermove", pointerMove);
      canvas.removeEventListener("pointerup", pointerUp);
      canvas.removeEventListener("pointercancel", pointerCancel);
      canvas.removeEventListener("lostpointercapture", pointerCancel);
      canvas.removeEventListener("wheel", wheel);
      releasePointer();
      drawRef.current = null;
      cameraActionRef.current = null;
    };
  }, []);

  return (
    <div className="vfc-stage">
      <div className="vfc-stage-label">
        <strong>Illustrative floorplan</strong>
        <span>
          {mode === "before"
            ? "Original workload scope"
            : mode === "after"
              ? "Updated workload scope"
              : "Original → Updated workload scope"}
        </span>
      </div>
      <div className="vfc-stage-legend" aria-label="Scope overlay legend">
        {mode !== "after" && (
          <span className="vfc-legend-original">Original scope</span>
        )}
        {mode !== "before" && (
          <span className="vfc-legend-updated">Updated scope</span>
        )}
      </div>
      <canvas
        ref={canvasRef}
        className="vfc-canvas"
        role="img"
        aria-label={`Interactive illustrative chip. Selected region: ${REGION_NAMES[region]}. Drag to rotate, scroll to zoom, or click a numbered region. Region buttons below provide keyboard selection; camera buttons provide keyboard rotation and zoom. This diagram does not represent a physical chip design.`}
      >
        Illustrative chip: 01 context and memory paths, 02 compute array, 03 I/O
        and scheduling. Use the region and camera buttons to explore.
      </canvas>
      <div className="vfc-camera" role="group" aria-label="Diagram camera">
        <button
          type="button"
          aria-label="Rotate left"
          title="Rotate left"
          onClick={() => cameraActionRef.current?.("left")}
        >
          <RotateCcw aria-hidden="true" />
        </button>
        <button
          type="button"
          aria-label="Rotate right"
          title="Rotate right"
          onClick={() => cameraActionRef.current?.("right")}
        >
          <RotateCw aria-hidden="true" />
        </button>
        <button
          type="button"
          aria-label={topView ? "Switch to oblique view" : "Switch to top view"}
          onClick={() => cameraActionRef.current?.("top")}
        >
          {topView ? "Oblique" : "Top"}
        </button>
        <button
          type="button"
          aria-label="Zoom out"
          title="Zoom out"
          disabled={zoom <= MIN_ZOOM}
          onClick={() => cameraActionRef.current?.("out")}
        >
          <Minus aria-hidden="true" />
        </button>
        <button
          type="button"
          aria-label="Zoom in"
          title="Zoom in"
          disabled={zoom >= MAX_ZOOM}
          onClick={() => cameraActionRef.current?.("in")}
        >
          <Plus aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}

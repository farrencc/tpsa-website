const N = 40, HIST = 14, W = 520, H = 300, PAD = 24;
const SVG_NS = "http://www.w3.org/2000/svg";

/* ---------- PRAXIS: probabilistic infrastructure forecast ----------
   An SVG rather than a canvas: the history line is solid, the forecast draws
   itself in, and two confidence bands fade up behind it. */
export function start(container) {
  const el = (name, attrs = {}) => {
    const n = document.createElementNS(SVG_NS, name);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    return n;
  };

  const pts = [];
  let v = 42;
  for (let i = 0; i < N; i++) {
    v += Math.sin(i * 0.5) * 2 + (i < HIST ? (Math.random() - 0.5) * 3 : 3.2);
    pts.push(v);
  }

  const xs = (i) => PAD + (i / (N - 1)) * (W - PAD * 2);
  const ymin = 30, ymax = Math.max(...pts) + 30;
  const ys = (val) => H - PAD - ((val - ymin) / (ymax - ymin)) * (H - PAD * 2);
  const spread = (i) => (i < HIST ? 0 : (i - HIST) * 2.6);
  const band = (mult) => {
    let d = `M ${xs(HIST)} ${ys(pts[HIST])}`;
    for (let i = HIST; i < N; i++) d += ` L ${xs(i)} ${ys(pts[i] + spread(i) * mult)}`;
    for (let i = N - 1; i >= HIST; i--) d += ` L ${xs(i)} ${ys(pts[i] - spread(i) * mult)}`;
    return d + " Z";
  };
  const line = (upto) => pts.slice(0, upto).map((val, i) => `${i === 0 ? "M" : "L"} ${xs(i)} ${ys(val)}`).join(" ");

  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMidYMid meet" });
  svg.style.cssText = "width:100%;height:100%";

  const defs = el("defs");
  const grad = el("linearGradient", { id: "pxg", x1: "0", x2: "1" });
  grad.appendChild(el("stop", { offset: "0", "stop-color": "#9d4edd" }));
  grad.appendChild(el("stop", { offset: "1", "stop-color": "#32e875" }));
  defs.appendChild(grad);
  svg.appendChild(defs);

  for (let i = 0; i < 5; i++) {
    const y = PAD + (i * (H - 2 * PAD)) / 4;
    svg.appendChild(el("line", { x1: PAD, x2: W - PAD, y1: y, y2: y, stroke: "#e5e7eb", "stroke-width": "1" }));
  }

  const bandOuter = el("path", { d: band(2.1), fill: "rgba(157,78,221,0.12)" });
  bandOuter.style.cssText = "opacity:0;transition:opacity 1.1s ease 0.5s";
  const bandInner = el("path", { d: band(1), fill: "rgba(50,232,117,0.16)" });
  bandInner.style.cssText = "opacity:0;transition:opacity 1.1s ease 0.7s";
  svg.appendChild(bandOuter);
  svg.appendChild(bandInner);

  svg.appendChild(el("line", { x1: xs(HIST), x2: xs(HIST), y1: PAD, y2: H - PAD, stroke: "#c77dff", "stroke-width": "1.5", "stroke-dasharray": "4 4" }));
  svg.appendChild(el("path", { d: line(HIST + 1), fill: "none", stroke: "#3c096c", "stroke-width": "3", "stroke-linejoin": "round", "stroke-linecap": "round" }));

  const forecast = el("path", {
    d: line(N), fill: "none", stroke: "url(#pxg)", "stroke-width": "3",
    "stroke-dasharray": "700", "stroke-linejoin": "round", "stroke-linecap": "round",
  });
  forecast.style.cssText = "stroke-dashoffset:700;transition:stroke-dashoffset 2s ease";
  svg.appendChild(forecast);

  const dots = [];
  for (let i = 0; i < N; i += 5) {
    const c = el("circle", { cx: xs(i), cy: ys(pts[i]), r: "3.5", fill: "#5a189a" });
    c.style.cssText = `opacity:0;transition:opacity 0.4s ease ${0.8 + (i / 5) * 0.12}s`;
    dots.push(c);
    svg.appendChild(c);
  }

  container.appendChild(svg);

  // next frame, flip to the end state so the CSS transitions run
  const raf = requestAnimationFrame(() => {
    bandOuter.style.opacity = "1";
    bandInner.style.opacity = "1";
    forecast.style.strokeDashoffset = "0";
    dots.forEach((d) => { d.style.opacity = "1"; });
  });

  return () => { cancelAnimationFrame(raf); svg.remove(); };
}

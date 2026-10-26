// Prototype UI (UNVERIFIED: could not npm install/build offline). Covers: risk map + legend, ranking table, alerts with status updates.
import { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, ScaleControl } from "react-leaflet";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
const API = (import.meta as any).env?.VITE_API ?? "http://localhost:8000";
type Risk = { region_id: string; name: string; crop: string; score: number | null; band: string; ndvi_z: number | null; rain_deficit_pct: number | null; flood_pct: number; central_loss_inr: number; evidence_strength: string; completeness: number };
const BANDS: [string, string][] = [["low (<25)", "#2e7d32"], ["moderate (25-50)", "#f9a825"], ["high (50-75)", "#ef6c00"], ["critical (>=75)", "#b71c1c"], ["no data", "#9e9e9e"]];
const color = (b: string) => BANDS.find(([l]) => l.startsWith(b))?.[1] ?? "#9e9e9e";
const f = (v: number | null, d = 1) => (v == null ? "n/a" : v.toFixed(d));
export default function App() {
  const [regions, setRegions] = useState<any>(null), [risk, setRisk] = useState<Risk[]>([]), [alerts, setAlerts] = useState<any[]>([]), [sel, setSel] = useState<string | null>(null), [err, setErr] = useState("");
  const [m, setM] = useState<[number, number]>([6, 9]);
  const load = () => Promise.all([fetch(`${API}/regions`).then(r => r.json()), fetch(`${API}/risk?start_month=${m[0]}&end_month=${m[1]}`).then(r => r.json()), fetch(`${API}/alerts`).then(r => r.json())])
    .then(([a, b, c]) => { setRegions(a); setRisk(b); setAlerts(c); setErr(""); }).catch(e => setErr(String(e)));
  useEffect(() => { load(); }, [m]);
  const by = Object.fromEntries(risk.map(r => [r.region_id, r]));
  const setStatus = (id: string, status: string) => fetch(`${API}/alerts/${encodeURIComponent(id)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) }).then(load);
  if (err) return <p role="alert">Could not reach API: {err}</p>;
  if (!regions) return <p>Loading…</p>;
  const s = sel ? by[sel] : null;
  return <div style={{ fontFamily: "sans-serif", padding: 12 }}>
    <h2>EarthShield AI <small style={{ color: "#b71c1c" }}>— SIMULATED DATA · screening scores, not probabilities</small></h2>
    <label>Months {" "}<select value={m[0]} onChange={e => setM([+e.target.value, Math.max(+e.target.value, m[1])])}>{[...Array(12)].map((_, i) => <option key={i} value={i + 1}>{i + 1}</option>)}</select>–
      <select value={m[1]} onChange={e => setM([Math.min(m[0], +e.target.value), +e.target.value])}>{[...Array(12)].map((_, i) => <option key={i} value={i + 1}>{i + 1}</option>)}</select> of 2025</label>{" "}
    <a href={`${API}/export/risk.csv`}>Export CSV</a>
    <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
      <div style={{ flex: 2 }}>
        <MapContainer center={[16.9, 80.4]} zoom={7} style={{ height: 420 }}><TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="© OpenStreetMap contributors" /><ScaleControl />
          <GeoJSON key={JSON.stringify(risk.map(r => r.score))} data={regions} style={(ft: any) => ({ fillColor: color(by[ft.properties.region_id]?.band ?? "no data"), fillOpacity: .6, color: "#333", weight: ft.properties.region_id === sel ? 3 : 1 })}
            onEachFeature={(ft, l) => l.on("click", () => setSel(ft.properties.region_id))} /></MapContainer>
        <div>{BANDS.map(([l, c]) => <span key={l} style={{ marginRight: 10 }}><span style={{ background: c, display: "inline-block", width: 12, height: 12 }} /> {l}</span>)}</div>
        <p style={{ fontSize: 12 }}>Demo polygons are not official boundaries. Grey = no data (not low risk).</p>
      </div>
      <div style={{ flex: 1 }}>
        <h4>Ranking</h4>
        <ResponsiveContainer height={160}><BarChart data={risk}><XAxis dataKey="region_id" /><YAxis domain={[0, 100]} /><Tooltip /><Bar dataKey="score" fill="#ef6c00" /></BarChart></ResponsiveContainer>
        {s && <div><h4>{s.name}</h4><ul><li>Score {f(s.score)} ({s.band}), evidence: {s.evidence_strength}</li><li>NDVI z: {f(s.ndvi_z, 2)}</li><li>Rain deficit: {f(s.rain_deficit_pct)}%</li><li>Flood area: {f(s.flood_pct)}% (simulated)</li>
          <li>Central modeled loss: ₹{Math.round(s.central_loss_inr).toLocaleString("en-IN")} (modeled, not verified)</li><li>Completeness {Math.round(s.completeness * 100)}%</li></ul></div>}
      </div></div>
    <h4>Alerts</h4>
    <table border={1} cellPadding={4}><thead><tr><th>Region</th><th>Type</th><th>Severity</th><th>Evidence</th><th>Status</th></tr></thead><tbody>
      {alerts.length === 0 && <tr><td colSpan={5}>No alerts</td></tr>}
      {alerts.map(a => <tr key={a.id}><td>{a.region_id}</td><td>{a.type}</td><td>{a.severity}</td><td>{a.evidence}</td><td><select value={a.status} onChange={e => setStatus(a.id, e.target.value)}>{["Open", "Under review", "Resolved", "Dismissed"].map(x => <option key={x}>{x}</option>)}</select></td></tr>)}</tbody></table>
  </div>;
}

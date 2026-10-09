import { useEffect, useState } from 'react';
import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet';
import { Activity, AlertTriangle, ArrowUpRight, Camera, CircleHelp, Clock3, LocateFixed, LogOut, MapPin, ShieldAlert, Wrench } from 'lucide-react';
import { fetchCameraStatus, fetchCurrentOfficial, fetchEstimate, fetchIncidents, logoutOfficial } from './api.js';
import LoginPage from './LoginPage.jsx';

const roadLabels = {
  local: 'Local street',
  collector: 'Collector road',
  arterial: 'Arterial road',
  highway: 'Highway',
};

const currency = value => new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
}).format(value);

export default function App() {
  const [official, setOfficial] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    let active = true;
    fetchCurrentOfficial()
      .then(current => active && setOfficial(current))
      .catch(() => active && setOfficial(null))
      .finally(() => active && setCheckingSession(false));
    return () => { active = false; };
  }, []);

  async function signOut() {
    try {
      await logoutOfficial();
    } finally {
      setOfficial(null);
    }
  }

  if (checkingSession) {
    return <main className="session-loading">Loading secure workspace…</main>;
  }

  if (!official) {
    return <LoginPage onLogin={setOfficial} />;
  }

  return <Dashboard official={official} onLogout={signOut} />;
}

function Dashboard({ official, onLogout }) {
  const [incidents, setIncidents] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [cameraResult, setCameraResult] = useState(null);
  const [cameraLoading, setCameraLoading] = useState(false);
  const [area, setArea] = useState('');
  const [depth, setDepth] = useState('');
  const [roadClass, setRoadClass] = useState('arterial');
  const [estimate, setEstimate] = useState(null);
  const [estimateError, setEstimateError] = useState('');

  const selected = incidents.find(incident => incident.id === selectedId);

  useEffect(() => {
    let active = true;
    fetchIncidents()
      .then(items => {
        if (!active) return;
        setIncidents(items);
        if (items.length) {
          setSelectedId(items[0].id);
          setArea(String(items[0].area_m2));
          setDepth(String(items[0].depth_cm));
          setRoadClass(items[0].road_class);
        }
      })
      .catch(error => active && setLoadError(error.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selected || Number(area) <= 0 || Number(depth) < 0) return undefined;
    let active = true;
    const timer = window.setTimeout(() => {
      fetchEstimate({ area_m2: Number(area), depth_cm: Number(depth), road_class: roadClass })
        .then(value => active && (setEstimate(value), setEstimateError('')))
        .catch(error => active && setEstimateError(error.message));
    }, 180);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [selected, area, depth, roadClass]);

  function selectIncident(incident) {
    setSelectedId(incident.id);
    setArea(String(incident.area_m2));
    setDepth(String(incident.depth_cm));
    setRoadClass(incident.road_class);
    setCameraResult(null);
  }

  async function checkCamera() {
    if (!selected) return;
    setCameraLoading(true);
    setCameraResult(null);
    try {
      setCameraResult(await fetchCameraStatus(selected.id));
    } catch (error) {
      setCameraResult({ status: 'error', detail: error.message });
    } finally {
      setCameraLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="RoadSense home">
          <span className="brand-mark"><MapPin size={20} strokeWidth={2.5} /></span>
          <span>roadsense<span className="brand-dot">.</span></span>
        </a>
        <div className="topbar-context"><span className="status-light" /> Incident review <span className="context-divider">/</span> North Ward <span className="context-divider">/</span> {official.username}</div>
        <div className="topbar-actions"><button className="icon-button" type="button" title="Help" aria-label="Help"><CircleHelp size={19} /></button><button className="sign-out-button" onClick={onLogout} type="button"><LogOut size={15} /> Sign out</button></div>
      </header>

      <section className="page-heading" id="top">
        <div>
          <p className="eyebrow">Municipal operations · prototype</p>
          <h1>Incident review</h1>
          <p className="subheading">Verify detection evidence, understand road impact, and prepare a repair estimate.</p>
        </div>
        <div className="connection-state"><span className="connection-dot" /> Demo records <span className="connection-divider">·</span> Integrations offline</div>
      </section>

      {loadError && <div className="notice notice-error"><AlertTriangle size={17} /> API unavailable: {loadError}. Start the FastAPI service to load incidents.</div>}

      <section className="metric-row" aria-label="Incident summary">
        <div className="metric"><span>Open incidents</span><strong>{loading ? '—' : incidents.length.toString().padStart(2, '0')}</strong><small>Current sample queue</small></div>
        <div className="metric"><span>Needs camera review</span><strong>{incidents.length.toString().padStart(2, '0')}</strong><small>Camera adapter not configured</small></div>
        <div className="metric"><span>Repeat sightings</span><strong>{incidents.reduce((sum, item) => sum + Math.max(0, item.report_count - 1), 0).toString().padStart(2, '0')}</strong><small>Grouped demo reports</small></div>
        <div className="metric metric-note"><Activity size={19} /><span>Sample values only</span><small>No work orders are created</small></div>
      </section>

      <section className="workspace">
        <aside className="incident-rail">
          <div className="section-heading"><div><p className="eyebrow">Queue</p><h2>Detected locations</h2></div><span className="count-badge">{incidents.length}</span></div>
          {loading && <p className="empty-state">Loading incidents…</p>}
          {!loading && incidents.length === 0 && !loadError && <p className="empty-state">No incidents in the queue.</p>}
          <div className="incident-list">
            {incidents.map(incident => (
              <button className={`incident-item ${incident.id === selectedId ? 'is-selected' : ''}`} key={incident.id} onClick={() => selectIncident(incident)} type="button">
                <span className={`severity-mark ${incident.severity >= 0.85 ? 'severity-high' : 'severity-medium'}`} />
                <span className="incident-copy"><strong>{incident.road_name}</strong><small>{incident.id} · {roadLabels[incident.road_class]}</small><small>{incident.report_count} grouped reports</small></span>
                <ArrowUpRight size={16} className="incident-arrow" />
              </button>
            ))}
          </div>
          <div className="rail-note"><ShieldAlert size={17} /><p>Repeat sightings are retained as evidence on one incident, not counted as separate repair jobs.</p></div>
        </aside>

        <section className="map-panel" aria-label="Incident map">
          <div className="map-heading"><div><p className="eyebrow">Location context</p><h2>{selected?.road_name ?? 'Incident map'}</h2></div><span className="map-source"><LocateFixed size={15} /> OSM map · sample pins</span></div>
          {selected ? (
            <MapContainer center={[selected.latitude, selected.longitude]} zoom={14} scrollWheelZoom={false} className="leaflet-map" key={selected.id}>
              <TileLayer
                attribution='Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Sources: Esri, TomTom, Garmin, FAO, NOAA, USGS, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>, and the GIS User Community'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
              />
              {incidents.map(incident => (
                <CircleMarker center={[incident.latitude, incident.longitude]} key={incident.id} radius={incident.id === selected.id ? 10 : 7} pathOptions={{ color: incident.severity >= 0.85 ? '#d14e38' : '#e59a27', fillColor: incident.severity >= 0.85 ? '#d14e38' : '#e59a27', fillOpacity: 0.88, weight: 2 }}>
                  <Popup><strong>{incident.id}</strong><br />{incident.road_name}<br />Severity {(incident.severity * 100).toFixed(0)}%</Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          ) : <div className="map-placeholder">The map appears when the API returns an incident.</div>}
          {selected && <div className="coordinate-strip"><MapPin size={15} /><span>{selected.latitude.toFixed(4)}° N, {selected.longitude.toFixed(4)}° E</span><span className="coordinate-divider" /><span>{selected.detected_by === 'vision' ? 'Vision detection' : selected.detected_by === 'sensor' ? 'Sensor report' : 'Location only · method not supplied'}</span><span className="coordinate-confidence">{(selected.confidence * 100).toFixed(0)}% confidence</span></div>}
        </section>

        <aside className="review-panel">
          {selected ? <>
            <div className="section-heading"><div><p className="eyebrow">{selected.id}</p><h2>Evidence &amp; repair</h2></div><span className="open-tag">Open</span></div>
            <div className="severity-summary"><div><span>Detection severity</span><strong>{(selected.severity * 100).toFixed(0)}<small>/100</small></strong></div><span className="severity-pill"><AlertTriangle size={14} /> {selected.severity >= 0.85 ? 'High' : 'Review'}</span></div>

            <section className="review-block">
              <div className="block-title"><Camera size={17} /><h3>Camera confirmation</h3><span className="pending-tag">Not connected</span></div>
              <p>{cameraResult?.detail ?? 'Camera feed access is not configured. No camera has been queried for this location.'}</p>
              <button className="secondary-button" disabled={cameraLoading} onClick={checkCamera} type="button">{cameraLoading ? 'Checking…' : 'Check integration status'}</button>
            </section>

            <section className="review-block repeat-block">
              <div className="block-title"><Clock3 size={17} /><h3>Report history</h3><span className="sample-tag">Sample</span></div>
              <p><strong>{selected.report_count} reports</strong> grouped on this incident. Connect the report store to validate distance and time-window matches.</p>
            </section>

            <section className="estimate-block">
              <div className="block-title"><Wrench size={17} /><h3>Repair estimate</h3></div>
              <label className="field-label">Road class <span>Road-data adapter pending</span>
                <select value={roadClass} onChange={event => setRoadClass(event.target.value)}>
                  {Object.entries(roadLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </label>
              <div className="field-row">
                <label className="field-label">Area (m²)<input min="0.1" step="0.1" type="number" value={area} onChange={event => setArea(event.target.value)} /></label>
                <label className="field-label">Depth (cm)<input min="0" step="0.1" type="number" value={depth} onChange={event => setDepth(event.target.value)} /></label>
              </div>
              {estimate && <div className="estimate-result"><span>Illustrative range · INR</span><strong>{currency(estimate.low_inr)} – {currency(estimate.high_inr)}</strong><small>Midpoint {currency(estimate.midpoint_inr)} · sample rate card</small></div>}
              {estimateError && <p className="inline-error">Estimate unavailable: {estimateError}</p>}
              <p className="estimate-disclaimer">Estimate excludes a verified municipal rate card and requires field review. Road class affects the access allowance and public-impact context, not the detected damage itself.</p>
            </section>
          </> : <div className="empty-state">Select an incident to review its evidence and estimate.</div>}
        </aside>
      </section>
      <footer className="page-footer"><span>RoadSense prototype</span><span>Camera · report store · road data · approved rate card: not connected</span></footer>
    </main>
  );
}

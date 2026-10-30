import { useEffect, useMemo, useState } from 'react'
import MapView, { type Marker } from './MapView'

type Loc = { lat: number; lon: number }
type Biz = { business_id: string; business_name: string; category: string; business_address: string; zip: string; neighbourhood: string; location: Loc }
type Scan = Biz & { scan_timestamp: string; device_id: string; user_name: string; user_birth_year: number }
type Enc = { business_id: string; business_name: string; index_scan: string; contact_scan: string; gap_minutes: number }
type Contact = { device_id: string; user_name: string; encounters: Enc[]; encounter_count: number; min_gap_minutes: number; risk: 'high' | 'low' }
type Health = { elasticsearch: boolean; dataset: { mode: string; businesses: number; people: number; scans: number; generator: string } | null }

const j = (u: string) => fetch(u).then(async r => { const b = await r.json(); if (!r.ok) throw new Error(b.detail ?? r.statusText); return b })
const fmt = (s: string) => new Date(s).toLocaleString('en-US', { timeZone: 'America/Los_Angeles', weekday: 'short', hour: 'numeric', minute: '2-digit' })

function Trace() {
  const [devices, setDevices] = useState<{ device_id: string; user_name: string; scans: number }[]>([])
  const [dev, setDev] = useState('')
  const [win, setWin] = useState(30)
  const [scans, setScans] = useState<Scan[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [err, setErr] = useState('')
  const [input, setInput] = useState('')
  useEffect(() => { j('/api/devices?size=15').then(r => { setDevices(r.devices); setDev(r.devices[0]?.device_id ?? '') }) }, [])
  useEffect(() => {
    if (!dev) return
    setErr('')
    j(`/api/devices/${dev}/scans`).then(r => setScans(r.scans)).catch(e => { setErr(e.message); setScans([]); setContacts([]) })
    j(`/api/devices/${dev}/contacts?window_minutes=${win}`).then(r => setContacts(r.contacts)).catch(() => {})
  }, [dev, win])
  const exposed = useMemo(() => new Set(contacts.flatMap(c => c.encounters.map(e => e.business_id))), [contacts])
  const markers: Marker[] = scans.map((s, i) => ({ lat: s.location.lat, lon: s.location.lon, color: exposed.has(s.business_id) ? '#dc2626' : '#4f46e5',
    radius: exposed.has(s.business_id) ? 9 : 7, label: `${i + 1}. ${s.business_name} · ${fmt(s.scan_timestamp)}` }))
  const name = scans[0]?.user_name
  return (
    <>
      <section className="card controls">
        <label>Device <select value={dev} onChange={e => setDev(e.target.value)}>{devices.map(d => <option key={d.device_id} value={d.device_id}>{d.device_id} · {d.user_name} ({d.scans} scans)</option>)}</select></label>
        <form onSubmit={e => { e.preventDefault(); if (input.trim()) setDev(input.trim()) }}><input placeholder="or type a device ID" value={input} onChange={e => setInput(e.target.value)} /></form>
        <label>Contact window ± <input type="range" min={5} max={120} step={5} value={win} onChange={e => setWin(+e.target.value)} /> <b>{win} min</b></label>
      </section>
      {err && <div className="err">{err}</div>}
      <div className="cols2">
        <section className="card">
          <h3>Movement trace · {name} <span className="hint">{scans.length} scans, red = place with a contact</span></h3>
          <MapView markers={markers} path={scans.map(s => [s.location.lat, s.location.lon])} />
          <ol className="timeline">{scans.map((s, i) => <li key={i} className={exposed.has(s.business_id) ? 'hit' : ''}><b>{fmt(s.scan_timestamp)}</b> {s.business_name} <span className="hint">{s.neighbourhood}</span></li>)}</ol>
        </section>
        <section className="card">
          <h3>Contacts <span className="hint">same place within ±{win} min</span></h3>
          <div className="kpis"><div><b>{contacts.length}</b><span>contacts</span></div><div><b className="red">{contacts.filter(c => c.risk === 'high').length}</b><span>high risk (≤15 min or repeat)</span></div></div>
          <table><thead><tr><th>Device</th><th>Name</th><th>Encounters</th><th>Closest gap</th><th>Risk</th></tr></thead>
            <tbody>{contacts.slice(0, 40).map(c => <tr key={c.device_id} className="click" onClick={() => setDev(c.device_id)} title={c.encounters.map(e => `${e.business_name}: ${fmt(e.contact_scan)}`).join('\n')}>
              <td><code>{c.device_id}</code></td><td>{c.user_name}</td><td>{c.encounter_count} · {c.encounters[0].business_name}</td><td>{c.min_gap_minutes} min</td>
              <td><span className={`pill ${c.risk}`}>{c.risk}</span></td></tr>)}</tbody></table>
          <div className="hint">Click a contact to trace them next.</div>
        </section>
      </div>
    </>
  )
}

function Businesses() {
  const [q, setQ] = useState('Cafe')
  const [zip, setZip] = useState('')
  const [list, setList] = useState<Biz[]>([])
  const [total, setTotal] = useState(0)
  const [sel, setSel] = useState<Biz | null>(null)
  const [visitors, setVisitors] = useState<Scan[]>([])
  const search = () => j(`/api/businesses?size=200${q ? `&q=${encodeURIComponent(q)}` : ''}${zip ? `&zip=${zip}` : ''}`).then(r => { setList(r.businesses); setTotal(r.total) })
  useEffect(() => { search() }, [])  // eslint-disable-line
  const pick = (b: Biz) => { setSel(b); j(`/api/businesses/${b.business_id}/scans`).then(r => setVisitors(r.scans)).catch(() => setVisitors([])) }
  const markers: Marker[] = list.map(b => ({ lat: b.location.lat, lon: b.location.lon, label: `${b.business_name} (${b.business_id})`,
    color: sel?.business_id === b.business_id ? '#dc2626' : '#0891b2', onClick: () => pick(b) }))
  return (
    <>
      <form className="card controls" onSubmit={e => { e.preventDefault(); search() }}>
        <label>Free text <input value={q} onChange={e => setQ(e.target.value)} placeholder="name, category, street…" /></label>
        <label>Zip <input value={zip} onChange={e => setZip(e.target.value)} placeholder="94110" style={{ width: 90 }} /></label>
        <button>Search</button><span className="hint">{total} matching businesses</span>
      </form>
      <div className="cols2">
        <section className="card"><MapView markers={markers} /><div className="hint">Click a marker to see who scanned in.</div></section>
        <section className="card">
          {sel ? <><h3>{sel.business_name} <span className="hint">{sel.business_id} · {sel.business_address}, {sel.zip}</span></h3>
            <table><thead><tr><th>Scan time (PT)</th><th>Device</th><th>Name</th><th>Born</th></tr></thead>
              <tbody>{visitors.map((v, i) => <tr key={i}><td>{fmt(v.scan_timestamp)}</td><td><code>{v.device_id}</code></td><td>{v.user_name}</td><td>{v.user_birth_year}</td></tr>)}</tbody></table></>
            : <table><thead><tr><th>ID</th><th>Business</th><th>Neighbourhood</th><th>Zip</th></tr></thead>
              <tbody>{list.slice(0, 25).map(b => <tr key={b.business_id} className="click" onClick={() => pick(b)}><td>{b.business_id}</td><td>{b.business_name}</td><td>{b.neighbourhood}</td><td>{b.zip}</td></tr>)}</tbody></table>}
        </section>
      </div>
    </>
  )
}

function Overview() {
  const [s, setS] = useState<{ scans: number; devices: number; by_neighbourhood: { name: string; scans: number }[]; per_hour: { t: string; scans: number }[] } | null>(null)
  useEffect(() => { j('/api/stats').then(setS) }, [])
  if (!s) return null
  const max = Math.max(...s.by_neighbourhood.map(b => b.scans)), hmax = Math.max(...s.per_hour.map(h => h.scans))
  return (
    <div className="cols2">
      <section className="card"><h3>Scans by neighbourhood</h3>
        {s.by_neighbourhood.map(b => <div key={b.name} className="bar"><span>{b.name}</span><div style={{ width: `${b.scans / max * 100}%` }} /><b>{b.scans}</b></div>)}</section>
      <section className="card"><h3>Scans per hour <span className="hint">{s.scans} scans · {s.devices} devices</span></h3>
        <div className="hist">{s.per_hour.map(h => <div key={h.t} title={`${fmt(h.t)}: ${h.scans}`} style={{ height: `${h.scans / hmax * 100}%` }} />)}</div></section>
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState<'trace' | 'biz' | 'stats'>('trace')
  const [h, setH] = useState<Health | null>(null)
  useEffect(() => { j('/health').then(setH).catch(() => {}) }, [])
  return (
    <div className="page">
      <header>
        <div><h1>🧬 SF App-Scan Contact Tracer</h1><div className="hint">Elasticsearch geo + time-window queries · FastAPI · React</div></div>
        <div className="badges">
          <span className={`badge ${h?.elasticsearch ? 'ok' : 'bad'}`}>Elasticsearch {h?.elasticsearch ? 'up' : 'down'}</span>
          {h?.dataset && <span className="badge warn">SYNTHETIC: {h.dataset.businesses} businesses · {h.dataset.people} people · {h.dataset.scans} scans</span>}
        </div>
      </header>
      <div className="banner">All people, device IDs, businesses and scans are <b>synthetic</b> ({h?.dataset?.generator ?? 'Faker'}). No real personal or business data is used.</div>
      <nav>{([['trace', 'Trace a device'], ['biz', 'Businesses'], ['stats', 'Overview']] as const).map(([k, l]) =>
        <button key={k} className={tab === k ? 'active' : ''} onClick={() => setTab(k)}>{l}</button>)}</nav>
      {tab === 'trace' ? <Trace /> : tab === 'biz' ? <Businesses /> : <Overview />}
    </div>
  )
}

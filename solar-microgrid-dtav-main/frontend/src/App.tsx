import { useState, useEffect } from "react";
import {
  Sun,
  BatteryCharging,
  Zap,
  Radio,
  Activity,
  LayoutDashboard,
  PanelsTopLeft,
  FlaskConical,
  AlertTriangle,
  Download,
  Moon,
  Menu,
  Power,
  ArrowUpRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  Legend,
} from "recharts";
import { State, fmt } from "./types";
const tabs = [
  "Overview",
  "Solar array",
  "Battery",
  "Loads",
  "Digital twin",
  "Research",
  "Fault log",
];
const icons = [
  LayoutDashboard,
  Sun,
  BatteryCharging,
  Zap,
  PanelsTopLeft,
  FlaskConical,
  AlertTriangle,
];
async function api(path: string, data?: unknown) {
  const r = await fetch(
    "/api/" + path,
    data
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      : undefined,
  );
  if (!r.ok) {
    let msg = await r.text();
    try {
      msg = JSON.parse(msg).detail;
    } catch {}
    throw new Error(String(msg));
  }
  return r.json();
}
export default function App() {
  const [s, setS] = useState<State>({}),
    [tab, setTab] = useState("Overview"),
    [history, setHistory] = useState<State[]>([]),
    [online, setOnline] = useState(false),
    [error, setError] = useState(""),
    [mode, setMode] = useState("simulation"),
    [strategy, setStrategy] = useState("dtav"),
    [dark, setDark] = useState(true),
    [menu, setMenu] = useState(false),
    [events, setEvents] = useState<Record<string, unknown>[]>([]),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    let ws: WebSocket | undefined,
      timer: ReturnType<typeof setTimeout>,
      alive = true;
    function connect() {
      ws = new WebSocket(
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
      );
      ws.onopen = () => setOnline(true);
      ws.onmessage = (e) => {
        const next: State = JSON.parse(e.data);
        setS(next);
        setHistory((h) =>
          [...h.filter((x) => x.generation === next.generation), next].slice(
            -180,
          ),
        );
      };
      ws.onclose = () => {
        setOnline(false);
        if (alive) timer = setTimeout(connect, 2000);
      };
    }
    connect();
    return () => {
      alive = false;
      clearTimeout(timer);
      ws?.close();
    };
  }, []);
  useEffect(() => {
    if (tab === "Fault log")
      api("events")
        .then(setEvents)
        .catch((e) => setError(e.message));
  }, [tab]);
  async function action(path: string, data: unknown) {
    setBusy(true);
    setError("");
    try {
      await api(path, data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function command(kind: string, target: number, value: number) {
    if (
      !window.confirm(
        `Confirm ${kind} command: target ${target + 1}, value ${value}. The controller will apply safety checks.`,
      )
    )
      return;
    await action("command", { kind, target, value, confirmed: true });
  }
  const disabled = !online || busy || s.mode === "replay" || s.stale;
  const flow =
    s.source === "solar" ? "solar" : s.source === "battery" ? "battery" : "off";
  return (
    <div className={dark ? "app dark" : "app light"}>
      <aside className={menu ? "open" : ""}>
        <div className="brand">
          <div className="brand-icon">
            <Sun size={25} />
          </div>
          <span>
            helio<span className="brand-dot">.</span>
            <small>MICROGRID LAB</small>
          </span>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          {tabs.map((name, i) => {
            const Icon = icons[i];
            return (
              <button
                key={name}
                className={tab === name ? "active" : ""}
                onClick={() => {
                  setTab(name);
                  setMenu(false);
                }}
              >
                <Icon size={18} />
                {name}
                {name === "Fault log" && !!s.faults?.length && (
                  <b>{s.faults.length}</b>
                )}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="node-status">
            <span className={online ? "dot" : "dot red"} />
            <div>
              Local laboratory
              <small>
                {online ? "Backend connected" : "Backend disconnected"}
              </small>
            </div>
          </div>
          <p>
            2 × 2 ARRAY · 1S STORAGE
            <br />
            DECISION-AWARE SENSING
          </p>
          <button onClick={() => setDark(!dark)}>
            <Moon size={16} /> {dark ? "Light" : "Dark"} appearance
          </button>
        </div>
      </aside>
      <main>
        <header>
          <div className="breadcrumbs">
            <button
              className="mobile-menu"
              onClick={() => setMenu(!menu)}
              aria-label="Toggle menu"
            >
              <Menu />
            </button>
            Workspace <span>/</span> <strong>{tab}</strong>
          </div>
          <div className="header-right">
            <span className={`connection ${online ? "" : "offline"}`}>
              <i />
              {online ? "LIVE CONNECTION" : "DISCONNECTED"}
            </span>
            <a href="/api/export.csv" className="export">
              <Download size={15} />
              Export data
            </a>
          </div>
        </header>
        <section className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">AUTONOMOUS SOLAR MICROGRID</div>
              <h1>{tab === "Overview" ? "Your energy, in balance." : tab}</h1>
              <p>
                {tab === "Overview"
                  ? "A live view of generation, storage and intelligent distribution."
                  : "Inspect system behaviour and verified controller responses."}
              </p>
            </div>
            <div className="mode-controls">
              <label>
                Operating mode
                <select
                  value={mode}
                  disabled={busy}
                  onChange={(e) => {
                    const m = e.target.value;
                    setMode(m);
                    action("settings", { mode: m, strategy });
                  }}
                >
                  <option value="simulation">Simulation</option>
                  <option value="hardware">Hardware</option>
                  <option value="replay">Historical replay</option>
                </select>
              </label>
              <span className="sim-badge">
                {s.provenance ?? "WAITING FOR DATA"}
              </span>
            </div>
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
              <button onClick={() => setError("")}>Dismiss</button>
            </div>
          )}
          {(!online || s.stale) && (
            <div className="error">
              {online
                ? "Controller data is stale. Controls are disabled."
                : "Waiting for the local backend. No device data is available."}
            </div>
          )}
          {tab === "Overview" && (
            <>
              <div className="metrics">
                <Metric
                  icon={Sun}
                  title="Solar generation"
                  value={fmt(s.solar_w, " W")}
                  sub="Four panels · two clusters"
                  color="amber"
                />
                <Metric
                  icon={BatteryCharging}
                  title="Battery reserve"
                  value={fmt(
                    s.soc === undefined ? undefined : s.soc * 100,
                    "%",
                    0,
                  )}
                  sub={`${fmt(s.battery_v, " V", 2)} · ${fmt(s.battery_a, " A", 2)}`}
                  color="mint"
                />
                <Metric
                  icon={Zap}
                  title="Active consumption"
                  value={fmt(s.load_w, " W")}
                  sub={`${s.loads?.filter(Boolean).length ?? 0} of 3 loads online`}
                  color="blue"
                />
                <Metric
                  icon={Activity}
                  title="Distribution bus"
                  value={fmt(s.bus_v, " V")}
                  sub={`${s.source ?? "Unknown"} source · ${s.state ?? "Waiting"}`}
                  color="purple"
                />
              </div>
              <div className="overview-grid">
                <article className="card energy">
                  <CardHead title="Energy flow" subtitle="Live system topology">
                    <span className="pill">
                      <span className="dot" />
                      {s.source ?? "OFF"} SOURCE
                    </span>
                  </CardHead>
                  <div className="flow-layout">
                    <div className="array-group">
                      <div className="array-caption">
                        SOLAR ARRAY <span>2 × 2</span>
                      </div>
                      <div className="panel-grid">
                        {[0, 1, 2, 3].map((i) => (
                          <button
                            key={i}
                            onClick={() => setTab("Solar array")}
                            className={`pv-panel ${s.isolated?.[i] ? "isolated" : ""}`}
                          >
                            <div className="pv-cells" />
                            <div className="pv-label">
                              <span>PV0{i + 1}</span>
                              <strong>{fmt(s.pv?.[i], " W")}</strong>
                            </div>
                            <i className={s.isolated?.[i] ? "red" : ""} />
                          </button>
                        ))}
                      </div>
                      <div className="cluster-labels">
                        <span>CLUSTER A</span>
                        <span>CLUSTER B</span>
                      </div>
                    </div>
                    <div className="flow-link">
                      <div
                        className={flow === "solar" ? "wire active" : "wire"}
                      />
                      <small>COMBINER</small>
                      <ArrowUpRight size={18} />
                    </div>
                    <div className="converter-stack">
                      <div
                        className={`flow-box ${flow === "solar" ? "energized" : ""}`}
                      >
                        <Sun size={23} />
                        <strong>Solar 12 V</strong>
                        <small>REGULATED SOURCE</small>
                      </div>
                      <div
                        className={`flow-box ${flow === "battery" ? "energized" : ""}`}
                      >
                        <BatteryCharging size={23} />
                        <strong>
                          {fmt(
                            s.soc === undefined ? undefined : s.soc * 100,
                            "%",
                            0,
                          )}
                        </strong>
                        <small>1S LIPO · BOOST 12 V</small>
                      </div>
                    </div>
                    <div className="flow-link">
                      <div
                        className={flow !== "off" ? "wire active" : "wire"}
                      />
                      <small>TRANSFER</small>
                    </div>
                    <div className="bus-loads">
                      <div className="bus-title">
                        12 V BUS <span>{fmt(s.load_w, " W")}</span>
                      </div>
                      {["Critical light", "Ventilation", "Auxiliary light"].map(
                        (name, i) => (
                          <div
                            key={name}
                            className={`load-mini ${s.loads?.[i] ? "on" : ""}`}
                          >
                            <Zap size={16} />
                            <div>
                              {name}
                              <small>PRIORITY 0{i + 1}</small>
                            </div>
                            <span
                              className={s.loads?.[i] ? "dot" : "dot gray"}
                            />
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                  <footer className="card-footer">
                    <span>
                      <i className="dot" /> Active path
                    </span>
                    <span>
                      <i className="dot gray" /> Standby
                    </span>
                    <span>PV allocation: {s.allocation ?? "unknown"}</span>
                  </footer>
                </article>
                <article className="card sensing">
                  <CardHead
                    title="Sensing intelligence"
                    subtitle="Decision-triggered active verification"
                  />
                  <div className="dtav-orbit">
                    <Radio size={32} />
                    <span>DTAV</span>
                  </div>
                  <div className="savings">
                    <strong>
                      {fmt(
                        s.research
                          ? 100 * s.research.communication_savings
                          : undefined,
                        "%",
                        0,
                      )}
                    </strong>
                    <span>
                      fewer optional reports
                      <br />
                      against one report per simulation tick
                    </span>
                  </div>
                  <div className="detail-row">
                    <span>Verification requests</span>
                    <strong>{s.research?.requests ?? "—"}</strong>
                  </div>
                  <div className="detail-row">
                    <span>Expected information value</span>
                    <strong>{fmt(s.research?.evsi, "", 3)}</strong>
                  </div>
                  <button
                    className="text-link"
                    onClick={() => setTab("Research")}
                  >
                    Explore decision history <ArrowUpRight size={15} />
                  </button>
                </article>
              </div>
              <article className="card trends">
                <CardHead
                  title="Power over time"
                  subtitle="Generation and demand · latest 180 samples"
                >
                  <span className="legend">
                    <i />
                    Solar generation <i />
                    Load demand
                  </span>
                </CardHead>
                <PowerChart data={history} />
              </article>
            </>
          )}
          {tab === "Solar array" && (
            <>
              <div className="metrics">
                {[0, 1, 2, 3].map((i) => (
                  <Metric
                    key={i}
                    icon={Sun}
                    title={`Panel ${i + 1}`}
                    value={fmt(s.pv?.[i], " W")}
                    sub={s.isolated?.[i] ? "Isolated" : "Connected"}
                    color="amber"
                  />
                ))}
              </div>
              <div className="two-col">
                {[0, 1].map((i) => (
                  <article className="card padded" key={i}>
                    <h2>Cluster {i ? "B" : "A"}</h2>
                    {Object.entries(s.clusters?.[i] ?? {}).map(([k, v]) => (
                      <div className="detail-row" key={k}>
                        <span>{k}</span>
                        <strong>{fmt(v)}</strong>
                      </div>
                    ))}
                  </article>
                ))}
              </div>
              <article className="card padded">
                <h2>Individual panel isolation</h2>
                <p>
                  Recovery is permitted only by local policy; latched electrical
                  faults require inspection.
                </p>
                <div className="button-row">
                  {[0, 1, 2, 3].map((i) => (
                    <button
                      disabled={disabled}
                      onClick={() =>
                        command("panel", i, s.isolated?.[i] ? 0 : 1)
                      }
                      key={i}
                    >
                      PV{i + 1}:{" "}
                      {s.isolated?.[i] ? "Request reconnect" : "Isolate"}
                    </button>
                  ))}
                </div>
              </article>
              <article className="card trends">
                <CardHead
                  title="Solar power"
                  subtitle="Provenance shown in operating mode"
                />
                <PowerChart data={history} />
              </article>
            </>
          )}
          {tab === "Battery" && (
            <>
              <div className="metrics">
                <Metric
                  icon={BatteryCharging}
                  title="State of charge estimate"
                  value={fmt(
                    s.soc === undefined ? undefined : s.soc * 100,
                    "%",
                    0,
                  )}
                  sub="Current integration + model"
                  color="mint"
                />
                <Metric
                  icon={Zap}
                  title="Pack voltage"
                  value={fmt(s.battery_v, " V", 3)}
                  sub="1S protected LiPo"
                  color="amber"
                />
                <Metric
                  icon={Activity}
                  title="Signed pack current"
                  value={fmt(s.battery_a, " A", 3)}
                  sub="Positive = discharging"
                  color="blue"
                />
                <Metric
                  icon={BatteryCharging}
                  title="Predicted runtime"
                  value={fmt(s.runtime_h, " h", 2)}
                  sub="Model estimate at present load"
                  color="purple"
                />
              </div>
              <article className="card trends">
                <CardHead title="Storage history" subtitle="SOC estimate (%)" />
                <div className="padded">
                  <p>
                    Shared PV bus · MPPT{" "}
                    {s.charge_inhibited === undefined
                      ? "status unknown"
                      : s.charge_inhibited
                        ? "inhibited during recovery or transfer"
                        : "permitted; actual charging follows surplus and CC/CV"}{" "}
                    · {fmt(s.pv_bus_v, " V", 2)}
                  </p>
                  <p>
                    Modelled charge power: {fmt(s.charge_w, " W")} · Net battery
                    current remains signed.
                  </p>
                </div>
                <ResponsiveContainer width="100%" height={290}>
                  <AreaChart
                    data={history.map((x) => ({
                      ...x,
                      soc_pct: (x.soc ?? 0) * 100,
                    }))}
                  >
                    <CartesianGrid
                      strokeDasharray="3 6"
                      stroke="var(--border)"
                    />
                    <XAxis dataKey="time" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Area dataKey="soc_pct" stroke="#6fe3bc" fill="#6fe3bc25" />
                  </AreaChart>
                </ResponsiveContainer>
              </article>
            </>
          )}
          {tab === "Loads" && (
            <>
              <div className="load-cards">
                {[
                  "Critical lighting",
                  "Ventilation fan",
                  "Auxiliary lighting",
                ].map((name, i) => (
                  <article className="card padded" key={name}>
                    <div className="eyebrow">PRIORITY {i + 1}</div>
                    <h2>{name}</h2>
                    <div className="big-value">
                      {fmt(s.load_powers?.[i], " W")}
                    </div>
                    <p>
                      {fmt(s.load_voltages?.[i], " V", 2)} ·{" "}
                      {fmt(s.load_currents?.[i], " A", 3)}
                    </p>
                    <p>{s.loads?.[i] ? "Operating" : "Disconnected"}</p>
                    <button
                      disabled={disabled}
                      onClick={() => command("load", i, s.loads?.[i] ? 0 : 1)}
                    >
                      <Power size={16} />
                      {s.loads?.[i] ? "Disconnect" : "Request restoration"}
                    </button>
                  </article>
                ))}
              </div>
              <article className="card padded">
                <h2>Source management</h2>
                <p>
                  Break-before-make transfer. Manual requests remain subject to
                  source availability, reserve and local protection.
                </p>
                <div className="button-row">
                  <button
                    disabled={disabled}
                    onClick={() => command("source", 0, 1)}
                  >
                    Request solar
                  </button>
                  <button
                    disabled={disabled}
                    onClick={() => command("source", 0, 2)}
                  >
                    Request battery
                  </button>
                  <button
                    disabled={disabled}
                    onClick={() => command("source", 0, 0)}
                  >
                    Safe shutdown
                  </button>
                  <button
                    disabled={disabled}
                    onClick={() =>
                      action("command", { kind: "auto", confirmed: true })
                    }
                  >
                    Return to automatic
                  </button>
                </div>
              </article>
            </>
          )}
          {tab === "Digital twin" && (
            <>
              <div className="metrics">
                <Metric
                  icon={Sun}
                  title="Solar available"
                  value={fmt(s.solar_available_w, " W")}
                  sub="After converter loss"
                  color="amber"
                />
                <Metric
                  icon={Activity}
                  title="Estimated losses"
                  value={fmt(s.loss_w, " W")}
                  sub="Includes curtailed PV potential"
                  color="purple"
                />
                <Metric
                  icon={Zap}
                  title="Unserved energy"
                  value={fmt(s.unserved_wh, " Wh", 3)}
                  sub="Against all three loads requested"
                  color="blue"
                />
                <Metric
                  icon={FlaskConical}
                  title="Estimator error"
                  value={fmt(s.research?.model_error_w, " W", 2)}
                  sub="Simulation truth comparison only"
                  color="mint"
                />
              </div>
              <article className="card trends">
                <CardHead
                  title="Truth and supervisory estimate"
                  subtitle="Simulation/replay values are never hardware measurements"
                />
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart
                    data={history.map((x) => ({
                      ...x,
                      estimate: x.research?.estimate,
                    }))}
                  >
                    <CartesianGrid stroke="var(--border)" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      dataKey="solar_available_w"
                      stroke="#f5bd5e"
                      dot={false}
                    />
                    <Line dataKey="estimate" stroke="#6fe3bc" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </article>
              <article className="card padded">
                <h2>Scenario laboratory</h2>
                <p>
                  Fault injection is available exclusively in simulation mode.
                </p>
                <div className="button-row">
                  {[
                    "shade",
                    "disconnect",
                    "reverse",
                    "lora_loss",
                    "restore",
                  ].map((kind) => (
                    <button
                      key={kind}
                      disabled={disabled || s.mode !== "simulation"}
                      onClick={() =>
                        action("inject", { kind, panel: 0, severity: 0.9 })
                      }
                    >
                      {kind.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </article>
            </>
          )}
          {tab === "Research" && (
            <>
              <article className="card padded">
                <h2>Decision value of fresh information</h2>
                <p>
                  EVSI compares the best action under the prior with expected
                  loss after a fresh observation. Requests are justified when
                  information can change an action and expected benefit exceeds
                  communication cost.
                </p>
                <label>
                  Sensing strategy{" "}
                  <select
                    value={strategy}
                    disabled={busy}
                    onChange={(e) => {
                      setStrategy(e.target.value);
                      action("settings", { mode, strategy: e.target.value });
                    }}
                  >
                    {["continuous", "periodic", "event", "dtav"].map((x) => (
                      <option key={x}>{x}</option>
                    ))}
                  </select>
                </label>
              </article>
              <div className="metrics">
                <Metric
                  icon={Radio}
                  title="Reports"
                  value={String(s.research?.reports ?? "—")}
                  sub="Optional long-range telemetry"
                  color="blue"
                />
                <Metric
                  icon={FlaskConical}
                  title="EVSI"
                  value={fmt(s.research?.evsi, "", 3)}
                  sub={`Communication cost ${fmt(s.research?.cost, "", 2)}`}
                  color="mint"
                />
                <Metric
                  icon={Activity}
                  title="Uncertainty"
                  value={fmt(s.research?.sigma, " W", 2)}
                  sub="Quadrature model standard deviation"
                  color="purple"
                />
                <Metric
                  icon={Radio}
                  title="Sample age"
                  value={fmt(s.research?.age_s, " s", 0)}
                  sub={
                    s.research?.request
                      ? "Verification useful"
                      : "No decision-value request"
                  }
                  color="amber"
                />
              </div>
              <article className="card padded">
                <h2>Repeatable comparisons</h2>
                <p>
                  Run{" "}
                  <code>
                    python scripts/experiment.py --seeds 5 --seconds 300
                  </code>{" "}
                  for paired scenarios, CSV records and summary statistics.
                  Displayed communication savings describe this simulation
                  session; no hardware performance improvement is claimed.
                </p>
              </article>
            </>
          )}
          {tab === "Fault log" && (
            <article className="card padded">
              <h2>Faults & operator activity</h2>
              {s.faults?.map((f) => (
                <div className="error" key={f.panel}>
                  PV{f.panel + 1}: {f.type} ·{" "}
                  {f.isolated ? "isolated" : "connected"}
                </div>
              ))}
              {!events.length ? (
                <p>No recorded events.</p>
              ) : (
                events.map((e, i) => (
                  <div className="event" key={i}>
                    <span>{String(e.type)}</span>
                    <code>{JSON.stringify(e)}</code>
                  </div>
                ))
              )}
            </article>
          )}
          <div className="bottom-note">
            <span>
              <span className="dot" /> Local protection remains independent of
              the digital twin
            </span>
            <span>HELIO / DTAV LAB · {s.provenance ?? "NO DATA"}</span>
          </div>
        </section>
      </main>
    </div>
  );
}
function Metric({
  icon: Icon,
  title,
  value,
  sub,
  color,
}: {
  icon: typeof Sun;
  title: string;
  value: string;
  sub: string;
  color: string;
}) {
  return (
    <article className="card metric">
      <div className="metric-top">
        <span>{title}</span>
        <div className={"metric-icon " + color}>
          <Icon size={19} />
        </div>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-sub">{sub}</div>
    </article>
  );
}
function CardHead({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="card-head">
      <div>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
      {children}
    </div>
  );
}
function PowerChart({ data }: { data: State[] }) {
  return (
    <ResponsiveContainer width="100%" height={235}>
      <AreaChart
        data={data}
        margin={{ top: 10, right: 24, bottom: 4, left: 0 }}
      >
        <defs>
          <linearGradient id="solarFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#edb959" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#edb959" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="2 7"
          vertical={false}
          stroke="var(--border)"
        />
        <XAxis
          dataKey="time"
          tickLine={false}
          axisLine={false}
          tick={{ fill: "#7b8a95", fontSize: 11 }}
          minTickGap={45}
          unit="s"
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tick={{ fill: "#7b8a95", fontSize: 11 }}
          unit="W"
          width={50}
        />
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 10,
          }}
        />
        <Area
          type="monotone"
          dataKey="solar_w"
          stroke="#edb959"
          strokeWidth={2}
          fill="url(#solarFill)"
          name="Solar"
          isAnimationActive={false}
        />
        <Area
          type="stepAfter"
          dataKey="load_w"
          stroke="#70dfb8"
          strokeWidth={2}
          fill="transparent"
          name="Load"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

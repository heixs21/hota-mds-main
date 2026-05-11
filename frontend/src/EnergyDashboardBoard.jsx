import { useCallback, useEffect, useMemo, useState } from "react";

import { useScreenCarouselPageActive } from "./screenCarouselContext.jsx";

function buildApiUrl(pathname) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
  return `${baseUrl}${pathname}`;
}

function formatNum(v) {
  const n = parseFloat(v);
  if (Number.isNaN(n)) return "—";
  if (Math.abs(n) >= 10000) return `${(n / 10000).toFixed(2)} 万`;
  return n.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function postEnergyDashboard(body) {
  const res = await fetch(buildApiUrl("/api/energy-dashboard"), {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.success === false) {
    throw new Error(json.message || `请求失败 (${res.status})`);
  }
  return json.data ?? json;
}

function todayISO() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function daysAgoISO(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

/** 最近 8 小时（含跨日时钟），仅当日 hourlySeries 有值的时段取数，其余为 0 */
function buildLast8HourPoints(series) {
  const ch = new Date().getHours();
  const map = new Map((series ?? []).map((s) => [Number(s.hour), parseFloat(s.kwh) || 0]));
  const pts = [];
  for (let k = ch - 7; k <= ch; k++) {
    const hourClock = ((k % 24) + 24) % 24;
    const kwh = k >= 0 && k < 24 ? map.get(k) ?? 0 : 0;
    pts.push({
      key: `h-${k}`,
      xLabel: `${hourClock}时`,
      kwh,
    });
  }
  return pts;
}

function buildLast7DayPoints(dayTrend) {
  const sorted = [...(dayTrend ?? [])].sort((a, b) => String(a.date).localeCompare(String(b.date)));
  return sorted.slice(-7).map((p, i) => ({
    key: `d-${p.date}-${i}`,
    xLabel: String(p.date).slice(5),
    kwh: parseFloat(p.kwh) || 0,
  }));
}

function buildLast6MonthPoints(monthTrend) {
  const sorted = [...(monthTrend ?? [])].sort((a, b) => String(a.month).localeCompare(String(b.month)));
  return sorted.slice(-6).map((p, i) => ({
    key: `m-${p.month}-${i}`,
    xLabel: String(p.month ?? "").replace(/-/g, "/"),
    kwh: parseFloat(p.kwh) || 0,
  }));
}

/** 柱顶数值略缩短，避免挤压 */
function formatBarTop(v) {
  const n = parseFloat(v);
  if (Number.isNaN(n)) return "—";
  if (Math.abs(n) >= 10000) return `${(n / 10000).toFixed(2)}万`;
  if (Math.abs(n) >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return n.toLocaleString("zh-CN", { minimumFractionDigits: 0, maximumFractionDigits: 1 });
}

/** variant: hour 青蓝 / day 紫 / month 琥珀 */
function UnifiedEnergyBarChart({ points, variant = "hour" }) {
  const list = points ?? [];
  if (!list.length) {
    return (
      <div className="edb-unified-bars edb-unified-bars--empty">
        <div className="edb-empty small">暂无数据</div>
      </div>
    );
  }
  const vals = list.map((p) => p.kwh);
  const max = Math.max(...vals, 1);
  return (
    <div className="edb-unified-bars">
      {list.map((p) => {
        const h = Math.max((p.kwh / max) * 100, p.kwh > 0 ? 4 : 2);
        return (
          <div className="edb-unified-col" key={p.key}>
            <span className="edb-unified-val">{formatBarTop(p.kwh)}</span>
            <div className="edb-unified-bar-track">
              <div
                className={`edb-unified-bar edb-unified-bar--${variant}`}
                style={{ height: `${h}%` }}
                title={`${p.kwh}`}
              />
            </div>
            <span className="edb-unified-x">{p.xLabel}</span>
          </div>
        );
      })}
    </div>
  );
}

function DonutChart({ slices }) {
  const total = (slices ?? []).reduce((a, s) => a + parseFloat(s.kwh || 0), 0);
  let acc = 0;
  const segs = (slices ?? []).map((s) => {
    const pct = total > 0 ? (parseFloat(s.kwh) / total) * 100 : 0;
    const start = acc;
    acc += pct;
    return { ...s, start, end: acc, pct };
  });
  const gradient =
    segs.length === 0
      ? "rgba(100,116,139,0.35) 0% 100%"
      : segs.map((s) => `${s.color} ${s.start}% ${s.end}%`).join(", ");

  return (
    <div className="edb-donut-wrap">
      <div className="edb-donut" style={{ background: `conic-gradient(${gradient})` }}>
        <div className="edb-donut-hole">
          <span className="edb-donut-total">{formatNum(total)}</span>
          <span className="edb-donut-unit">kWh</span>
        </div>
      </div>
      <ul className="edb-donut-legend">
        {(slices ?? []).map((s) => (
          <li key={s.id}>
            <span className="edb-leg-dot" style={{ background: s.color }} />
            <span>{s.label}</span>
            <strong>{formatNum(s.kwh)}</strong>
            <em>{s.percent?.toFixed?.(1) ?? "0"}%</em>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function EnergyDashboardBoard({ bootstrap }) {
  const carouselPageActive = useScreenCarouselPageActive();
  const dataSourceIds = bootstrap?.dataSourceIds ?? [];
  const bootErr = bootstrap?.errorMessage;
  const equipmentIdsConfigured = bootstrap?.energyEquipmentIds ?? [];

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(bootErr || null);
  const [dash, setDash] = useState(null);

  /** 与后台数据源「轮询间隔」一致（秒→毫秒），仅使用大屏载荷下发的值，不写死默认秒数 */
  const pollIntervalMs = useMemo(() => {
    const s = bootstrap?.refreshIntervalSeconds;
    if (typeof s === "number" && Number.isFinite(s) && s > 0) {
      return Math.max(5000, s * 1000);
    }
    return null;
  }, [bootstrap?.refreshIntervalSeconds]);

  const equipmentKey = useMemo(() => JSON.stringify(equipmentIdsConfigured), [equipmentIdsConfigured]);

  const bodyBase = useMemo(
    () => ({
      dataSourceIds,
      dateFrom: daysAgoISO(6),
      dateTo: todayISO(),
      equipmentIds: equipmentIdsConfigured.length ? equipmentIdsConfigured : [],
    }),
    [dataSourceIds, equipmentKey],
  );

  const fetchFull = useCallback(async () => {
    if (!dataSourceIds.length) return;
    setLoading(true);
    setErr(null);
    try {
      const payload = await postEnergyDashboard({ ...bodyBase, refreshScope: "full" });
      setDash(payload);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [bodyBase, dataSourceIds.length]);

  const fetchLive = useCallback(async () => {
    if (!dataSourceIds.length) return;
    try {
      const payload = await postEnergyDashboard({ ...bodyBase, refreshScope: "live" });
      setDash((prev) => {
        if (!prev) return payload;
        return {
          ...prev,
          summary: payload.summary ?? prev.summary,
          equipmentTree: payload.equipmentTree ?? prev.equipmentTree,
          table: payload.table ?? prev.table,
          classificationPie: payload.classificationPie?.length ? payload.classificationPie : prev.classificationPie,
          loopRanking: payload.loopRanking?.length ? payload.loopRanking : prev.loopRanking,
          generatedAt: payload.generatedAt,
          filtersApplied: payload.filtersApplied ?? prev.filtersApplied,
          hourlySeries: payload.hourlySeries?.length ? payload.hourlySeries : prev.hourlySeries,
          dayTrend: payload.dayTrend?.length ? payload.dayTrend : prev.dayTrend,
          monthTrend: payload.monthTrend?.length ? payload.monthTrend : prev.monthTrend,
        };
      });
    } catch {
      /* 轮询失败静默 */
    }
  }, [bodyBase, dataSourceIds.length]);

  useEffect(() => {
    if (!dataSourceIds.length || !carouselPageActive || pollIntervalMs == null) return;
    const t = setInterval(() => fetchLive(), pollIntervalMs);
    return () => clearInterval(t);
  }, [dataSourceIds.length, fetchLive, carouselPageActive, pollIntervalMs]);

  useEffect(() => {
    if (!dataSourceIds.length) return;
    const h = setTimeout(() => fetchFull(), 180);
    return () => clearTimeout(h);
  }, [dataSourceIds, equipmentKey, fetchFull]);

  const summary = dash?.summary ?? {};
  const pie = dash?.classificationPie ?? [];
  const loops = dash?.loopRanking ?? [];
  const table = dash?.table ?? [];
  const hourChartPoints = useMemo(() => buildLast8HourPoints(dash?.hourlySeries), [dash?.hourlySeries]);
  const dayChartPoints = useMemo(() => buildLast7DayPoints(dash?.dayTrend), [dash?.dayTrend]);
  const monthChartPoints = useMemo(() => buildLast6MonthPoints(dash?.monthTrend), [dash?.monthTrend]);

  if (!dataSourceIds.length) {
    return (
      <section className="edb-shell screen-panel panel-span-12 panel-unbounded">
        <p className="edb-banner-error">{bootErr || "请在后台「屏幕子页面」为能耗页配置数据库数据源。"}</p>
      </section>
    );
  }

  return (
    <section className="edb-shell screen-panel panel-span-12 panel-unbounded">
      <header className="edb-hero">
        <div className="edb-hero-title">
          <h2>{bootstrap?.pageTitle || "能耗数据采集与设备状态监测看板"}</h2>
          {bootstrap?.sourceName ? <span className="edb-src">{bootstrap.sourceName}</span> : null}
        </div>
        <div className="edb-hero-meta">
          {loading ? "加载中…" : dash?.generatedAt ? `更新 ${dash.generatedAt}` : ""}
        </div>
      </header>

      {err ? (
        <div className="edb-banner-error" role="alert">
          {err}
        </div>
      ) : null}

      <div className="edb-kpi-row">
        <article className="edb-kpi">
          <span className="edb-kpi-label">今日总用电</span>
          <strong className="edb-kpi-val cyan">{formatNum(summary.todayKwh)}</strong>
          <span className="edb-kpi-unit">{summary.unit || "kWh"}</span>
        </article>
        <article className="edb-kpi">
          <span className="edb-kpi-label">本月累计</span>
          <strong className="edb-kpi-val blue">{formatNum(summary.monthKwh)}</strong>
          <span className="edb-kpi-unit">{summary.unit || "kWh"}</span>
        </article>
        <article className="edb-kpi edb-kpi--merged-run-alert">
          <span className="edb-kpi-label">运行与通讯异常</span>
          <div className="edb-kpi-split">
            <div className="edb-kpi-split-cell">
              <span className="edb-kpi-sublabel">运行设备</span>
              <strong className="edb-kpi-val green">{summary.runningDeviceCount ?? "—"}</strong>
            </div>
            <div className="edb-kpi-split-cell">
              <span className="edb-kpi-sublabel">通讯异常</span>
              <strong className="edb-kpi-val red">{summary.abnormalDeviceCount ?? "—"}</strong>
            </div>
          </div>
        </article>
        <article className="edb-kpi edb-kpi-wide">
          <span className="edb-kpi-label">分类用电（今日）</span>
          <div className="edb-mini-bars">
            {(summary.categoryMiniBars ?? []).map((c) => (
              <div key={c.id} className="edb-mini-bar-i">
                <span>{c.label}</span>
                <div className="edb-mini-track">
                  <div className="edb-mini-fill" style={{ width: `${c.percent}%`, background: c.color }} />
                </div>
                <em>{c.percent}%</em>
              </div>
            ))}
          </div>
        </article>
        <article className="edb-kpi edb-kpi-tall">
          <span className="edb-kpi-label">昨日同时段对比</span>
          <div className="edb-yoy">
            <span>昨日窗 {formatNum(summary.yesterdaySameWindowKwh)}</span>
            <span>今日窗 {formatNum(summary.todaySameWindowKwh)}</span>
            <strong className={summary.yoyPercent >= 0 ? "up" : "down"}>
              {summary.yoyPercent >= 0 ? "+" : ""}
              {(summary.yoyPercent ?? 0).toFixed?.(1) ?? summary.yoyPercent}%
            </strong>
          </div>
        </article>
      </div>

      <div className="edb-main edb-main--no-tree">
        <main className="edb-center">
          <div className="edb-table-wrap edb-table-wrap--fit">
            <h3 className="edb-block-title">实时通讯与电量</h3>
            <div className="edb-table-scroll edb-scroll edb-table-scroll--fit">
              <table className="edb-table">
                <thead>
                  <tr>
                    <th>设备</th>
                    <th>通讯</th>
                    <th>有功电能读数</th>
                    <th>近1h电量</th>
                    <th>当日累计</th>
                    <th>回路类型</th>
                    <th>能耗分类</th>
                    <th>倍率</th>
                  </tr>
                </thead>
                <tbody>
                  {table.map((row) => (
                    <tr key={row.equipmentId} className={row.rowAlert ? "edb-tr-alert" : ""}>
                      <td>
                        <span className={`edb-led ${row.commNormal ? "edb-led--normal" : "edb-led--abnormal"}`} />
                        {row.equipmentName}
                      </td>
                      <td>{row.commNormal ? "正常" : "异常"}</td>
                      <td>{row.reading}</td>
                      <td>{row.lastHourKwh}</td>
                      <td>{row.todayKwh}</td>
                      <td>{row.loopType}</td>
                      <td>{row.energyCategory}</td>
                      <td>{row.multiplyingPower}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!table.length ? <div className="edb-empty">暂无表格数据</div> : null}
            </div>
          </div>

          <div className="edb-unified-chart-panel">
            <h3 className="edb-unified-chart-main-title">电量分析</h3>
            <div className="edb-unified-triple">
              <div className="edb-unified-chart-col">
                <h4 className="edb-unified-chart-col-title">
                  小时 <span className="edb-unified-chart-sub">最近8小时（kWh）</span>
                </h4>
                <UnifiedEnergyBarChart points={hourChartPoints} variant="hour" />
              </div>
              <div className="edb-unified-chart-col">
                <h4 className="edb-unified-chart-col-title">
                  按日 <span className="edb-unified-chart-sub">最近一周（kWh）</span>
                </h4>
                <UnifiedEnergyBarChart points={dayChartPoints} variant="day" />
              </div>
              <div className="edb-unified-chart-col">
                <h4 className="edb-unified-chart-col-title">
                  按月 <span className="edb-unified-chart-sub">最近6个月（kWh）</span>
                </h4>
                <UnifiedEnergyBarChart points={monthChartPoints} variant="month" />
              </div>
            </div>
          </div>
        </main>

        <aside className="edb-aside edb-aside-right edb-scroll">
          <div className="edb-card">
            <h4>能耗分类占比</h4>
            <DonutChart slices={pie} />
          </div>
          <div className="edb-card">
            <h4>回路类型 TOP5</h4>
            <ul className="edb-loop-list">
              {(loops ?? []).map((l, i) => (
                <li key={i}>
                  <span>{l.loopType}</span>
                  <strong>{formatNum(l.kwh)}</strong>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </section>
  );
}

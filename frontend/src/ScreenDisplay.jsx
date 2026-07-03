import { Fragment, useEffect, useMemo, useRef, useState } from "react";

import { EnergyDashboardBoard } from "./EnergyDashboardBoard.jsx";
import { RealtimeDeviceCard } from "./screen/realtime/RealtimeCards.jsx";
import { TaotongGunziLineRealtimeBoard } from "./screen/realtime/TaotongGunziLineBoard.jsx";
import { XiaozhouLineRealtimeBoard } from "./screen/realtime/XiaozhouLineBoard.jsx";
import { ScreenCarouselPageContext } from "./screenCarouselContext.jsx";

const DAY_MS = 24 * 60 * 60 * 1000;
const DEFAULT_PAGE_KEYS = {
  left: ["overview", "operations", "energy", "realtime"],
  right: ["schedule", "risk", "simulation"],
};
const PAGE_PRESETS = {
  left: {
    overview: {
      key: "overview",
      label: "综合总览",
      sections: ["deviceOverview", "productionOverview", "productionTrend", "energyOverview", "repairPlaceholder"],
    },
    operations: {
      key: "operations",
      label: "运行与产量",
      sections: ["deviceOverview", "productionOverview", "productionTrend"],
    },
    energy: {
      key: "energy",
      label: "能耗数据",
      sections: ["energyData"],
    },
    realtime: {
      key: "realtime",
      label: "设备实时监控",
      sections: ["deviceRealtimeMonitor"],
    },
  },
  right: {
    schedule: {
      key: "schedule",
      label: "排产总览",
      sections: ["schedule", "delayLegend", "simulationPlaceholder"],
    },
    risk: {
      key: "risk",
      label: "风险说明",
      sections: ["delayLegend", "schedule"],
    },
    simulation: {
      key: "simulation",
      label: "仿真预留",
      sections: ["simulationPlaceholder", "delayLegend"],
    },
    realtime: {
      key: "realtime",
      label: "设备实时监控",
      sections: ["deviceRealtimeMonitor"],
    },
    energy: {
      key: "energy",
      label: "能耗数据",
      sections: ["energyData"],
    },
  },
};
const EMBEDDED_SECTION_HOSTS = {
  energyOverview: "productionTrend",
  repairPlaceholder: "deviceOverview",
  delayLegend: "schedule",
};

function buildApiUrl(pathname) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
  return `${baseUrl}${pathname}`;
}

async function fetchScreenPayload(areaCode, screenKey) {
  const response = await fetch(buildApiUrl(`/api/screens/${encodeURIComponent(areaCode)}/${screenKey}`));
  const responseText = await response.text();
  let payload = null;

  if (responseText) {
    try {
      payload = JSON.parse(responseText);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const message =
      payload?.message ||
      `screen request failed (${response.status})`;
    throw new Error(message);
  }

  if (!payload) {
    const sample = responseText.trim().slice(0, 120);
    const hint = sample ? `, response starts with: ${sample}` : "";
    throw new Error(`screen payload is invalid${hint}`);
  }

  if (payload.success === false) {
    throw new Error(payload.message || "screen request failed");
  }

  if (payload.data && typeof payload.data === "object") {
    return payload.data;
  }

  if (payload.screen && payload.content) {
    return payload;
  }

  throw new Error("screen payload is invalid");
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}:${String(date.getSeconds()).padStart(2, "0")}`;
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("zh-CN").format(Number(value));
}

/** 产线卡片时间兜底：仅展示 YYYY-MM-DD */
function formatScreenDateOnly(value) {
  if (value == null || value === "") {
    return "-";
  }
  const s = String(value).trim();
  const head = s.slice(0, 10);
  if (/^\d{4}-\d{2}-\d{2}$/.test(head)) {
    return head;
  }
  const t = new Date(s);
  if (Number.isNaN(t.getTime())) {
    return "-";
  }
  const y = t.getFullYear();
  const m = String(t.getMonth() + 1).padStart(2, "0");
  const d = String(t.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function startOfDay(value) {
  const date = value instanceof Date ? new Date(value) : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  date.setHours(0, 0, 0, 0);
  return date;
}

function buildWindowDays(windowDays, anchorIsoDate) {
  const safeWindowDays = Math.max(Number(windowDays) || 30, 1);
  const fromAnchor = anchorIsoDate ? startOfDay(anchorIsoDate) : null;
  const windowStart = fromAnchor ?? startOfDay(new Date()) ?? new Date();
  return Array.from({ length: safeWindowDays }, (_, index) => {
    return new Date(windowStart.getTime() + index * DAY_MS);
  });
}

function formatWindowLabel(date, index) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  if (index === 0 || index === 29 || date.getDate() === 1 || index % 5 === 0) {
    return `${month}/${day}`;
  }
  return day;
}

function getGanttBarLayout(order, windowStart, windowDays) {
  const plannedStart = startOfDay(order?.plannedStartAt ?? order?.displayStartAt);
  const plannedEnd = startOfDay(order?.plannedEndAt ?? order?.displayEndAt);

  if (!plannedStart || !plannedEnd) {
    return null;
  }

  const rawStart = Math.floor((plannedStart.getTime() - windowStart.getTime()) / DAY_MS);
  const rawEnd = Math.floor((plannedEnd.getTime() - windowStart.getTime()) / DAY_MS) + 1;
  const normalizedEnd = Math.max(rawEnd, rawStart + 1);
  const clippedStart = clamp(rawStart, 0, windowDays);
  const clippedEnd = clamp(normalizedEnd, 0, windowDays);

  if (clippedEnd <= clippedStart) {
    return null;
  }

  const spanDays = Math.max(clippedEnd - clippedStart, 1);
  return {
    offsetDays: clippedStart,
    spanDays,
    leftPercent: (clippedStart / windowDays) * 100,
    widthPercent: (spanDays / windowDays) * 100,
    clippedStart: rawStart < 0,
    clippedEnd: normalizedEnd > windowDays,
  };
}

function getGanttBarDensity(layout) {
  if (!layout) {
    return "full";
  }

  if (layout.spanDays <= 1 || layout.widthPercent <= 4.5) {
    return "tiny";
  }

  if (layout.spanDays <= 2 || layout.widthPercent <= 8) {
    return "compact";
  }

  return "full";
}

/** 完成率≥100% 视为上游已完工脏数据，不展示在甘特上（与后端过滤一致） */
function isScheduleOrderExcludedAsUpstreamCompleted(order) {
  const rateRaw = Number(order?.completionRate);
  if (!Number.isFinite(rateRaw)) {
    return false;
  }
  return rateRaw >= 100;
}

/** 计划结束日早于今日且未满进度 → 超时未完成（未完成部分用红色底） */
function parseOrderPlanEndDay(order) {
  const raw = order?.displayEndAt ?? order?.plannedEndAt;
  if (raw == null || raw === "") {
    return null;
  }
  const s = String(raw);
  const dayPart = s.length >= 10 ? s.slice(0, 10) : s;
  return startOfDay(dayPart);
}

function isScheduleOrderOverdueIncomplete(order) {
  if (isScheduleOrderExcludedAsUpstreamCompleted(order)) {
    return false;
  }
  const rateRaw = Number(order?.completionRate);
  const rate = Number.isFinite(rateRaw) ? rateRaw : 0;
  if (rate >= 99.99) {
    return false;
  }
  const endDay = parseOrderPlanEndDay(order);
  if (!endDay) {
    return false;
  }
  const today = startOfDay(new Date());
  if (!today) {
    return false;
  }
  return endDay.getTime() < today.getTime();
}

/** 甘特条底色：未开始全蓝；进行中左侧绿、右侧蓝（未完成）；超时未完成未完成侧红底、已完成侧黄；完工全绿；暂停灰 */
function getGanttScheduleVisual(order) {
  const status = String(order.status ?? "").trim();
  const risk = order.riskStatus ?? "normal";
  const rateRaw = Number(order.completionRate);
  const rate = Number.isFinite(rateRaw) ? Math.min(100, Math.max(0, rateRaw)) : 0;
  const stLower = status.toLowerCase();
  const overdueIncomplete = isScheduleOrderOverdueIncomplete(order);

  const isPaused = risk === "paused" || /暂停|paused/i.test(status);
  if (isPaused) {
    return { variant: "paused", completedPct: rate, risk, overdueIncomplete: false };
  }

  const looksDone = rate >= 99.99 || /完成|完工|结案|关闭/i.test(status);
  if (looksDone) {
    return { variant: "green_full", completedPct: 100, risk, overdueIncomplete: false };
  }

  const looksInProgress =
    /进行|执行|生产中|在制|加工中/i.test(status) ||
    stLower === "in_progress" ||
    stLower === "processing";

  /* 有完成率则一律按 split 展示进度条，避免上游仍标 planned/未开始却已有产量时整根单色 */
  const looksNotStarted =
    rate === 0 &&
    (stLower === "planned" ||
      /未开始|待开始/i.test(status) ||
      !looksInProgress);

  if (looksNotStarted) {
    return {
      variant: overdueIncomplete ? "red_full" : "blue_full",
      completedPct: 0,
      risk,
      overdueIncomplete,
    };
  }

  return { variant: "split", completedPct: rate, risk, overdueIncomplete };
}

function ganttBarRiskClass(risk) {
  if (!risk || risk === "normal") {
    return "";
  }
  return `gantt-bar--risk-${risk}`;
}

function formatGanttMaterialLine(order) {
  const code = order.materialCode ?? "";
  const name = order.materialName ?? "";
  const c = String(code).trim();
  const n = String(name).trim();
  if (c && n) {
    return `${c} ${n}`;
  }
  return c || n || "-";
}

function formatGanttDateRange(order, display) {
  const label = display.timeRangeLabel;
  if (typeof label === "string" && label.includes("至")) {
    return label;
  }
  const a = order.displayStartAt ?? "";
  const b = order.displayEndAt ?? "";
  if (a && b) {
    return `${a} 至 ${b}`;
  }
  return label || "";
}

function ganttCompletionLabel(display, order) {
  return display.completionRateLabel || `${order.completionRate ?? "-"}%`;
}

function ganttOrderSortKey(order) {
  const raw = order.plannedStartAt ?? order.displayStartAt;
  if (!raw) {
    return 0;
  }
  const t = new Date(raw).getTime();
  return Number.isNaN(t) ? 0 : t;
}

function compareGanttOrders(a, b) {
  const da = ganttOrderSortKey(a.order);
  const db = ganttOrderSortKey(b.order);
  if (da !== db) {
    return da - db;
  }
  return String(a.order.orderCode ?? "").localeCompare(String(b.order.orderCode ?? ""), "zh-CN");
}

function resolveConfiguredPages(screenKey, pageKeys) {
  const presets = PAGE_PRESETS[screenKey] ?? {};
  const configuredKeys = Array.isArray(pageKeys) ? pageKeys : [];
  const resolvedPages = configuredKeys.map((pageKey) => presets[pageKey]).filter(Boolean);

  if (resolvedPages.length > 0) {
    return resolvedPages;
  }

  return DEFAULT_PAGE_KEYS[screenKey].map((pageKey) => presets[pageKey]).filter(Boolean);
}

function isModuleEnabled(moduleSettings, moduleKey) {
  return moduleSettings?.[moduleKey] !== false;
}

function resolveVisibleSections(activeSections, moduleSettings) {
  const resolved = [];
  const seen = new Set();

  activeSections.forEach((sectionKey) => {
    if (!isModuleEnabled(moduleSettings, sectionKey)) {
      return;
    }

    const hostKey = EMBEDDED_SECTION_HOSTS[sectionKey] ?? sectionKey;
    if (hostKey !== sectionKey && !isModuleEnabled(moduleSettings, hostKey)) {
      return;
    }
    if (seen.has(hostKey)) {
      return;
    }

    seen.add(hostKey);
    resolved.push(hostKey);
  });

  return resolved;
}

function useClock() {
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    const timerId = window.setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => window.clearInterval(timerId);
  }, []);

  return currentTime;
}

function useFullscreen(targetRef) {
  const [isFullscreen, setIsFullscreen] = useState(() => Boolean(document.fullscreenElement));

  useEffect(() => {
    function handleFullscreenChange() {
      const target = targetRef.current;
      if (!target) {
        setIsFullscreen(Boolean(document.fullscreenElement));
        return;
      }
      setIsFullscreen(document.fullscreenElement === target);
    }

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, [targetRef]);

  async function toggleFullscreen() {
    const target = targetRef.current;
    if (!target || !document.fullscreenEnabled) {
      return;
    }

    if (document.fullscreenElement === target) {
      await document.exitFullscreen();
      return;
    }

    await target.requestFullscreen();
  }

  return {
    canFullscreen: Boolean(document.fullscreenEnabled),
    isFullscreen,
    toggleFullscreen,
  };
}

function usePageRotation(pages, rotationIntervalSeconds) {
  const [activePageIndex, setActivePageIndex] = useState(0);

  useEffect(() => {
    setActivePageIndex(0);
  }, [pages]);

  useEffect(() => {
    const safeInterval = Number(rotationIntervalSeconds) || 0;
    if (pages.length <= 1 || safeInterval <= 0) {
      return undefined;
    }

    const timerId = window.setInterval(() => {
      setActivePageIndex((currentIndex) => (currentIndex + 1) % pages.length);
    }, safeInterval * 1000);

    return () => window.clearInterval(timerId);
  }, [pages, rotationIntervalSeconds]);

  return [activePageIndex, setActivePageIndex];
}

function useAutoVerticalScroll(containerRef, enabled, intervalMs = 40) {
  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    const timerId = window.setInterval(() => {
      const element = containerRef.current;
      if (!element) {
        return;
      }

      const maxScrollTop = element.scrollHeight - element.clientHeight;
      if (maxScrollTop <= 8) {
        return;
      }

      const nextScrollTop = element.scrollTop + 1;
      if (nextScrollTop >= maxScrollTop - 1) {
        element.scrollTop = 0;
        return;
      }

      element.scrollTop = nextScrollTop;
    }, intervalMs);

    return () => window.clearInterval(timerId);
  }, [containerRef, enabled, intervalMs]);
}

/** When `active`, observes container size and auto-scrolls only if content overflows (vertical marquee). */
function useOverflowAutoScroll(containerRef, active, intervalMs = 40) {
  const [isOverflowing, setIsOverflowing] = useState(false);

  useEffect(() => {
    if (!active) {
      setIsOverflowing(false);
      return undefined;
    }

    const el = containerRef.current;
    if (!el) {
      setIsOverflowing(false);
      return undefined;
    }

    const measure = () => {
      setIsOverflowing(el.scrollHeight - el.clientHeight > 8);
    };

    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [containerRef, active]);

  useAutoVerticalScroll(containerRef, isOverflowing, intervalMs);

  return isOverflowing;
}

function ScreenStatus({ errorMessage, usingFallback, lastSuccessfulAt }) {
  const metaDisplay = lastSuccessfulAt?.display ?? {};
  const lastSuccessfulAtLabel = metaDisplay.lastSuccessfulAtLabel || formatDateTime(lastSuccessfulAt?.value || lastSuccessfulAt);

  if (!errorMessage && !usingFallback) {
    return (
      <div className="screen-status">
        <span className="status-pill ok">数据正常</span>
        <span>最近成功更新 {lastSuccessfulAtLabel}</span>
      </div>
    );
  }

  return (
    <div className="screen-status">
      <span className={usingFallback ? "status-pill warning" : "status-pill danger"}>
        {usingFallback ? "正在使用兜底数据" : "接口异常"}
      </span>
      <span>{errorMessage || `最近成功更新 ${lastSuccessfulAtLabel}`}</span>
    </div>
  );
}

function resolveScreenSubtitle(screen, welcome) {
  const fromScreen = typeof screen?.subtitle === "string" ? screen.subtitle.trim() : "";
  const fromWelcome = typeof welcome?.welcomeMessage === "string" ? welcome.welcomeMessage.trim() : "";
  return fromScreen || fromWelcome || "面向访客的数字化工厂展示";
}

function ScreenHeader({
  currentTime,
  logoUrl,
  onToggleFullscreen,
  pageIndex,
  pages,
  screen,
  statusNode,
  welcome,
  canFullscreen,
  isFullscreen,
  setPageIndex,
}) {
  const subtitle = resolveScreenSubtitle(screen, welcome);

  return (
    <header className="screen-header">
      <div className="screen-hero">
        <div className="screen-brand">
          <div className="screen-logo">
            {logoUrl ? <img alt={welcome.companyName || "HOTA"} src={logoUrl} /> : <span>HT</span>}
          </div>
          <div className="screen-brand-copy">
            <p className="screen-tag">HOTA MDS</p>
            <h1>{screen.title || "和泰智造数屏系统"}</h1>
            <p className="screen-subtitle">{subtitle}</p>
          </div>
        </div>

        <div className="screen-toolbar">
          <div className="screen-toolbar-meta">
            <strong>{welcome.companyName || "和泰智造"}</strong>
            <span>{formatDateTime(currentTime.toISOString())}</span>
            <span className="screen-toolbar-hint">双击画面或点击按钮进入全屏</span>
          </div>
          {canFullscreen ? (
            <button className="screen-action-button" onClick={onToggleFullscreen} type="button">
              {isFullscreen ? "退出全屏" : "进入全屏"}
            </button>
          ) : null}
        </div>
      </div>

      <div className="screen-control-bar">
        <div className="screen-page-switcher" role="tablist" aria-label="页面轮播">
          {pages.map((page, index) => (
            <button
              aria-selected={pageIndex === index}
              className={pageIndex === index ? "screen-page-chip active" : "screen-page-chip"}
              key={page.key}
              onClick={() => setPageIndex(index)}
              type="button"
            >
              {page.label}
            </button>
          ))}
        </div>
        <div className="screen-control-status">{statusNode}</div>
      </div>
    </header>
  );
}

function MetricTile({ label, value, accent = "green" }) {
  return (
    <article className={`metric-tile accent-${accent}`}>
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
    </article>
  );
}

function SectionEmpty({ description, title = "当前模块暂无数据" }) {
  return (
    <div className="section-empty">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}

function LeftScreen({ payload, errorMessage, fullscreenState, screenRef }) {
  const clock = useClock();
  const screen = payload?.screen ?? {};
  const content = payload?.content ?? {};
  const meta = payload?.meta ?? {};
  const welcome = content.welcome ?? {};
  const deviceOverview = content.deviceOverview ?? {};
  const productionOverview = content.productionOverview ?? {};
  const energyOverview = content.energyOverview ?? {};
  const repairPlaceholder = content.repairPlaceholder ?? {};
  const productionTrend = content.productionTrend ?? [];
  const lineSummaries = productionOverview.lineSummaries ?? [];
  const areaSummaries = energyOverview.areaSummaries ?? [];
  const productionDisplay = productionOverview.display ?? {};
  const ledgerLineCount =
    productionOverview.ledgerProductionLineCount != null ? productionOverview.ledgerProductionLineCount : lineSummaries.length;
  const energyDisplay = energyOverview.display ?? {};
  const deviceDisplay = deviceOverview.display ?? {};
  const moduleSettings = screen.moduleSettings ?? {};
  const pages = useMemo(() => resolveConfiguredPages("left", screen.pageKeys), [screen.pageKeys]);
  const [activePageIndex, setActivePageIndex] = usePageRotation(pages, screen.rotationIntervalSeconds);
  const activeSections = pages[activePageIndex]?.sections ?? [];
  const visibleSectionsActive = useMemo(
    () => resolveVisibleSections(activeSections, moduleSettings),
    [activeSections, moduleSettings],
  );
  const trendMax = Math.max(
    ...productionTrend.map((item) => Number(item?.producedQuantity ?? 0)),
    1,
  );
  const lineSummaryScrollRef = useRef(null);
  const energySummaryScrollRef = useRef(null);
  const energyModuleOn = isModuleEnabled(moduleSettings, "energyOverview");
  const lineScrollActive = lineSummaries.length > 0;
  const energyScrollActive = energyModuleOn && areaSummaries.length > 0;

  const lineListOverflowing = useOverflowAutoScroll(lineSummaryScrollRef, lineScrollActive);
  const energyListOverflowing = useOverflowAutoScroll(energySummaryScrollRef, energyScrollActive);

  const drm = content.deviceRealtimeMonitor ?? {};
  const [alarmPulseDismissed, setAlarmPulseDismissed] = useState(() => new Set());

  useEffect(() => {
    const cards = content.deviceRealtimeMonitor?.cards ?? [];
    setAlarmPulseDismissed((prev) => {
      const next = new Set();
      for (const code of prev) {
        const card = cards.find((c) => c.sourceCode === code);
        if (card?.machineStatus?.alarmActive) {
          next.add(code);
        }
      }
      return next;
    });
  }, [content.deviceRealtimeMonitor]);

  const sectionNodes = {
    deviceOverview: (
      <section className="screen-panel panel-span-4" key="deviceOverview">
        <div className="panel-header">
          <h2>设备运行概览</h2>
          <span>数据更新时间 {deviceDisplay.sourceUpdatedAtLabel || formatDateTime(deviceOverview.sourceUpdatedAt)}</span>
        </div>
        <div className="metric-grid metric-grid-three">
          <MetricTile accent="teal" label="设备总数" value={deviceDisplay.totalCountLabel || formatNumber(deviceOverview.totalCount)} />
          <MetricTile accent="green" label="运行设备" value={deviceDisplay.runningCountLabel || formatNumber(deviceOverview.runningCount)} />
          <MetricTile accent="amber" label="异常设备" value={deviceDisplay.abnormalCountLabel || formatNumber(deviceOverview.abnormalCount)} />
        </div>
        {isModuleEnabled(moduleSettings, "repairPlaceholder") ? (
          <div className="embedded-panel-block">
            <div className="embedded-panel-header">
              <h3>报修占位区</h3>
              <span>一期后段</span>
            </div>
            <div className="placeholder-copy embedded-placeholder-copy">
              <strong>{repairPlaceholder.title || "报修模块待接入"}</strong>
              <p>{repairPlaceholder.description || "当前阶段仅保留占位区，不阻塞一期前段大屏。"}</p>
            </div>
          </div>
        ) : null}
      </section>
    ),
    productionOverview: (
      <section className="screen-panel panel-span-4 production-overview-panel" key="productionOverview">
        <div className="panel-header">
          <h2>产量执行概览</h2>
          <span>{`产线 ${ledgerLineCount} 条`}</span>
        </div>
        <div className="metric-grid metric-grid-two">
          <MetricTile
            accent="blue"
            label="目标产量"
            value={productionDisplay.totalTargetQuantityLabel || formatNumber(productionOverview.totalTargetQuantity)}
          />
          <MetricTile
            accent="teal"
            label="已产数量"
            value={productionDisplay.totalProducedQuantityLabel || formatNumber(productionOverview.totalProducedQuantity)}
          />
        </div>
        <div className="production-overview-summary">
          <span>完成率 {productionDisplay.overallCompletionRateLabel || `${productionOverview.overallCompletionRate ?? "-"}%`}</span>
        </div>
        {lineSummaries.length > 0 ? (
          <div
            className={
              lineListOverflowing
                ? "line-summary-list production-overview-list line-summary-list-scrollable"
                : "line-summary-list production-overview-list"
            }
            ref={lineSummaryScrollRef}
          >
            {lineSummaries.map((item) => {
              const itemDisplay = item.display ?? {};
              const completionRateValue = clamp(Number(item?.completionRate ?? 0), 0, 100);
              const progressAccent = itemDisplay.progressAccent || (item.isDelayed ? "red" : "blue");
              return (
                <article className="line-summary-item" key={item.lineCode}>
                  <div className="line-summary-main">
                    <div className="line-summary-head">
                      <strong>{item.lineName}</strong>
                    </div>
                    <span>{itemDisplay.currentOrderLabel || item.currentOrderCode || "当前订单待补充"}</span>
                  </div>
                  <div className="line-summary-meta">
                    <span>{itemDisplay.targetQuantityLabel || `目标 ${formatNumber(item.targetQuantity)}`}</span>
                    <span>{itemDisplay.producedQuantityLabel || `已产 ${formatNumber(item.producedQuantity)}`}</span>
                  </div>
                  <div className="line-summary-progress-row">
                    <div
                      aria-hidden="true"
                      className={`line-summary-progress accent-${progressAccent}`}
                    >
                      <div
                        className={`line-summary-progress-fill accent-${progressAccent}`}
                        style={{ width: `${completionRateValue}%` }}
                      />
                    </div>
                    <span className="line-summary-progress-value">
                      {itemDisplay.completionRateLabel || `${item.completionRate ?? "-"}%`}
                    </span>
                  </div>
                  <div className="line-summary-timeline">
                    <span>
                      {itemDisplay.plannedRangeLabel ||
                        `${formatScreenDateOnly(item.plannedStartAt)} - ${formatScreenDateOnly(item.plannedEndAt)}`}
                    </span>
                    <span>{`预计完成 ${itemDisplay.estimatedCompletionLabel || formatScreenDateOnly(item.estimatedCompletionAt)}`}</span>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <SectionEmpty description="当前没有可展示的产线产量摘要。" />
        )}
      </section>
    ),
    productionTrend: (
      <section
        className={`screen-panel panel-span-4 production-trend-panel${energyModuleOn ? " production-trend-panel--with-energy" : ""}`}
        key="productionTrend"
      >
        <div className="panel-header">
          <h2>近 8 小时产量趋势</h2>
          <span>后端缓存数据</span>
        </div>
        {productionTrend.length > 0 ? (
          <div className="trend-bars production-trend-chart">
            {productionTrend.map((item) => {
              const itemDisplay = item.display ?? {};
              const producedQuantity = Number(item?.producedQuantity ?? 0);

              return (
                <div className="trend-bar-item" key={item.hourLabel}>
                  <span className="trend-bar-value">{itemDisplay.producedQuantityLabel || formatNumber(item.producedQuantity)}</span>
                  <div className="trend-bar-track">
                    <div
                      className="trend-bar-fill"
                      style={{ height: `${Math.max((producedQuantity / trendMax) * 100, 10)}%` }}
                    />
                  </div>
                  <span className="trend-bar-label">{itemDisplay.timeLabel || item.hourLabel}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <SectionEmpty description="产量趋势点暂未返回，当前不会影响其他模块展示。" />
        )}
        {energyModuleOn ? (
          <div className="embedded-panel-block embedded-panel-block-fill">
            <div className="embedded-panel-header">
              <h3>区域能耗概览</h3>
              <span>{energyDisplay.totalConsumptionLabel || `总能耗 ${formatNumber(energyOverview.totalConsumption)} ${energyOverview.unit ?? ""}`}</span>
            </div>
            <div className="embedded-panel-summary">
              <span>
                {`区域 ${areaSummaries.length} 个`}
                {energyListOverflowing ? " · 自动滚动中" : ""}
              </span>
            </div>
            {areaSummaries.length > 0 ? (
              <div
                className={
                  energyListOverflowing
                    ? "energy-list energy-list-embedded energy-list-scrollable"
                    : "energy-list energy-list-embedded"
                }
                ref={energySummaryScrollRef}
              >
                {areaSummaries.map((item) => {
                  const itemDisplay = item.display ?? {};
                  return (
                    <article className="energy-item energy-item-embedded" key={item.areaCode}>
                      <div>
                        <strong>{item.areaName}</strong>
                        <span>{item.areaCode}</span>
                      </div>
                      <strong>{itemDisplay.consumptionLabel || `${formatNumber(item.consumption)} ${item.unit ?? ""}`}</strong>
                    </article>
                  );
                })}
              </div>
            ) : (
              <SectionEmpty description="当前没有可展示的区域能耗数据。" />
            )}
          </div>
        ) : null}
      </section>
    ),
    deviceRealtimeMonitor: (
      <DeviceRealtimeSection
        key="deviceRealtimeMonitor"
        drm={drm}
        alarmPulseDismissed={alarmPulseDismissed}
        setAlarmPulseDismissed={setAlarmPulseDismissed}
      />
    ),
    energyData: <EnergyDashboardBoard key="energyData" bootstrap={content.energyData ?? {}} />,
  };

  const isRealtimeOnlyPage =
    visibleSectionsActive.length === 1 && visibleSectionsActive[0] === "deviceRealtimeMonitor";
  const isEnergyOnlyPage = visibleSectionsActive.length === 1 && visibleSectionsActive[0] === "energyData";

  return (
    <main className="screen-shell screen-left" onDoubleClick={fullscreenState.toggleFullscreen} ref={screenRef}>
      <ScreenHeader
        canFullscreen={fullscreenState.canFullscreen}
        currentTime={clock}
        isFullscreen={fullscreenState.isFullscreen}
        logoUrl={welcome.logoUrl}
        onToggleFullscreen={fullscreenState.toggleFullscreen}
        pageIndex={activePageIndex}
        pages={pages}
        screen={screen}
        setPageIndex={setActivePageIndex}
        statusNode={
          <ScreenStatus
            errorMessage={errorMessage}
            lastSuccessfulAt={{ value: meta.lastSuccessfulAt, display: meta.display }}
            usingFallback={meta.usingFallback}
          />
        }
        welcome={welcome}
      />

      <section className={`screen-page screen-grid screen-grid-left${isRealtimeOnlyPage ? " screen-grid-left-realtime" : ""}${isEnergyOnlyPage ? " screen-grid-energy" : ""}`}>
        {pages.length === 0 ? (
          <section className="screen-panel panel-span-12">
            <SectionEmpty title="未配置轮播页面" description="请在左右屏配置中设置 pageKeys。" />
          </section>
        ) : (
          pages.map((page, pageIndex) => {
            const sliceSections = resolveVisibleSections(page.sections ?? [], moduleSettings);
            const isSliceActive = pageIndex === activePageIndex;
            return (
              <ScreenCarouselPageContext.Provider key={page.key} value={{ isActive: isSliceActive }}>
                <div
                  className={`screen-page-slice${isSliceActive ? " screen-page-slice--active" : " screen-page-slice--hidden"}`}
                  aria-hidden={!isSliceActive}
                >
                  {sliceSections.length > 0 ? (
                    sliceSections.map((sectionKey) => {
                      const node = sectionNodes[sectionKey];
                      if (!node) return null;
                      return (
                        <Fragment key={`${page.key}-${sectionKey}`}>{node}</Fragment>
                      );
                    })
                  ) : (
                    <section className="screen-panel panel-span-12">
                      <SectionEmpty
                        title="当前轮播页没有可展示模块"
                        description="请检查该屏幕的 moduleSettings 或 pageKeys 配置。"
                      />
                    </section>
                  )}
                </div>
              </ScreenCarouselPageContext.Provider>
            );
          })
        )}
      </section>
    </main>
  );
}

function DeviceRealtimeSection({ drm, alarmPulseDismissed, setAlarmPulseDismissed }) {
  if (drm.realtimeLayout === "xiaozhou_line") {
    return (
      <XiaozhouLineRealtimeBoard
        drm={drm}
        alarmPulseDismissed={alarmPulseDismissed}
        setAlarmPulseDismissed={setAlarmPulseDismissed}
        formatDateTime={formatDateTime}
      />
    );
  }

  if (drm.realtimeLayout === "taotong_gunzi_line") {
    return (
      <TaotongGunziLineRealtimeBoard
        drm={drm}
        alarmPulseDismissed={alarmPulseDismissed}
        setAlarmPulseDismissed={setAlarmPulseDismissed}
        formatDateTime={formatDateTime}
      />
    );
  }

  return (
    <section className="screen-panel panel-span-12 panel-unbounded industrial-realtime-panel" key="deviceRealtimeMonitor">
      <div className="industrial-realtime-grid">
        {(drm.cards ?? []).map((card) => {
          const pulseOn = Boolean(card.machineStatus?.alarmActive) && !alarmPulseDismissed.has(card.sourceCode);
          return (
            <RealtimeDeviceCard
              key={card.sourceCode}
              card={card}
              pulseOn={pulseOn}
              formatDateTime={formatDateTime}
              onDismissAlarm={() => {
                if (card.machineStatus?.alarmActive) {
                  setAlarmPulseDismissed((prev) => new Set(prev).add(card.sourceCode));
                }
              }}
            />
          );
        })}
        {(drm.cards ?? []).length === 0 ? (
          <SectionEmpty title="当前暂无可监控 OPC UA 设备" description="请在数据源配置中绑定设备并配置节点列表（含 TK.MD 数据点）。" />
        ) : null}
      </div>
    </section>
  );
}

function GanttBoard({ lineSchedules, schedule }) {
  const barSlotHeight = 98;
  const barTopOffset = 10;
  const rowBottomPadding = 18;
  const windowDays = Math.max(Number(schedule?.windowDays) || 30, 1);
  const windowAnchorDate = schedule?.windowAnchorDate;
  const windowDates = useMemo(
    () => buildWindowDays(windowDays, windowAnchorDate),
    [windowDays, windowAnchorDate],
  );
  const windowStart = windowDates[0] ? startOfDay(windowDates[0]) : startOfDay(new Date());
  const scrollRef = useRef(null);
  const rowsActive = lineSchedules.length > 0;
  /* 甘特产线列表超量滚动：步长 1px，间隔 60ms（原 40ms 的 2/3 速度） */
  useOverflowAutoScroll(scrollRef, rowsActive, 60);

  return (
    <div className="gantt-shell">
      <div className="gantt-board">
        <div className="gantt-days">
          <div className="gantt-days-spacer">产线</div>
          <div className="gantt-days-track" style={{ "--gantt-window-days": windowDays }}>
            {windowDates.map((date, index) => (
              <span className="gantt-day-label" key={date.toISOString()}>
                {formatWindowLabel(date, index)}
              </span>
            ))}
          </div>
        </div>

        <div className="gantt-rows" ref={scrollRef}>
          {lineSchedules.length > 0 ? (
            lineSchedules.map((line) => {
              const visibleOrders = (line.orders ?? [])
                .filter((order) => !isScheduleOrderExcludedAsUpstreamCompleted(order))
                .map((order) => {
                  const layout = getGanttBarLayout(order, windowStart, windowDays);
                  return layout ? { order, layout } : null;
                })
                .filter(Boolean)
                .sort(compareGanttOrders);
              /* 两条纵向轨道交替：按时间排序后第 1、3、5… 在上轨，第 2、4、6… 在下轨，限制每条产线最多两行高度 */
              const laneCount = visibleOrders.length <= 1 ? 1 : 2;
              const rowHeight = laneCount * barSlotHeight + barTopOffset + rowBottomPadding;

              return (
                <article className="gantt-row" key={line.lineCode}>
                  <div className="gantt-line-meta">
                    <strong>{line.lineName}</strong>
                    <span>{line.areaName || "演示区域"}</span>
                  </div>
                  <div className="gantt-track-shell">
                    <div className="gantt-track" style={{ "--gantt-window-days": windowDays, minHeight: `${rowHeight}px` }}>
                      <div className="gantt-grid">
                        {windowDates.map((date) => (
                          <span className="gantt-grid-cell" key={date.toISOString()} />
                        ))}
                      </div>

                        {visibleOrders.length > 0 ? (
                          visibleOrders.map(({ order, layout }, orderIndex) => {
                            const display = order.display ?? {};
                            const density = getGanttBarDensity(layout);
                            const viz = getGanttScheduleVisual(order);
                            const barClassName = ["gantt-bar", `gantt-bar--${density}`, `gantt-bar--viz-${viz.variant}`, ganttBarRiskClass(viz.risk)]
                              .filter(Boolean)
                              .join(" ");
                            const completionLabel = ganttCompletionLabel(display, order);
                            const lane = orderIndex % 2;
                            const topPx = barTopOffset + lane * barSlotHeight;

                            return (
                              <div
                                className={barClassName}
                                key={`${line.lineCode}-${order.orderCode}-${orderIndex}`}
                                style={{
                                  left: `${layout.leftPercent}%`,
                                  top: `${topPx}px`,
                                  width: `${layout.widthPercent}%`,
                                }}
                              >
                                <div className="gantt-bar-paint-stack" aria-hidden="true">
                                  {viz.variant === "blue_full" ? <span className="gantt-bar-paint gantt-bar-paint--blue" /> : null}
                                  {viz.variant === "red_full" ? <span className="gantt-bar-paint gantt-bar-paint--red" /> : null}
                                  {viz.variant === "green_full" ? <span className="gantt-bar-paint gantt-bar-paint--green" /> : null}
                                  {viz.variant === "paused" ? <span className="gantt-bar-paint gantt-bar-paint--paused" /> : null}
                                  {viz.variant === "split" ? (
                                    <>
                                      <span
                                        className={
                                          viz.overdueIncomplete
                                            ? "gantt-bar-paint gantt-bar-paint--red gantt-bar-paint--base"
                                            : "gantt-bar-paint gantt-bar-paint--blue gantt-bar-paint--base"
                                        }
                                      />
                                      <span
                                        className={
                                          viz.overdueIncomplete
                                            ? "gantt-bar-paint gantt-bar-paint--yellow gantt-bar-paint--progress gantt-bar-paint--progress-cover"
                                            : "gantt-bar-paint gantt-bar-paint--green gantt-bar-paint--progress"
                                        }
                                        style={{ width: viz.completedPct <= 0 ? 0 : `${viz.completedPct}%` }}
                                      />
                                    </>
                                  ) : null}
                                </div>
                                <div className={`gantt-bar-content gantt-bar-content--${density}`}>
                                  <span className="gantt-bar-completion-corner">{completionLabel}</span>
                                  {density === "tiny" ? (
                                    <div className="gantt-bar-mini">
                                      <strong>{order.orderCode}</strong>
                                    </div>
                                  ) : density === "compact" ? (
                                    <div className="gantt-bar-compact">
                                      <strong>{order.orderCode}</strong>
                                    </div>
                                  ) : (
                                    <>
                                      <div className="gantt-bar-head">
                                        <strong className="gantt-bar-order-no">{order.orderCode}</strong>
                                      </div>
                                      <div className="gantt-bar-body gantt-bar-body--material">
                                        <span className="gantt-bar-material-line">{formatGanttMaterialLine(order)}</span>
                                      </div>
                                      <div className="gantt-bar-foot">
                                        <span className="gantt-bar-date-range">{formatGanttDateRange(order, display)}</span>
                                      </div>
                                    </>
                                  )}
                                </div>
                              </div>
                            );
                          })
                      ) : (
                        <div className="gantt-empty-row">当前产线在时间跨度内无可见订单</div>
                      )}
                    </div>
                  </div>
                </article>
              );
            })
          ) : (
            <div className="gantt-empty-state">当前没有可展示的未完工订单排产数据。</div>
          )}
        </div>
      </div>
    </div>
  );
}

function aggregateScheduleOverview(lineSchedules) {
  let totalTarget = 0;
  let totalProduced = 0;
  let orderCount = 0;
  const materialMap = new Map();

  for (const line of lineSchedules ?? []) {
    for (const order of line.orders ?? []) {
      if (isScheduleOrderExcludedAsUpstreamCompleted(order)) {
        continue;
      }
      orderCount += 1;
      const t = Number(order.targetQuantity);
      const p = Number(order.producedQuantity);
      const tt = Number.isFinite(t) ? t : 0;
      const pp = Number.isFinite(p) ? p : 0;
      totalTarget += tt;
      totalProduced += pp;
      const code = String(order.materialCode ?? "").trim() || "-";
      const name = String(order.materialName ?? "").trim();
      const key = `${code}\u0000${name}`;
      const cur = materialMap.get(key) ?? {
        materialCode: code,
        materialName: name,
        targetQuantity: 0,
        producedQuantity: 0,
        orderCount: 0,
      };
      cur.targetQuantity += tt;
      cur.producedQuantity += pp;
      cur.orderCount += 1;
      materialMap.set(key, cur);
    }
  }

  const materials = Array.from(materialMap.values()).sort((a, b) => {
    if (b.targetQuantity !== a.targetQuantity) {
      return b.targetQuantity - a.targetQuantity;
    }
    return b.orderCount - a.orderCount;
  });

  const completionPct =
    totalTarget > 0 ? Math.min(100, Math.round((totalProduced / totalTarget) * 10000) / 100) : 0;

  return { totalTarget, totalProduced, completionPct, materials, orderCount };
}

function ScheduleOverviewSide({ areaName, riskItems, lineSchedules }) {
  const stats = useMemo(() => aggregateScheduleOverview(lineSchedules), [lineSchedules]);
  const topMaterials = useMemo(() => stats.materials.slice(0, 8), [stats.materials]);

  return (
    <section className="screen-panel panel-span-4 placeholder-panel schedule-overview-side-panel">
      <div className="panel-header">
        <h2>{areaName ? `${areaName}工单信息总览` : "工单信息总览"}</h2>
      </div>
      <div className="schedule-overview-side-body">
        {riskItems.length > 0 ? (
          <div className="risk-summary-row risk-summary-row--overview">
            {riskItems.map((item) => (
              <article className={`risk-summary-tile accent-${item.accent}`} key={item.key}>
                <span>{item.label}</span>
                <strong>{item.countLabel || formatNumber(item.count)}</strong>
              </article>
            ))}
          </div>
        ) : null}

        <div className="schedule-overview-section">
          <h3 className="schedule-overview-section-title">窗口内工单产量</h3>
          {stats.orderCount === 0 ? (
            <p className="schedule-overview-empty">当前窗口内无可汇总工单。</p>
          ) : (
            <dl className="schedule-overview-metrics">
              <div className="schedule-overview-metric">
                <dt>工单数</dt>
                <dd>{formatNumber(stats.orderCount)}</dd>
              </div>
              <div className="schedule-overview-metric">
                <dt>目标产量</dt>
                <dd>{formatNumber(stats.totalTarget)}</dd>
              </div>
              <div className="schedule-overview-metric">
                <dt>已产数量</dt>
                <dd>{formatNumber(stats.totalProduced)}</dd>
              </div>
              <div className="schedule-overview-metric">
                <dt>产量完成率</dt>
                <dd>{`${stats.completionPct}%`}</dd>
              </div>
            </dl>
          )}
        </div>

        <div className="schedule-overview-section">
          <h3 className="schedule-overview-section-title">工单产成品统计</h3>
          {topMaterials.length === 0 ? (
            <p className="schedule-overview-empty">暂无物料维度数据。</p>
          ) : (
            <ul className="schedule-overview-material-list">
              {topMaterials.map((m, index) => (
                <li key={`${m.materialCode}-${m.materialName}-${index}`}>
                  <span
                    className="schedule-overview-material-line"
                    title={`${m.materialCode} ${m.materialName}`.trim()}
                  >
                    {formatGanttMaterialLine({ materialCode: m.materialCode, materialName: m.materialName })}
                  </span>
                  <span className="schedule-overview-material-qty">
                    {formatNumber(m.producedQuantity)} / {formatNumber(m.targetQuantity)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}

function RightScreen({ payload, errorMessage, fullscreenState, screenRef }) {
  const clock = useClock();
  const screen = payload?.screen ?? {};
  const content = payload?.content ?? {};
  const meta = payload?.meta ?? {};
  const welcome = content.welcome ?? {};
  const schedule = content.schedule ?? {};
  const riskItems = schedule?.riskSummary?.items ?? [];
  const scheduleRows = schedule.lineSchedules ?? [];
  const moduleSettings = screen.moduleSettings ?? {};
  const pages = useMemo(() => resolveConfiguredPages("right", screen.pageKeys), [screen.pageKeys]);
  const [activePageIndex, setActivePageIndex] = usePageRotation(pages, screen.rotationIntervalSeconds);
  const activeSections = pages[activePageIndex]?.sections ?? [];
  const visibleSectionsActive = useMemo(
    () => resolveVisibleSections(activeSections, moduleSettings),
    [activeSections, moduleSettings],
  );

  const activePageKey = pages[activePageIndex]?.key ?? "";

  const simulationScrollRef = useRef(null);
  const simulationScrollActive = visibleSectionsActive.includes("simulationPlaceholder");
  const simulationOverflowing = useOverflowAutoScroll(simulationScrollRef, simulationScrollActive);

  const isRealtimeOnlyPage =
    visibleSectionsActive.length === 1 && visibleSectionsActive[0] === "deviceRealtimeMonitor";
  const isEnergyOnlyPage = visibleSectionsActive.length === 1 && visibleSectionsActive[0] === "energyData";

  const drm = content.deviceRealtimeMonitor ?? {};
  const [alarmPulseDismissed, setAlarmPulseDismissed] = useState(() => new Set());
  useEffect(() => {
    const cards = content.deviceRealtimeMonitor?.cards ?? [];
    setAlarmPulseDismissed((prev) => {
      const next = new Set();
      for (const code of prev) {
        const card = cards.find((c) => c.sourceCode === code);
        if (card?.machineStatus?.alarmActive) {
          next.add(code);
        }
      }
      return next;
    });
  }, [content.deviceRealtimeMonitor]);

  const sectionNodes = {
    deviceRealtimeMonitor: (
      <DeviceRealtimeSection
        key="deviceRealtimeMonitor"
        drm={drm}
        alarmPulseDismissed={alarmPulseDismissed}
        setAlarmPulseDismissed={setAlarmPulseDismissed}
      />
    ),
    schedule: (
      <section className="screen-panel panel-span-8 schedule-panel" key="schedule">
        <div className="panel-header panel-header--schedule-only">
          <h2>{meta.areaName ? `${meta.areaName}工单甘特图` : "工单甘特图"}</h2>
          <span className="gantt-window-badge">
            {schedule?.display?.windowDaysLabel || `时间跨度${Math.max(Number(schedule?.windowDays) || 30, 1)}天`}
          </span>
        </div>
        <GanttBoard lineSchedules={scheduleRows} schedule={schedule} />
      </section>
    ),
    simulationPlaceholder:
      activePageKey === "schedule" ? (
        <ScheduleOverviewSide areaName={meta.areaName} riskItems={riskItems} lineSchedules={scheduleRows} />
      ) : (
        <section className="screen-panel panel-span-4 placeholder-panel simulation-panel" key="simulationPlaceholder">
          <div className="panel-header">
            <h2>3D 仿真占位区</h2>
            <span>
              一期后段
              {simulationOverflowing ? " · 自动滚动中" : ""}
            </span>
          </div>
          <div className="placeholder-copy placeholder-copy-wide simulation-placeholder-body" ref={simulationScrollRef}>
            <strong>{content.simulationPlaceholder?.title || "3D 仿真待一期后段接入"}</strong>
            <p>{content.simulationPlaceholder?.description || "当前阶段只保留预留区，不阻塞一期前段大屏。"}</p>
          </div>
        </section>
      ),
    energyData: <EnergyDashboardBoard key="energyData" bootstrap={content.energyData ?? {}} />,
  };

  return (
    <main className="screen-shell screen-right" onDoubleClick={fullscreenState.toggleFullscreen} ref={screenRef}>
      <ScreenHeader
        canFullscreen={fullscreenState.canFullscreen}
        currentTime={clock}
        isFullscreen={fullscreenState.isFullscreen}
        logoUrl={welcome.logoUrl}
        onToggleFullscreen={fullscreenState.toggleFullscreen}
        pageIndex={activePageIndex}
        pages={pages}
        screen={screen}
        setPageIndex={setActivePageIndex}
        statusNode={
          <ScreenStatus
            errorMessage={errorMessage}
            lastSuccessfulAt={{ value: meta.lastSuccessfulAt, display: meta.display }}
            usingFallback={meta.usingFallback}
          />
        }
        welcome={welcome}
      />

      <section className={`screen-page screen-grid screen-grid-right${isRealtimeOnlyPage ? " screen-grid-realtime" : ""}${isEnergyOnlyPage ? " screen-grid-energy" : ""}`}>
        {pages.length === 0 ? (
          <section className="screen-panel panel-span-12">
            <SectionEmpty title="未配置轮播页面" description="请在左右屏配置中设置 pageKeys。" />
          </section>
        ) : (
          pages.map((page, pageIndex) => {
            const sliceSections = resolveVisibleSections(page.sections ?? [], moduleSettings);
            const isSliceActive = pageIndex === activePageIndex;
            return (
              <ScreenCarouselPageContext.Provider key={page.key} value={{ isActive: isSliceActive }}>
                <div
                  className={`screen-page-slice${isSliceActive ? " screen-page-slice--active" : " screen-page-slice--hidden"}`}
                  aria-hidden={!isSliceActive}
                >
                  {sliceSections.length > 0 ? (
                    sliceSections.map((sectionKey) => {
                      const node = sectionNodes[sectionKey];
                      if (!node) return null;
                      return (
                        <Fragment key={`${page.key}-${sectionKey}`}>{node}</Fragment>
                      );
                    })
                  ) : (
                    <section className="screen-panel panel-span-12">
                      <SectionEmpty
                        title="当前轮播页没有可展示模块"
                        description="请检查该屏幕的 moduleSettings 或 pageKeys 配置。"
                      />
                    </section>
                  )}
                </div>
              </ScreenCarouselPageContext.Provider>
            );
          })
        )}
      </section>
    </main>
  );
}

function ScreenLoading({ screenKey }) {
  const screenName = screenKey === "left" ? "左屏" : "右屏";

  return (
    <main className="screen-shell screen-loading">
      <section className="screen-panel fallback-panel screen-loading-panel">
        <p className="screen-tag">HOTA MDS</p>
        <h1>{screenName}数据加载中…</h1>
        <p>正在获取展示数据（含设备实时监控等模块），请稍候。</p>
        <p className="screen-loading-hint">包含 OPC 实时监控时，首次请求可能稍慢。</p>
      </section>
    </main>
  );
}

function ScreenFallback({ areaCode, screenKey, errorMessage }) {
  const screenName = screenKey === "left" ? "左屏" : "右屏";
  const safeAreaCode = areaCode || "default";

  return (
    <main className="screen-shell screen-fallback">
      <section className="screen-panel fallback-panel">
        <p className="screen-tag">HOTA MDS</p>
        <h1>{screenName}展示页暂时不可用</h1>
        <p>{errorMessage || "后端展示接口暂时未返回数据。"}</p>
        <div className="quick-links" aria-label="快速入口">
          <a href={`/screen/${safeAreaCode}/left`}>{`/screen/${safeAreaCode}/left`}</a>
          <a href={`/screen/${safeAreaCode}/right`}>{`/screen/${safeAreaCode}/right`}</a>
          <a href="/admin/login">/admin/login</a>
        </div>
      </section>
    </main>
  );
}

const DEFAULT_SCREEN_POLL_SEC = 30;
const REALTIME_POLL_FLOOR_SEC = 2;

function resolveScreenPollSeconds(screenKey, payload) {
  const pageKeys = payload?.screen?.pageKeys ?? [];
  const hasRealtimePage = pageKeys.includes("realtime");
  const drmPoll = Number(payload?.content?.deviceRealtimeMonitor?.pollIntervalSeconds);

  if (hasRealtimePage || (Number.isFinite(drmPoll) && drmPoll > 0)) {
    const sec = Number.isFinite(drmPoll) && drmPoll > 0 ? drmPoll : REALTIME_POLL_FLOOR_SEC;
    return Math.max(sec, REALTIME_POLL_FLOOR_SEC);
  }

  return DEFAULT_SCREEN_POLL_SEC;
}

function ScreenDisplay({ areaCode, screenKey }) {
  const [payload, setPayload] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [pollIntervalMs, setPollIntervalMs] = useState(DEFAULT_SCREEN_POLL_SEC * 1000);
  const screenRef = useRef(null);
  const fullscreenState = useFullscreen(screenRef);

  useEffect(() => {
    let cancelled = false;

    async function loadScreen() {
      try {
        const nextPayload = await fetchScreenPayload(areaCode, screenKey);
        if (cancelled) {
          return;
        }
        setPayload(nextPayload);
        setPollIntervalMs(resolveScreenPollSeconds(screenKey, nextPayload) * 1000);
        setErrorMessage("");
      } catch (error) {
        if (cancelled) {
          return;
        }
        setErrorMessage(error.message || "screen request failed");
      }
    }

    loadScreen();
    const timerId = window.setInterval(loadScreen, pollIntervalMs);

    return () => {
      cancelled = true;
      window.clearInterval(timerId);
    };
  }, [areaCode, screenKey, pollIntervalMs]);

  if (!payload) {
    if (errorMessage) {
      return <ScreenFallback areaCode={areaCode} errorMessage={errorMessage} screenKey={screenKey} />;
    }
    return <ScreenLoading screenKey={screenKey} />;
  }

  if (screenKey === "left") {
    return (
      <LeftScreen
        errorMessage={errorMessage}
        fullscreenState={fullscreenState}
        payload={payload}
        screenRef={screenRef}
      />
    );
  }

  return (
    <RightScreen
      errorMessage={errorMessage}
      fullscreenState={fullscreenState}
      payload={payload}
      screenRef={screenRef}
    />
  );
}

export default ScreenDisplay;

import { formatRpm, RealtimeRobotColumn, RealtimeSpindleColumn, SpindleLoadRing } from "./shared.jsx";

function RealtimeCardShell({
  card,
  pulseOn,
  onDismissAlarm,
  children,
  footerExtra = null,
  modelLabel = null,
}) {
  const borderKey = card.machineStatus?.borderColor ?? "gray";
  return (
    <article
      className={`cnc-device-card cnc-device-card--border-${borderKey} ${pulseOn ? "cnc-device-card--pulse" : ""}`}
      onClick={onDismissAlarm}
    >
      {card.machineStatus?.alarmActive ? (
        <span className="cnc-alarm-icon" title="报警" aria-hidden="true">
          !
        </span>
      ) : null}
      <div className="cnc-device-head">
        <div className="cnc-device-head-text">
          <h3 className="cnc-device-title">{card.displayTitle || card.deviceName || card.sourceName}</h3>
          {card.subtitle ? <div className="cnc-device-subtitle">{card.subtitle}</div> : null}
          {modelLabel !== false ? (
            <div className="cnc-device-model">{modelLabel ?? `型号 ${card.deviceModel ?? "--"}`}</div>
          ) : null}
        </div>
        <div className="cnc-device-status">
          <span className={`cnc-status-dot cnc-status-dot--${card.machineStatus?.indicator ?? "gray"}`} />
          <span className="cnc-status-label">{card.machineStatus?.label ?? "--"}</span>
        </div>
      </div>
      {children}
      {footerExtra}
    </article>
  );
}

function RealtimeJobFooter({ job, formatDateTime, updatedAt, extraRows = null }) {
  return (
    <>
      <footer className="cnc-job-footer">
        <div className="cnc-job-program-row">
          <span className="cnc-job-k">当前程序</span>
          <span className="cnc-job-main">{job.mainProgram ?? "--"}</span>
          <span className="cnc-job-sep">·</span>
          <span className="cnc-job-k">行号</span>
          <span className="cnc-job-line">{job.exeLine ?? "--"}</span>
        </div>
        <div className="cnc-job-times">
          <div className="cnc-job-time-pill" title="累计有效切削时间">
            <span>切削</span>
            <strong>{job.cycleTimeFormatted ?? "--"}</strong>
          </div>
          <div className="cnc-job-time-pill" title="控制器开机时长">
            <span>开机</span>
            <strong>{job.operationTimeFormatted ?? "--"}</strong>
          </div>
          <span className={`cnc-mode-tag cnc-mode-tag--${String(job.workModeTag ?? "").toLowerCase()}`}>
            {job.workModeTag ?? "--"}
          </span>
        </div>
        {extraRows}
      </footer>
      <div className="cnc-device-foot-meta">{`更新 ${formatDateTime(updatedAt)}`}</div>
    </>
  );
}

function formatPct(value) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }
  const n = Number(value);
  if (Number.isNaN(n)) {
    return "--";
  }
  return `${Math.round(n)}%`;
}

export function SiemensBoringRealtimeCard({ card, pulseOn, onDismissAlarm, formatDateTime }) {
  const spindles = Array.isArray(card.spindles) ? card.spindles : [];
  const job = card.job ?? {};
  const mergeLayout = Boolean(card.mergeLayout && card.robot);
  const cncOffline = mergeLayout ? card.cncSourceStatus !== "online" : card.status !== "online";
  const robotOffline = mergeLayout ? card.robotSourceStatus !== "online" : true;

  return (
    <RealtimeCardShell card={card} pulseOn={pulseOn} onDismissAlarm={onDismissAlarm}>
      {mergeLayout ? (
        <div className="cnc-machine-split">
          <div className="cnc-machine-split-col">
            <RealtimeSpindleColumn deviceOffline={cncOffline} slot={spindles[0] ?? { label: "主轴", configured: false }} />
          </div>
          <div className="cnc-machine-split-vrule" aria-hidden="true" />
          <div className="cnc-machine-split-col">
            <RealtimeRobotColumn deviceOffline={robotOffline} robot={card.robot} />
          </div>
        </div>
      ) : (
        <div className="cnc-spindle-row">
          <RealtimeSpindleColumn deviceOffline={card.status !== "online"} slot={spindles[0] ?? { label: "主轴", configured: false }} />
        </div>
      )}
      <RealtimeJobFooter job={job} formatDateTime={formatDateTime} updatedAt={card.updatedAt} />
    </RealtimeCardShell>
  );
}

export function SyntecCncRealtimeCard({
  card,
  pulseOn,
  onDismissAlarm,
  formatDateTime,
  compact = false,
  lineLayout = false,
  titleOverride = null,
}) {
  const slot = (Array.isArray(card.spindles) ? card.spindles[0] : null) ?? { label: "主轴", configured: false };
  const job = card.job ?? {};
  const extras = card.syntecExtras ?? {};
  const ms = card.machineStatus ?? {};
  const offline = card.status !== "online";
  const loadPct = slot.loadPct;
  const loadDanger = loadPct != null && loadPct > 95;
  const title = titleOverride || card.displayTitle || card.sourceName || card.deviceName || "CNC";
  const indicator = ms.indicator ?? "gray";
  const fullName = card.displayTitle || card.sourceName || card.deviceName || "";
  const modelText =
    card.deviceModel && card.deviceModel !== "--" ? card.deviceModel : "新代 CNC";
  const metaText =
    lineLayout && titleOverride && fullName && fullName !== titleOverride
      ? fullName
      : `${modelText}${job.workModeTag && job.workModeTag !== "--" ? ` · ${job.workModeTag}` : ""}`;

  return (
    <article
      className={`syntec-card ${lineLayout ? "syntec-card--line" : ""} ${compact ? "syntec-card--compact" : ""} syntec-card--${indicator} ${pulseOn ? "syntec-card--pulse" : ""}`}
      onClick={onDismissAlarm}
    >
      {ms.alarmActive ? <span className="syntec-alarm-badge">!</span> : null}

      <header className="syntec-head">
        <div className="syntec-head-main">
          <h3 className="syntec-title" title={fullName || title}>
            {title}
          </h3>
          <p className="syntec-meta">{metaText}</p>
        </div>
        <div className={`syntec-state syntec-state--${indicator}`}>{ms.label ?? "--"}</div>
      </header>

      <div className="syntec-dash">
        <div className="syntec-dash-rpm">
          <span className="syntec-dash-label">主轴转速</span>
          <div className="syntec-dash-rpm-val">
            <strong>{offline ? "--" : formatRpm(slot.actSpeedRpm)}</strong>
            <em>rpm</em>
          </div>
        </div>
        <div className="syntec-dash-load">
          <span className="syntec-dash-label">负载</span>
          <SpindleLoadRing pct={offline ? null : loadPct} danger={loadDanger} />
        </div>
        <div className="syntec-dash-feed">
          <span className="syntec-dash-label">转速倍率</span>
          <strong>{offline ? "--" : formatPct(slot.speedOverridePct)}</strong>
        </div>
      </div>

      <div className="syntec-prog">
        <div className="syntec-prog-main">
          <span className="syntec-prog-label">程序</span>
          <span className="syntec-prog-name" title={job.mainProgram ?? ""}>
            {job.mainProgram ?? "--"}
          </span>
        </div>
        <div className="syntec-prog-line">
          <span className="syntec-prog-label">行号</span>
          <span>{job.exeLine ?? "--"}</span>
        </div>
        <div className="syntec-prog-time">
          <span>开机 {job.operationTimeFormatted ?? "--"}</span>
        </div>
      </div>

      <div className="syntec-tags">
        {extras.toolId != null ? <span>T{extras.toolId}</span> : <span>T--</span>}
        {extras.totalPartCount != null ? <span>产量 {extras.totalPartCount}</span> : <span>产量 --</span>}
        {extras.feedOverridePct != null ? (
          <span>进给 {formatPct(extras.feedOverridePct)}</span>
        ) : (
          <span>进给 --</span>
        )}
        {extras.cmdOverridePct != null ? (
          <span>指令 {formatPct(extras.cmdOverridePct)}</span>
        ) : (
          <span>指令 --</span>
        )}
      </div>

      {extras.currentAlarm ? (
        <div className="syntec-alarm-text" title={extras.currentAlarm}>
          {extras.currentAlarm}
        </div>
      ) : null}

      <footer className="syntec-foot">{formatDateTime(card.updatedAt)}</footer>
    </article>
  );
}

export function ParameterGridRealtimeCard({ card, pulseOn, onDismissAlarm, formatDateTime }) {
  const groups = card.groupedParameters ?? [];
  return (
    <RealtimeCardShell card={card} pulseOn={pulseOn} onDismissAlarm={onDismissAlarm} modelLabel={false}>
      <div className="cnc-param-grid">
        {groups.length > 0 ? (
          groups.map((group) => (
            <section className="cnc-param-group" key={group.groupKey || group.groupLabel}>
              <h4 className="cnc-param-group-title">{group.groupLabel || group.groupKey}</h4>
              <div className="cnc-param-group-items">
                {(group.items ?? []).map((item, idx) => (
                  <div className="cnc-param-line" key={`${item.comment}-${idx}`}>
                    <span className="cnc-param-k">{item.comment}</span>
                    <span className={`cnc-param-v ${item.ok ? "" : "cnc-param-v--bad"}`}>
                      {item.ok ? item.value : "获取失败"}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          ))
        ) : (
          <p className="cnc-robot-empty">暂无节点数据</p>
        )}
      </div>
      <div className="cnc-device-foot-meta">{`更新 ${formatDateTime(card.updatedAt)}`}</div>
    </RealtimeCardShell>
  );
}

export function RealtimeDeviceCard({ card, pulseOn, onDismissAlarm, formatDateTime, compact = false }) {
  const template = card.dashboardTemplate || "siemens_boring";
  if (template === "syntec_cnc" || template === "syntec_cnc_compact") {
    return (
      <SyntecCncRealtimeCard
        card={card}
        pulseOn={pulseOn}
        onDismissAlarm={onDismissAlarm}
        formatDateTime={formatDateTime}
        compact={compact || template === "syntec_cnc_compact"}
      />
    );
  }
  if (template === "parameter_grid") {
    return (
      <ParameterGridRealtimeCard
        card={card}
        pulseOn={pulseOn}
        onDismissAlarm={onDismissAlarm}
        formatDateTime={formatDateTime}
      />
    );
  }
  return (
    <SiemensBoringRealtimeCard
      card={card}
      pulseOn={pulseOn}
      onDismissAlarm={onDismissAlarm}
      formatDateTime={formatDateTime}
    />
  );
}

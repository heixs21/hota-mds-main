import { RealtimeRobotColumn } from "./shared.jsx";
import { SyntecCncRealtimeCard } from "./RealtimeCards.jsx";

function S7BinBox({ label, value }) {
  return (
    <div className="xz-robot-bin">
      <span className="xz-robot-bin-label">{label}</span>
      <strong className="xz-robot-bin-value">{value ?? "0"}</strong>
    </div>
  );
}

export function S7RobotLineCard({ card, stationLabel, pulseOn, onDismissAlarm, formatDateTime }) {
  const ms = card.machineStatus ?? {};
  const extras = card.s7Extras ?? {};
  const offline = card.status !== "online";
  const indicator = offline ? "gray" : (ms.indicator ?? "gray");
  const title = card.displayTitle || card.sourceName || stationLabel || "机器手";
  const fullName = card.sourceName || card.displayTitle || title;
  const items = card.robot?.items ?? [];

  return (
    <article
      className={`syntec-card syntec-card--line syntec-card--robot syntec-card--${indicator} ${pulseOn ? "syntec-card--pulse" : ""}`}
      onClick={onDismissAlarm}
    >
      <header className="syntec-head">
        <div className="syntec-head-main">
          <h3 className="syntec-title" title={fullName}>
            {title}
          </h3>
          <p className="syntec-meta">S7 机器手 · {fullName}</p>
        </div>
        <div className={`syntec-state syntec-state--${indicator}`}>{offline ? "离线" : (ms.label ?? "--")}</div>
      </header>

      <div className="xz-robot-bins">
        <S7BinBox label="东北框" value={extras.neCount} />
        <S7BinBox label="西南框" value={extras.swCount} />
      </div>

      <div className="xz-robot-panel">
        <RealtimeRobotColumn robot={card.robot} deviceOffline={offline} />
      </div>

      {extras.materialCode ? (
        <div className="xz-robot-material" title={extras.materialCode}>
          物料编码 {extras.materialCode}
        </div>
      ) : null}

      {!offline && items.length === 0 ? <p className="cnc-robot-empty">暂无节点数据</p> : null}

      <footer className="syntec-foot">{formatDateTime(card.updatedAt)}</footer>
    </article>
  );
}

export function StationPlaceholderCard({ card, stationLabel }) {
  const title = stationLabel || card.displayTitle || "工位";
  return (
    <article className="syntec-card syntec-card--line syntec-card--gray xz-line-placeholder">
      <header className="syntec-head">
        <div className="syntec-head-main">
          <h3 className="syntec-title">{title}</h3>
          <p className="syntec-meta">待接入数据源</p>
        </div>
        <div className="syntec-state syntec-state--gray">待接入</div>
      </header>
      <div className="xz-line-placeholder-body">
        <span className="xz-line-placeholder-icon" aria-hidden="true">
          ○
        </span>
        <p>{card.offlineReason || "尚未绑定 OPC / S7 数据源"}</p>
      </div>
    </article>
  );
}

export function XiaozhouLineStation({ station, pulseOn, onDismissAlarm, formatDateTime }) {
  const card = station.card ?? {};
  const template = card.dashboardTemplate || "station_placeholder";
  const stationLabel = station.label || card.displayTitle;

  if (station.pending || template === "station_placeholder") {
    return <StationPlaceholderCard card={card} stationLabel={stationLabel} />;
  }
  if (template === "s7_robot") {
    return (
      <S7RobotLineCard
        card={card}
        stationLabel={stationLabel}
        pulseOn={pulseOn}
        onDismissAlarm={onDismissAlarm}
        formatDateTime={formatDateTime}
      />
    );
  }

  return (
    <SyntecCncRealtimeCard
      card={card}
      pulseOn={pulseOn}
      onDismissAlarm={onDismissAlarm}
      formatDateTime={formatDateTime}
      lineLayout
    />
  );
}

export function XiaozhouLineRow({ line, alarmPulseDismissed, setAlarmPulseDismissed, formatDateTime }) {
  const stationCount = (line.stations ?? []).length || 7;
  const trackClass =
    stationCount < 7 ? "xz-line-track xz-line-track--align-end" : "xz-line-track";
  return (
    <section className="xz-line-row" aria-label={line.lineLabel || "产线"}>
      <div className="xz-line-row-label">{line.lineLabel}</div>
      <div className={trackClass}>
        {(line.stations ?? []).map((station) => {
          const card = station.card ?? {};
          const pulseOn = Boolean(card.machineStatus?.alarmActive) && !alarmPulseDismissed.has(card.sourceCode);
          return (
            <div className="xz-line-slot" key={`${line.lineNumber}-${station.stationKey}`}>
              <XiaozhouLineStation
                station={station}
                pulseOn={pulseOn}
                formatDateTime={formatDateTime}
                onDismissAlarm={() => {
                  if (card.machineStatus?.alarmActive && card.sourceCode) {
                    setAlarmPulseDismissed((prev) => new Set(prev).add(card.sourceCode));
                  }
                }}
              />
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function XiaozhouLineRealtimeBoard({ drm, alarmPulseDismissed, setAlarmPulseDismissed, formatDateTime }) {
  const lines = drm.lines ?? [];
  return (
    <section className="screen-panel panel-span-12 panel-unbounded industrial-realtime-panel xz-line-panel" key="deviceRealtimeMonitor">
      <div className="xz-line-board">
        {lines.length > 0 ? (
          lines.map((line) => (
            <XiaozhouLineRow
              key={line.lineNumber}
              line={line}
              alarmPulseDismissed={alarmPulseDismissed}
              setAlarmPulseDismissed={setAlarmPulseDismissed}
              formatDateTime={formatDateTime}
            />
          ))
        ) : (
          <p className="xz-line-empty">当前未配置销轴产线数据源，请在子页面绑定 S7 机器手或 CNC 数据源。</p>
        )}
      </div>
    </section>
  );
}

import { SyntecCncRealtimeCard } from "./RealtimeCards.jsx";
import { StationPlaceholderCard } from "./XiaozhouLineBoard.jsx";

function TaotongGunziLineStation({ station, pulseOn, onDismissAlarm, formatDateTime }) {
  if (station.empty) {
    return <div className="ttgz-line-slot ttgz-line-slot--empty" aria-hidden="true" />;
  }

  const card = station.card ?? {};
  const template = card.dashboardTemplate || "station_placeholder";
  const stationLabel = station.label || card.displayTitle;

  if (station.pending || template === "station_placeholder") {
    return <StationPlaceholderCard card={card} stationLabel={stationLabel} />;
  }

  return (
    <SyntecCncRealtimeCard
      card={card}
      pulseOn={pulseOn}
      onDismissAlarm={onDismissAlarm}
      formatDateTime={formatDateTime}
      lineLayout
      titleOverride={stationLabel}
    />
  );
}

export function TaotongGunziLineRow({ line, alarmPulseDismissed, setAlarmPulseDismissed, formatDateTime }) {
  return (
    <section className="ttgz-line-row" aria-label={line.lineLabel || "产线"}>
      <div className="ttgz-line-row-label">{line.lineLabel}</div>
      <div className="ttgz-line-track">
        {(line.stations ?? []).map((station) => {
          const card = station.card ?? {};
          const pulseOn = Boolean(card.machineStatus?.alarmActive) && !alarmPulseDismissed.has(card.sourceCode);
          return (
            <div
              className={`ttgz-line-slot${station.empty ? " ttgz-line-slot--empty" : ""}`}
              key={`${line.lineNumber}-${station.stationKey}`}
            >
              <TaotongGunziLineStation
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

export function TaotongGunziLineRealtimeBoard({ drm, alarmPulseDismissed, setAlarmPulseDismissed, formatDateTime }) {
  const lines = drm.lines ?? [];
  return (
    <section
      className="screen-panel panel-span-12 panel-unbounded industrial-realtime-panel ttgz-line-panel"
      key="deviceRealtimeMonitor"
    >
      <div className="ttgz-line-board">
        {lines.length > 0 ? (
          lines.map((line) => (
            <TaotongGunziLineRow
              key={line.lineNumber}
              line={line}
              alarmPulseDismissed={alarmPulseDismissed}
              setAlarmPulseDismissed={setAlarmPulseDismissed}
              formatDateTime={formatDateTime}
            />
          ))
        ) : (
          <p className="ttgz-line-empty">当前未配置套筒滚子 OPC UA 数据源，请在子页面绑定 DS-02001 起的机床数据源。</p>
        )}
      </div>
    </section>
  );
}

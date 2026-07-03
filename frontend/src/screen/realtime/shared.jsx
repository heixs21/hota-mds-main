/** 设备实时监控 — 镗孔/新代等模板共用的主轴、机器人列组件 */

export function formatRpm(value) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }
  const n = Number(value);
  if (Number.isNaN(n)) {
    return "--";
  }
  return Math.round(n).toLocaleString("zh-CN");
}

export function SpindleLoadRing({ pct, danger }) {
  const n = pct == null || Number.isNaN(Number(pct)) ? null : Math.min(100, Math.max(0, Number(pct)));
  const r = 38;
  const c = 2 * Math.PI * r;
  const offset = n == null ? c : c * (1 - n / 100);
  const label = n == null ? "--" : `${Math.round(n)}%`;

  return (
    <div className="cnc-load-ring-wrap">
      <svg className="cnc-load-ring-svg" viewBox="0 0 100 100" aria-hidden="true">
        <circle className="cnc-load-ring-track" cx="50" cy="50" r={r} fill="none" strokeWidth="10" />
        <circle
          className={danger ? "cnc-load-ring-fill cnc-load-ring-fill--danger" : "cnc-load-ring-fill"}
          cx="50"
          cy="50"
          r={r}
          fill="none"
          strokeWidth="10"
          strokeDasharray={c}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
        />
      </svg>
      <span className={`cnc-load-ring-label ${danger ? "cnc-load-ring-label--danger" : ""}`}>{label}</span>
    </div>
  );
}

function opcRobotRowActive(row) {
  if (!row || !row.ok) {
    return false;
  }
  const v = row.value;
  if (v === true) {
    return true;
  }
  if (v === false || v === null || v === undefined) {
    return false;
  }
  const s = String(v).trim().toLowerCase();
  if (s === "true" || s === "1" || s === "yes" || s === "是" || s === "on") {
    return true;
  }
  if (s === "false" || s === "0" || s === "no" || s === "否" || s === "off" || s === "") {
    return false;
  }
  const n = Number(s);
  if (!Number.isNaN(n)) {
    return n !== 0;
  }
  return Boolean(v);
}

function robotStatusKindFromComment(comment) {
  const raw = (comment || "").trim();
  if (!raw) {
    return null;
  }
  if (/故障|fault|alarm/i.test(raw)) {
    return "fault";
  }
  if (/停止|stop|非运行/i.test(raw)) {
    return "stop";
  }
  if (/运行|run/i.test(raw)) {
    return "run";
  }
  return null;
}

function RobotRunStopFaultLights({ runRow, stopRow, faultRow }) {
  const runOn = opcRobotRowActive(runRow);
  const stopOn = opcRobotRowActive(stopRow);
  const faultOn = opcRobotRowActive(faultRow);
  return (
    <div className="cnc-robot-status-bar" role="group" aria-label="机器人运行状态">
      <div className="cnc-robot-status-lamps">
        <div className="cnc-robot-lamp-slot">
          <span
            className={`cnc-robot-lamp cnc-robot-lamp--run ${runOn ? "is-on" : ""} ${
              runRow && runRow.ok === false ? "is-err" : ""
            }`}
            title={runRow?.ok === false ? "运行 — 读取失败" : "运行"}
            aria-hidden="true"
          />
          <span className="cnc-robot-lamp-cap">运行</span>
        </div>
        <div className="cnc-robot-lamp-slot">
          <span
            className={`cnc-robot-lamp cnc-robot-lamp--stop ${stopOn ? "is-on" : ""} ${
              stopRow && stopRow.ok === false ? "is-err" : ""
            }`}
            title={stopRow?.ok === false ? "停止 — 读取失败" : "停止"}
            aria-hidden="true"
          />
          <span className="cnc-robot-lamp-cap">停止</span>
        </div>
        <div className="cnc-robot-lamp-slot">
          <span
            className={`cnc-robot-lamp cnc-robot-lamp--fault ${faultOn ? "is-on" : ""} ${
              faultRow && faultRow.ok === false ? "is-err" : ""
            }`}
            title={faultRow?.ok === false ? "故障 — 读取失败" : "故障"}
            aria-hidden="true"
          />
          <span className="cnc-robot-lamp-cap">故障</span>
        </div>
      </div>
    </div>
  );
}

export function RealtimeRobotColumn({ robot, deviceOffline }) {
  if (!robot) {
    return null;
  }
  if (deviceOffline) {
    return (
      <div className="cnc-robot-col cnc-robot-col--offline">
        <div className="cnc-robot-col-head">{robot.displayTitle || "机器人"}</div>
        <p className="cnc-spindle-offline-msg">离线</p>
      </div>
    );
  }
  const rows = robot.items ?? [];
  let runRow;
  let stopRow;
  let faultRow;
  const plainRows = [];
  for (const row of rows) {
    const kind = robotStatusKindFromComment(row.comment);
    if (kind === "run" && runRow === undefined) {
      runRow = row;
    } else if (kind === "stop" && stopRow === undefined) {
      stopRow = row;
    } else if (kind === "fault" && faultRow === undefined) {
      faultRow = row;
    } else {
      plainRows.push(row);
    }
  }
  const hasStatusLights = runRow !== undefined || stopRow !== undefined || faultRow !== undefined;

  return (
    <div className="cnc-robot-col">
      <div className="cnc-robot-col-head">{robot.displayTitle || "机器人"}</div>
      {rows.length > 0 ? (
        <>
          {hasStatusLights ? (
            <RobotRunStopFaultLights faultRow={faultRow} runRow={runRow} stopRow={stopRow} />
          ) : null}
          {plainRows.length > 0 ? (
            <div className="cnc-robot-plain-stack">
              {plainRows.map((row, idx) => (
                <div className="cnc-robot-plain-line" key={`${row.comment}-${idx}`}>
                  <span className="cnc-robot-plain-k">{row.comment}</span>
                  <span className={`cnc-robot-plain-v ${row.ok ? "" : "cnc-robot-plain-v--bad"}`}>
                    {row.ok ? row.value : "获取失败"}
                  </span>
                </div>
              ))}
            </div>
          ) : null}
          {!hasStatusLights && plainRows.length === 0 ? <p className="cnc-robot-empty">暂无节点数据</p> : null}
        </>
      ) : (
        <p className="cnc-robot-empty">暂无节点数据</p>
      )}
    </div>
  );
}

export function RealtimeSpindleColumn({ slot, deviceOffline, hideTemperature = false }) {
  if (deviceOffline) {
    return (
      <div className="cnc-spindle-col cnc-spindle-col--offline">
        <div className="cnc-spindle-col-head">{slot.label}</div>
        <p className="cnc-spindle-offline-msg">离线</p>
      </div>
    );
  }

  const ovr = slot.speedOverridePct;
  const ovrWarn = ovr != null && ovr < 99.5;
  const cmd = slot.cmdSpeedRpm;
  const loadPct = slot.loadPct;
  const loadDanger = loadPct != null && loadPct > 95;

  return (
    <div className={`cnc-spindle-col ${slot.configured ? "" : "cnc-spindle-col--empty"}`}>
      <div className="cnc-spindle-col-head">{slot.label}</div>
      {!slot.configured ? (
        <p className="cnc-spindle-unconfigured">未配置</p>
      ) : (
        <>
          <div className="cnc-spindle-rpm">
            <span className="cnc-spindle-rpm-value">{formatRpm(slot.actSpeedRpm)}</span>
            <span className="cnc-spindle-rpm-unit">rpm</span>
          </div>
          <div className={`cnc-spindle-ovr ${ovrWarn ? "cnc-spindle-ovr--warn" : ""}`}>
            倍率 {ovr != null ? `${Math.round(ovr)}%` : "--"}
          </div>
          {cmd != null ? (
            <div className="cnc-spindle-cmd">S 指令: {`${formatRpm(cmd)} rpm`}</div>
          ) : null}
          <div className="cnc-spindle-load-row">
            <span className="cnc-spindle-load-cap">负载</span>
            <SpindleLoadRing pct={loadPct} danger={loadDanger} />
          </div>
          {!hideTemperature ? (
            <div className="cnc-spindle-extra">
              <span className={slot.temperatureC != null && slot.temperatureC > 85 ? "cnc-spindle-extra-warn" : ""}>
                温度 {slot.temperatureC != null ? `${Number(slot.temperatureC).toFixed(1)} °C` : "-- °C"}
              </span>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

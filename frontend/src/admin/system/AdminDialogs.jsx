import { useEffect, useState } from "react";

import { apiRequest } from "../../adminApi.js";

/**
 * 「系统设置」侧：数据源历史、设备详情等弹窗。
 */
export function HistoryDialog({ resourceDefinition, item, token, onClose, onUnauthorized, showToast }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      try {
        const response = await apiRequest(
          `${resourceDefinition.endpoint}/${item.id}/history?page=${page}&pageSize=${pageSize}`,
          { token },
        );
        if (cancelled) return;
        setItems(response.data.items ?? []);
        setTotal(response.data.total ?? 0);
      } catch (error) {
        if (cancelled) return;
        if (error.status === 401) {
          onUnauthorized();
          return;
        }
        showToast(error.message || "历史数据加载失败", { variant: "error" });
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [item.id, page, pageSize, resourceDefinition.endpoint, token, onUnauthorized, showToast]);

  function formatTime(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    const pad = (n) => String(n).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      onClose();
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="modal-backdrop" onMouseDown={handleBackdropClick}>
      <div className="modal-dialog modal-dialog--wide" role="dialog" aria-modal="true" aria-label="OPC UA 历史数据">
        <div className="modal-header">
          <h3>OPC UA 历史数据 - {item.name || item.code}</h3>
          <button aria-label="关闭" className="modal-close" onClick={onClose} type="button">
            ×
          </button>
        </div>

        <div className="modal-body modal-body--table">
          {isLoading ? (
            <div className="modal-empty">正在加载...</div>
          ) : items.length === 0 ? (
            <div className="modal-empty">该数据源暂无历史数据</div>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>采样时间</th>
                    <th>节点 ID</th>
                    <th>采样值</th>
                    <th>质量</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((row) => (
                    <tr key={row.id}>
                      <td>{formatTime(row.sampledAt)}</td>
                      <td>{row.nodeId}</td>
                      <td>{row.value}</td>
                      <td>{row.qualityLabel || row.quality}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="modal-footer modal-footer--between">
          <div className="table-pagination-meta">
            共 {total} 条，当前第 {page}/{totalPages} 页
          </div>
          <div className="table-pagination-actions">
            <label className="table-page-size">
              每页
              <select
                value={pageSize}
                onChange={(event) => {
                  setPage(1);
                  setPageSize(Number(event.target.value));
                }}
              >
                {[10, 20, 50].map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
              条
            </label>
            <button disabled={page <= 1 || isLoading} onClick={() => setPage(page - 1)} type="button">
              上一页
            </button>
            <button disabled={page >= totalPages || isLoading} onClick={() => setPage(page + 1)} type="button">
              下一页
            </button>
            <button className="ghost-button" onClick={onClose} type="button">
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function DeviceDetailDialog({ device, onClose }) {
  if (!device) {
    return null;
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      onClose();
    }
  }

  const fields = [
    ["编码", device.code],
    ["名称", device.name],
    ["设备IP", device.ip],
    ["区域", device.areaName],
    ["产线", device.productionLineName],
    ["状态", device.defaultStatus],
    ["启用", device.isActive ? "是" : "否"],
    ["备注", device.notes],
  ];

  return (
    <div className="modal-backdrop" onMouseDown={handleBackdropClick}>
      <div className="modal-dialog modal-dialog--device-detail" role="dialog" aria-modal="true" aria-label="设备详情">
        <div className="modal-header">
          <h3>设备详情</h3>
          <button aria-label="关闭" className="modal-close" onClick={onClose} type="button">
            ×
          </button>
        </div>
        <div className="modal-body">
          <div className="device-detail-grid">
            {fields.map(([label, value]) => (
              <div
                className={`device-detail-item${label === "备注" ? " device-detail-item--full" : ""}`}
                key={label}
              >
                <div className="device-detail-label">{label}</div>
                <div className="device-detail-value">{value === undefined || value === "" ? "—" : String(value)}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="modal-footer">
          <button className="ghost-button" onClick={onClose} type="button">
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}

import { Button, Descriptions, Modal, Table } from "antd";
import { useEffect, useMemo, useState } from "react";

import { apiRequest } from "../../adminApi.js";
import {
  ADMIN_TABLE_PAGE_SIZE_CHANGER,
  ADMIN_TABLE_PAGE_SIZE_OPTIONS,
  buildRowIndexColumn,
} from "../adminUtils.js";

/**
 * 「系统设置」侧：数据源历史、设备详情等弹窗。
 */
function formatHistoryPayload(payload) {
  if (payload == null || payload === "") {
    return "(空)";
  }
  if (typeof payload === "string") {
    return payload;
  }
  try {
    return JSON.stringify(payload, null, 2);
  } catch {
    return String(payload);
  }
}

function formatTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

export function HistoryDialog({ resourceDefinition, item, token, onClose, onUnauthorized, showToast }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [payloadDetailRow, setPayloadDetailRow] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      try {
        const response = await apiRequest(
          `${resourceDefinition.endpoint}/${item.id}/history?page=${page}&pageSize=${pageSize}`,
          { token },
        );
        if (cancelled) {
          return;
        }
        setItems(response.data.items ?? []);
        setTotal(response.data.total ?? 0);
      } catch (error) {
        if (cancelled) {
          return;
        }
        if (error.status === 401) {
          onUnauthorized();
          return;
        }
        showToast(error.message || "历史数据加载失败", { variant: "error" });
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [item.id, page, pageSize, resourceDefinition.endpoint, token, onUnauthorized, showToast]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const columns = useMemo(
    () => [
      buildRowIndexColumn(page, pageSize),
      {
        title: "获取时间",
        dataIndex: "fetchedAt",
        key: "fetchedAt",
        width: 170,
        render: (value) => formatTime(value),
      },
      {
        title: "设备",
        key: "device",
        ellipsis: true,
        render: (_, row) => row.deviceName || row.deviceCode || "-",
      },
      {
        title: "成功",
        dataIndex: "readOk",
        key: "readOk",
        width: 72,
        render: (value) => (value ? "是" : "否"),
      },
      {
        title: "离线",
        dataIndex: "offline",
        key: "offline",
        width: 72,
        render: (value) => (value ? "是" : "否"),
      },
      {
        title: "耗时(ms)",
        dataIndex: "durationMs",
        key: "durationMs",
        width: 96,
        render: (value) => (value != null ? value : "-"),
      },
      {
        title: "来源",
        dataIndex: "trigger",
        key: "trigger",
        width: 100,
        render: (value) => value || "-",
      },
      {
        title: "摘要",
        dataIndex: "failureSummary",
        key: "failureSummary",
        ellipsis: true,
        render: (value, row) => value || (row.readOk ? "正常" : "失败"),
      },
      {
        title: "操作",
        key: "actions",
        fixed: "right",
        width: 110,
        render: (_, row) => (
          <Button onClick={() => setPayloadDetailRow(row)} size="small" type="link">
            查看详情
          </Button>
        ),
      },
    ],
    [page, pageSize],
  );

  return (
    <>
      <Modal
        destroyOnClose
        footer={
          <Button onClick={onClose} type="default">
            关闭
          </Button>
        }
        onCancel={onClose}
        open
        title={`OPC UA 历史数据 - ${item.name || item.code}`}
        width={1200}
      >
        <Table
          columns={columns}
          dataSource={items}
          loading={isLoading}
          locale={{ emptyText: isLoading ? "正在加载..." : "该数据源暂无历史数据" }}
          pagination={{
            current: page,
            onChange: (nextPage, nextPageSize) => {
              setPage(nextPage);
              setPageSize(nextPageSize);
            },
            pageSize,
            pageSizeOptions: ADMIN_TABLE_PAGE_SIZE_OPTIONS,
            showSizeChanger: ADMIN_TABLE_PAGE_SIZE_CHANGER,
            showTotal: () => `共 ${total} 条，当前第 ${page}/${totalPages} 页`,
            total,
          }}
          rowKey="id"
          scroll={{ x: "max-content" }}
          size="small"
        />
      </Modal>

      <Modal
        destroyOnClose
        footer={
          <Button onClick={() => setPayloadDetailRow(null)} type="default">
            关闭
          </Button>
        }
        onCancel={() => setPayloadDetailRow(null)}
        open={Boolean(payloadDetailRow)}
        title="读数明细（payload）"
        width={860}
      >
        <pre className="resource-crud-readonly-detail">{formatHistoryPayload(payloadDetailRow?.payload)}</pre>
      </Modal>
    </>
  );
}

export function DeviceDetailDialog({ device, onClose }) {
  if (!device) {
    return null;
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
    <Modal
      destroyOnClose
      footer={
        <Button onClick={onClose} type="default">
          关闭
        </Button>
      }
      onCancel={onClose}
      open
      title="设备详情"
      width={640}
    >
      <Descriptions bordered column={2} size="small">
        {fields.map(([label, fieldValue]) => (
          <Descriptions.Item
            key={label}
            label={label}
            span={label === "备注" ? 2 : 1}
          >
            {fieldValue === undefined || fieldValue === "" ? "—" : String(fieldValue)}
          </Descriptions.Item>
        ))}
      </Descriptions>
    </Modal>
  );
}

import { CopyOutlined, DeleteOutlined, EditOutlined, LinkOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Drawer, Form, InputNumber, Modal, Popconfirm, Select, Space, Table, Typography, message } from "antd";
import { useCallback, useMemo, useRef } from "react";

import { formatCellValue, stringifyJson, collectBooleanFieldKeys } from "../../adminResources.js";
import { useAdminSession } from "../context/AdminSessionContext.jsx";
import { buildRowIndexColumn } from "../adminUtils.js";
import { useResourceCrud } from "../hooks/useResourceCrud.js";
import { useTableBodyScrollY } from "../hooks/useTableBodyScrollY.js";
import { DeviceDetailDialog, HistoryDialog } from "../system/AdminDialogs.jsx";
import { AntResourceModalForm } from "./AntResourceModalForm.jsx";
import { AntResourceQueryBar } from "./AntResourceQueryBar.jsx";
import { BooleanSwitchCell } from "./BooleanSwitchCell.jsx";
import { ColumnTitleWithHint } from "./ColumnTitleWithHint.jsx";
import { ScreenKeyTag } from "./ScreenKeyTag.jsx";

function notifyFromAntd({ text, variant }) {
  const fn = message[variant] ?? message.info;
  fn(text);
}

function buildBulkToolbarExtra(crud) {
  const bt = crud.resourceDefinition.bulkApplyToolbar;
  if (!bt) {
    return null;
  }

  const disabled = crud.isLoading || crud.isBulkRefreshing || crud.checkedIds.size === 0;

  if (bt.fields?.length) {
    return bt.fields
      .map((field) => (
        <Form.Item key={field.key} label={field.label}>
          <InputNumber
            disabled={crud.isLoading || crud.isBulkRefreshing}
            max={field.max}
            min={field.min}
            onChange={(value) =>
              crud.setBulkToolbarMulti((prev) => ({
                ...prev,
                [field.key]: value ?? "",
              }))
            }
            step={field.step}
            value={crud.bulkToolbarMulti[field.key] ?? null}
          />
        </Form.Item>
      ))
      .concat(
        <Form.Item key="bulk-apply">
          <Button disabled={disabled} loading={crud.isBulkRefreshing} onClick={crud.handleBulkToolbarApply}>
            批量设置
          </Button>
        </Form.Item>,
      );
  }

  if (bt.inputKind === "booleanSelect") {
    return (
      <>
        <Form.Item label={bt.label}>
          <Select
            disabled={crud.isLoading || crud.isBulkRefreshing}
            onChange={crud.setBulkToolbarInput}
            options={bt.selectOptions ?? []}
            placeholder={`请选择${bt.label}`}
            style={{ minWidth: 120 }}
            value={crud.bulkToolbarInput || undefined}
          />
        </Form.Item>
        <Form.Item>
          <Button disabled={disabled} loading={crud.isBulkRefreshing} onClick={crud.handleBulkToolbarApply}>
            批量设置
          </Button>
        </Form.Item>
      </>
    );
  }

  return (
    <>
      <Form.Item label={bt.label}>
        <InputNumber
          disabled={crud.isLoading || crud.isBulkRefreshing}
          max={bt.max}
          min={bt.min}
          onChange={(value) => crud.setBulkToolbarInput(value ?? "")}
          step={1}
          value={crud.bulkToolbarInput === "" ? null : Number(crud.bulkToolbarInput)}
        />
      </Form.Item>
      <Form.Item>
        <Button disabled={disabled} loading={crud.isBulkRefreshing} onClick={crud.handleBulkToolbarApply}>
          批量设置
        </Button>
      </Form.Item>
    </>
  );
}

export default function ResourceCrudPage({ resourceKey }) {
  const { onUnauthorized, token } = useAdminSession();
  const notify = useCallback((payload) => notifyFromAntd(payload), []);
  const crud = useResourceCrud({ resourceKey, token, onUnauthorized, notify });
  const { resourceDefinition } = crud;
  const tableWrapRef = useRef(null);
  const tableScrollY = useTableBodyScrollY(tableWrapRef, [
    resourceKey,
    crud.isLoading,
    crud.items.length,
    crud.page,
    crud.pageSize,
    resourceDefinition.queryFields?.length ?? 0,
    Boolean(resourceDefinition.bulkApplyToolbar),
  ]);

  const booleanFieldKeys = useMemo(
    () => collectBooleanFieldKeys(resourceDefinition.fields),
    [resourceDefinition.fields],
  );

  const columns = useMemo(() => {
    const nextColumns = [
      buildRowIndexColumn(crud.page, crud.pageSize),
      ...resourceDefinition.columns.map((column) => {
        const isBooleanColumn = booleanFieldKeys.has(column.key);
        return {
      title: <ColumnTitleWithHint hint={column.columnHint} label={column.label} />,
      dataIndex: column.key,
      key: column.key,
      width: column.width ?? (isBooleanColumn ? 80 : undefined),
      align: isBooleanColumn ? "center" : undefined,
      ellipsis: column.width ? false : !isBooleanColumn,
      render: (value, record) => {
        if (isBooleanColumn) {
          return (
            <BooleanSwitchCell
              checked={value}
              disabled={resourceDefinition.readOnly || crud.isLoading || crud.isSaving}
              loading={crud.isInlineBooleanPatching(record.id, column.key)}
              onChange={(nextValue) => crud.handleInlineBooleanToggle(record, column.key, nextValue)}
            />
          );
        }
        if (column.cellFormat === "screenKeyTag") {
          return <ScreenKeyTag value={value} />;
        }
        if (column.cellFormat === "resourceLinks" && Array.isArray(record[column.key])) {
          if (record[column.key].length === 0) {
            return "-";
          }
          return (
            <Space direction="vertical" size={4}>
              {record[column.key].map((linkedItem) => (
                <Button
                  icon={<LinkOutlined />}
                  key={`${column.key}-${linkedItem.id}`}
                  onClick={() => crud.handleOpenResourceItem(column.resource, linkedItem.id)}
                  size="small"
                  type="link"
                >
                  {linkedItem.name || linkedItem.code || linkedItem.id}
                </Button>
              ))}
            </Space>
          );
        }
        return formatCellValue(value, column, record);
      },
    };
      }),
    ];

    if (resourceDefinition.supportsHistory) {
      nextColumns.push({
        title: "历史数据",
        key: "history",
        width: 110,
        render: (_, record) => (
          <Button onClick={() => crud.handleShowHistory(record)} size="small" type="link">
            查看历史
          </Button>
        ),
      });
    }

    if (resourceDefinition.useModalForm && !resourceDefinition.readOnly) {
      nextColumns.push({
        title: "操作",
        key: "actions",
        fixed: "right",
        width: resourceDefinition.supportsTestConnection ? 220 : 160,
        render: (_, record) => (
          <Space size={4} wrap>
            {resourceDefinition.supportsTestConnection ? (
              <Button
                disabled={crud.isTestingConnection}
                onClick={() => crud.handleTestConnectionByItem(record)}
                size="small"
                type="link"
              >
                测试连接
              </Button>
            ) : null}
            <Button icon={<EditOutlined />} onClick={() => crud.handleEditRow(record)} size="small" type="link">
              编辑
            </Button>
            <Popconfirm
              cancelText="取消"
              okText="删除"
              okType="danger"
              onConfirm={() => crud.handleDeleteRow(record)}
              title={`确认删除${resourceDefinition.itemLabel}「${record.name || record.code || record.id}」吗？`}
            >
              <Button danger icon={<DeleteOutlined />} size="small" type="link">
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      });
    }

    return nextColumns;
  }, [booleanFieldKeys, crud, resourceDefinition]);

  const secondaryActions =
    !resourceDefinition.readOnly &&
    (crud.checkedIds.size > 0 || resourceDefinition.supportsCopyAsNew) ? (
      <Space wrap>
        {crud.checkedIds.size > 0 ? (
          <Popconfirm
            cancelText="取消"
            okText="删除"
            okType="danger"
            onConfirm={crud.handleBatchDelete}
            title={`确定要批量删除选中的 ${crud.checkedIds.size} 条${resourceDefinition.itemLabel}吗？`}
          >
            <Button danger loading={crud.isBatchDeleting}>
              批量删除
            </Button>
          </Popconfirm>
        ) : null}
        {resourceDefinition.supportsCopyAsNew ? (
          <Button
            disabled={crud.isLoading || crud.isCopying || crud.checkedIds.size === 0}
            icon={<CopyOutlined />}
            loading={crud.isCopying}
            onClick={() => {
              if (crud.checkedIds.size > 1) {
                Modal.confirm({
                  cancelText: "取消",
                  content: `确定要复制选中的 ${crud.checkedIds.size} 条${resourceDefinition.itemLabel}并新增吗？将自动为编码添加 _copy 后缀。`,
                  okText: "复制新增",
                  onOk: () => crud.handleBatchCopyAsNew(),
                  title: "复制新增",
                });
                return;
              }
              crud.handleBatchCopyAsNew();
            }}
          >
            复制新增
          </Button>
        ) : null}
      </Space>
    ) : null;

  const primaryAction = !resourceDefinition.readOnly ? (
    <Button icon={<PlusOutlined />} onClick={crud.handleCreateNew} type="primary">
      新建{resourceDefinition.itemLabel}
    </Button>
  ) : null;

  return (
    <section className="resource-crud-page">
      <div className="resource-crud-body">
        <AntResourceQueryBar
          bulkToolbarExtra={buildBulkToolbarExtra(crud)}
          disabled={crud.isLoading}
          onChange={crud.handleQueryFieldChange}
          primaryAction={primaryAction}
          onReset={crud.handleResetQuery}
          onSearch={crud.handleSearch}
          queryFields={resourceDefinition.queryFields ?? []}
          queryState={crud.queryDraft}
          relatedOptions={crud.relatedOptions}
          secondaryActions={secondaryActions}
        />

        <div className="resource-crud-table-wrap" ref={tableWrapRef}>
          <Table
            className="resource-crud-table"
            columns={columns}
            dataSource={crud.items}
            loading={crud.isLoading}
            locale={{ emptyText: "还没有数据" }}
            pagination={{
              className: "resource-crud-pagination",
              current: crud.page,
              onChange: (nextPage, nextPageSize) => crud.handlePageChange(nextPage, nextPageSize),
              pageSize: crud.pageSize,
              pageSizeOptions: [10, 20, 50],
              showSizeChanger: true,
              showTotal: (value) => (
                <Space className="resource-crud-pagination-summary" size="middle">
                  {crud.checkedIds.size > 0 && !resourceDefinition.readOnly ? (
                    <Typography.Text className="resource-crud-selection-count" type="secondary">
                      已选 {crud.checkedIds.size} 条
                    </Typography.Text>
                  ) : null}
                  <Typography.Text type="secondary">
                    {`共 ${value} 条，当前第 ${crud.page}/${Math.max(1, Math.ceil(value / crud.pageSize))} 页`}
                  </Typography.Text>
                </Space>
              ),
              total: crud.total,
            }}
            rowKey="id"
            rowSelection={
              resourceDefinition.readOnly
                ? undefined
                : {
                    onChange: (keys) => crud.setCheckedRowKeys(keys),
                    selectedRowKeys: crud.checkedRowKeys,
                  }
            }
            scroll={{ x: "max-content", y: tableScrollY }}
            size="middle"
            onRow={(record) => ({
              onClick: () => {
                if (resourceDefinition.readOnly) {
                  crud.handleSelectItem(record);
                }
              },
            })}
          />
        </div>
      </div>

      {crud.useModalForm && crud.modalState ? (
        <AntResourceModalForm
          key={`${crud.modalState.mode}-${crud.modalState.item?.id ?? "new"}-${Boolean(crud.modalState.initialForm)}`}
          initialFormState={crud.modalState.initialForm}
          initialItem={crud.modalState.item}
          isSaving={crud.isSaving}
          isTesting={crud.isTestingConnection}
          onCancel={() => {
            if (!crud.isSaving && !crud.isTestingConnection) {
              crud.setModalState(null);
            }
          }}
          onSubmit={crud.handleModalSubmit}
          onTestConnection={crud.handleTestConnection}
          open={Boolean(crud.modalState)}
          relatedOptions={crud.relatedOptions}
          resourceDefinition={resourceDefinition}
        />
      ) : null}

      {resourceDefinition.readOnly ? (
        <Drawer
          destroyOnClose
          onClose={() => crud.handleSelectItem(null)}
          open={Boolean(crud.selectedItem)}
          title="日志详情"
          width={520}
        >
          <pre className="resource-crud-readonly-detail">
            {crud.selectedItem ? stringifyJson(crud.selectedItem) : "点击表格行查看详情"}
          </pre>
        </Drawer>
      ) : null}

      {crud.historyTarget ? (
        <HistoryDialog
          item={crud.historyTarget}
          onClose={() => crud.setHistoryTarget(null)}
          onUnauthorized={onUnauthorized}
          resourceDefinition={resourceDefinition}
          showToast={(text, options) => notifyFromAntd({ text, variant: options?.variant ?? "info" })}
          token={token}
        />
      ) : null}

      {crud.deviceDetail ? (
        <DeviceDetailDialog device={crud.deviceDetail} onClose={() => crud.setDeviceDetail(null)} />
      ) : null}
    </section>
  );
}

import { formatCellValue } from "../../adminResources.js";

/**
 * 基础台账等资源共用的数据表格与分页（左侧菜单「基础台账」等条目切换后内容区列表）。
 */
export function ResourceTable({
  resourceDefinition,
  items,
  selectedId,
  onSelect,
  checkedIds,
  onToggleCheck,
  onToggleCheckAll,
  onEditRow,
  onDeleteRow,
  onShowHistory,
  onTestRowConnection,
  isTestingConnection,
  onOpenResourceItem,
}) {
  const showCheckbox = !resourceDefinition.readOnly;
  const showActions = Boolean(resourceDefinition.useModalForm);
  const showTestConnectionAction = Boolean(resourceDefinition.supportsTestConnection);
  const showHistoryColumn = Boolean(resourceDefinition.supportsHistory);
  const isDataSourceTable = Boolean(resourceDefinition.fixedSourceType);
  const allChecked = items.length > 0 && items.every((item) => checkedIds.has(item.id));
  const someChecked = items.some((item) => checkedIds.has(item.id));
  const totalColumns =
    resourceDefinition.columns.length +
    (showCheckbox ? 1 : 0) +
    (showHistoryColumn ? 1 : 0) +
    (showActions ? 1 : 0);

  return (
    <div className="table-wrap">
      <table className={`data-table${isDataSourceTable ? " data-table--datasource" : ""}`}>
        <thead>
          <tr>
            {showCheckbox ? (
              <th className="col-checkbox">
                <input
                  aria-label="全选"
                  checked={allChecked}
                  onChange={() => onToggleCheckAll(items)}
                  ref={(el) => {
                    if (el) el.indeterminate = someChecked && !allChecked;
                  }}
                  type="checkbox"
                />
              </th>
            ) : null}
            {resourceDefinition.columns.map((column) => (
              <th className={`col-${column.key}`} key={column.key}>
                {column.label}
              </th>
            ))}
            {showHistoryColumn ? <th className="col-history">历史数据</th> : null}
            {showActions ? <th className="col-actions">操作</th> : null}
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td className="empty-row" colSpan={totalColumns || 1}>
                还没有数据
              </td>
            </tr>
          ) : (
            items.map((item) => (
              <tr className={selectedId === item.id ? "selected" : ""} key={item.id} onClick={() => onSelect(item)}>
                {showCheckbox ? (
                  <td className="col-checkbox" onClick={(e) => e.stopPropagation()}>
                    <input
                      aria-label={`选择 ${item.id}`}
                      checked={checkedIds.has(item.id)}
                      onChange={() => onToggleCheck(item.id)}
                      type="checkbox"
                    />
                  </td>
                ) : null}
                {resourceDefinition.columns.map((column) => (
                  <td className={`col-${column.key}`} key={column.key}>
                    {column.cellFormat === "resourceLinks" && Array.isArray(item[column.key]) ? (
                      <div className="resource-link-list">
                        {item[column.key].length === 0 ? (
                          "-"
                        ) : (
                          item[column.key].map((linkedItem) => (
                            <button
                              className="row-action-button row-action-link"
                              key={`${column.key}-${linkedItem.id}`}
                              onClick={(event) => {
                                event.stopPropagation();
                                onOpenResourceItem?.(column.resource, linkedItem.id);
                              }}
                              type="button"
                            >
                              {linkedItem.name || linkedItem.code || linkedItem.id}
                            </button>
                          ))
                        )}
                      </div>
                    ) : (
                      formatCellValue(item[column.key], column)
                    )}
                  </td>
                ))}
                {showHistoryColumn ? (
                  <td className="col-history" onClick={(e) => e.stopPropagation()}>
                    <button className="row-action-button row-action-link" onClick={() => onShowHistory(item)} type="button">
                      查看历史
                    </button>
                  </td>
                ) : null}
                {showActions ? (
                  <td className="col-actions" onClick={(e) => e.stopPropagation()}>
                    <div className="row-action-group">
                      {showTestConnectionAction ? (
                        <button
                          className="row-action-button row-action-link"
                          disabled={isTestingConnection}
                          onClick={() => onTestRowConnection(item)}
                          type="button"
                        >
                          测试连接
                        </button>
                      ) : null}
                      <button className="row-action-button" onClick={() => onEditRow(item)} type="button">
                        编辑
                      </button>
                      <button className="row-action-button row-action-danger" onClick={() => onDeleteRow(item)} type="button">
                        删除
                      </button>
                    </div>
                  </td>
                ) : null}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export function ResourcePagination({ page, pageSize, total, onPageChange, onPageSizeChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const canPrev = page > 1;
  const canNext = page < totalPages;

  return (
    <div aria-label="分页" className="table-pagination" role="navigation">
      <div className="table-pagination-meta">
        共 {total} 条，当前第 {page}/{totalPages} 页
      </div>
      <div className="table-pagination-actions">
        <label className="table-page-size">
          每页
          <select value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
            {[10, 20, 50].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
          条
        </label>
        <button disabled={!canPrev} onClick={() => onPageChange(page - 1)} type="button">
          上一页
        </button>
        <button disabled={!canNext} onClick={() => onPageChange(page + 1)} type="button">
          下一页
        </button>
      </div>
    </div>
  );
}

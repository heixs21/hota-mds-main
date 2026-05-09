import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { apiRequest } from "../adminApi.js";
import { humanizeAdminApiError, humanizeJsonFieldSyntaxError } from "../adminUserFacingMessages.js";
import {
  createEmptyForm,
  createEmptyQuery,
  createFormFromItem,
  RESERVED_FIELD_KEYS,
  resourceDefinitions,
  stringifyJson,
} from "../adminResources.js";
import { ADMIN_TOAST_MS } from "./adminConstants.js";
import { httpErrorToastVariant } from "./adminUtils.js";
import { ResourceField } from "./ResourceField.jsx";
import { ResourcePagination, ResourceTable } from "./ledger/ResourceTable.jsx";
import { ResourceModalForm } from "./ResourceModalForm.jsx";
import { ResourceQueryBar } from "./ResourceQueryBar.jsx";
import { buildPayloadFromForm } from "./resourcePayload.js";
import { DeviceDetailDialog, HistoryDialog } from "./system/AdminDialogs.jsx";

export function ResourceEditor({ activeResource, token, onUnauthorized }) {
  const resourceDefinition = resourceDefinitions[activeResource];
  const useModalForm = Boolean(resourceDefinition.useModalForm);

  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formState, setFormState] = useState(createEmptyForm(resourceDefinition));
  const [relatedOptions, setRelatedOptions] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isBatchDeleting, setIsBatchDeleting] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [toast, setToast] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [queryDraft, setQueryDraft] = useState(createEmptyQuery(resourceDefinition));
  const [queryApplied, setQueryApplied] = useState(createEmptyQuery(resourceDefinition));
  const [checkedIds, setCheckedIds] = useState(new Set());
  const [modalState, setModalState] = useState(null);
  const [historyTarget, setHistoryTarget] = useState(null);
  const [deviceDetail, setDeviceDetail] = useState(null);
  const toastTimerRef = useRef(null);

  const buildResourceListPath = useCallback(
    (targetPage, targetPageSize, queryState) => {
      const params = new URLSearchParams();
      params.set("page", String(targetPage));
      params.set("pageSize", String(targetPageSize));
      if (queryState) {
        Object.entries(queryState).forEach(([key, value]) => {
          const normalized = typeof value === "string" ? value.trim() : value;
          if (normalized !== "" && normalized !== null && normalized !== undefined) {
            params.set(key, String(normalized));
          }
        });
      }
      if (resourceDefinition.fixedListParams) {
        Object.entries(resourceDefinition.fixedListParams).forEach(([key, value]) => {
          params.set(key, String(value));
        });
      }
      return `${resourceDefinition.endpoint}?${params.toString()}`;
    },
    [resourceDefinition.endpoint, resourceDefinition.fixedListParams],
  );

  const fetchAllItems = useCallback(
    async (endpoint) => {
      const allItems = [];
      let currentPage = 1;
      const fixedPageSize = 200;
      let totalCount = 0;
      do {
        const response = await apiRequest(`${endpoint}?page=${currentPage}&pageSize=${fixedPageSize}`, { token });
        const pageItems = response.data.items ?? [];
        totalCount = response.data.total ?? pageItems.length;
        allItems.push(...pageItems);
        currentPage += 1;
      } while (allItems.length < totalCount);
      return allItems;
    },
    [token],
  );

  const dismissToast = useCallback(() => {
    if (toastTimerRef.current !== null) {
      window.clearTimeout(toastTimerRef.current);
      toastTimerRef.current = null;
    }
    setToast(null);
  }, []);

  const showToast = useCallback((text, { variant = "info" } = {}) => {
    if (toastTimerRef.current !== null) {
      window.clearTimeout(toastTimerRef.current);
      toastTimerRef.current = null;
    }
    const trimmed = typeof text === "string" ? text.trim() : "";
    if (!trimmed) {
      setToast(null);
      return;
    }
    const normalizedVariant =
      variant === "success" || variant === "warning" || variant === "error" || variant === "info" ? variant : "info";
    setToast({ text: trimmed, variant: normalizedVariant });
    toastTimerRef.current = window.setTimeout(() => {
      toastTimerRef.current = null;
      setToast(null);
    }, ADMIN_TOAST_MS);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current !== null) {
        window.clearTimeout(toastTimerRef.current);
      }
    };
  }, []);

  const resourceDependencies = useMemo(() => {
    const nextDependencies = new Set();
    for (const key of resourceDefinition.relatedResources ?? []) {
      nextDependencies.add(key);
    }
    for (const field of resourceDefinition.fields) {
      if (
        field.type === "resourceSelect" ||
        field.type === "resourceMultiSelect" ||
        field.type === "resourceMultiSelectFiltered"
      ) {
        nextDependencies.add(field.resource);
      }
    }
    for (const field of resourceDefinition.queryFields ?? []) {
      if (field.type === "resourceSelect") {
        nextDependencies.add(field.resource);
      }
    }
    return [...nextDependencies];
  }, [resourceDefinition]);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      dismissToast();
      setIsLoading(true);
      setSelectedItem(null);
      setFormState(createEmptyForm(resourceDefinition));
      setPage(1);
      setCheckedIds(new Set());
      setModalState(null);
      setHistoryTarget(null);
      const initialQuery = createEmptyQuery(resourceDefinition);
      setQueryDraft(initialQuery);
      setQueryApplied(initialQuery);

      try {
        const listPromise = apiRequest(buildResourceListPath(1, pageSize, initialQuery), { token });
        const dependencyPromises = resourceDependencies.map((dependencyKey) =>
          fetchAllItems(resourceDefinitions[dependencyKey].endpoint),
        );
        const [listResponse, ...dependencyItemsGroup] = await Promise.all([listPromise, ...dependencyPromises]);

        if (cancelled) {
          return;
        }

        setItems(listResponse.data.items ?? []);
        setTotal(listResponse.data.total ?? 0);
        const nextRelatedOptions = {};
        resourceDependencies.forEach((dependencyKey, index) => {
          nextRelatedOptions[dependencyKey] = dependencyItemsGroup[index] ?? [];
        });
        setRelatedOptions(nextRelatedOptions);
      } catch (error) {
        if (cancelled) {
          return;
        }
        if (error.status === 401) {
          onUnauthorized();
          return;
        }
        showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "列表加载失败，请稍后重试。" }), {
          variant: httpErrorToastVariant(error.status),
        });
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadData();

    return () => {
      cancelled = true;
    };
  }, [resourceDefinition, resourceDependencies, token, onUnauthorized, dismissToast, showToast, buildResourceListPath, fetchAllItems, pageSize]);

  function handleSelectItem(item) {
    setSelectedItem(item);
    if (!resourceDefinition.readOnly && !useModalForm) {
      setFormState(createFormFromItem(resourceDefinition, item));
    }
  }

  function handleCreateNew() {
    setSelectedItem(null);
    setFormState(createEmptyForm(resourceDefinition));
    if (useModalForm) {
      setModalState({ mode: "create", item: null });
    } else {
      showToast(`正在创建新的${resourceDefinition.itemLabel}。`, { variant: "info" });
    }
  }

  async function reloadCurrentResource(nextSelectedId = null, targetPage = page, targetPageSize = pageSize, queryState = queryApplied) {
    const payload = await apiRequest(buildResourceListPath(targetPage, targetPageSize, queryState), { token });
    const nextItems = payload.data.items ?? [];
    setItems(nextItems);
    setTotal(payload.data.total ?? 0);
    setPage(targetPage);
    setPageSize(targetPageSize);
    setCheckedIds(new Set());

    if (nextSelectedId) {
      const nextSelectedItem = nextItems.find((item) => item.id === nextSelectedId) ?? null;
      setSelectedItem(nextSelectedItem);
      if (nextSelectedItem && !resourceDefinition.readOnly && !useModalForm) {
        setFormState(createFormFromItem(resourceDefinition, nextSelectedItem));
      }
    } else {
      setSelectedItem(null);
      if (!resourceDefinition.readOnly && !useModalForm) {
        setFormState(createEmptyForm(resourceDefinition));
      }
    }
  }

  async function handlePageChange(nextPage) {
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const bounded = Math.min(Math.max(nextPage, 1), totalPages);
    if (bounded === page || isLoading) {
      return;
    }
    setIsLoading(true);
    try {
      await reloadCurrentResource(null, bounded, pageSize, queryApplied);
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "分页加载失败，请稍后重试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function handlePageSizeChange(nextPageSize) {
    if (nextPageSize === pageSize || isLoading) {
      return;
    }
    setIsLoading(true);
    try {
      await reloadCurrentResource(null, 1, nextPageSize, queryApplied);
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "分页加载失败，请稍后重试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function persistFormState(values, { editingItem }) {
    setIsSaving(true);
    showToast("正在保存...", { variant: "info" });

    try {
      let payload;
      try {
        payload = buildPayloadFromForm(resourceDefinition, values);
      } catch (formErr) {
        if (formErr && formErr.kind === "json") {
          showToast(humanizeJsonFieldSyntaxError(formErr.field, formErr.error), { variant: "error" });
          return false;
        }
        if (formErr && formErr.kind === "integer") {
          showToast(`「${formErr.field.label}」须填写有效整数。`, { variant: "error" });
          return false;
        }
        throw formErr;
      }

      for (const key of RESERVED_FIELD_KEYS) {
        payload[key] = "";
      }

      const isEdit = Boolean(editingItem?.id);
      const path = isEdit ? `${resourceDefinition.endpoint}/${editingItem.id}` : resourceDefinition.endpoint;
      const method = isEdit ? "PATCH" : "POST";
      const response = await apiRequest(path, { method, token, body: payload });
      await reloadCurrentResource(response.data.id, page, pageSize, queryApplied);
      showToast(isEdit ? "更新成功。" : "创建成功。", { variant: "success" });
      return true;
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return false;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "保存失败，请检查表单后重试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
      return false;
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await persistFormState(formState, { editingItem: selectedItem });
  }

  async function handleModalSubmit(values) {
    const editingItem = modalState?.item ?? null;
    const success = await persistFormState(values, { editingItem });
    if (success) {
      setModalState(null);
    }
  }

  async function handleTestConnection(values) {
    setIsTestingConnection(true);
    try {
      let payload;
      try {
        payload = buildPayloadFromForm(resourceDefinition, values);
      } catch (formErr) {
        if (formErr && formErr.kind === "json") {
          showToast(humanizeJsonFieldSyntaxError(formErr.field, formErr.error), { variant: "error" });
          return;
        }
        if (formErr && formErr.kind === "integer") {
          showToast(`「${formErr.field.label}」须填写有效整数。`, { variant: "error" });
          return;
        }
        throw formErr;
      }

      const response = await apiRequest(`${resourceDefinition.endpoint}/test-connection`, {
        method: "POST",
        token,
        body: payload,
      });
      showToast(response.data?.message || "连接测试成功。", { variant: "success" });
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(error.message || "连接测试失败。", { variant: httpErrorToastVariant(error.status) });
    } finally {
      setIsTestingConnection(false);
    }
  }

  async function handleTestConnectionByItem(item) {
    if (!item) {
      return;
    }
    const values = createFormFromItem(resourceDefinition, item);
    await handleTestConnection(values);
  }

  async function handleDelete() {
    if (!selectedItem?.id) {
      return;
    }

    setIsDeleting(true);
    showToast("正在删除...", { variant: "info" });
    try {
      await apiRequest(`${resourceDefinition.endpoint}/${selectedItem.id}`, {
        method: "DELETE",
        token,
      });
      await reloadCurrentResource(null, page, pageSize, queryApplied);
      showToast("删除成功。", { variant: "success" });
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "删除失败，请稍后再试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleDeleteRow(item) {
    if (!item?.id) return;
    if (!window.confirm(`确认删除${resourceDefinition.itemLabel}「${item.name || item.code || item.id}」吗？`)) {
      return;
    }
    setIsDeleting(true);
    showToast("正在删除...", { variant: "info" });
    try {
      await apiRequest(`${resourceDefinition.endpoint}/${item.id}`, { method: "DELETE", token });
      await reloadCurrentResource(null, page, pageSize, queryApplied);
      showToast("删除成功。", { variant: "success" });
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "删除失败，请稍后再试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsDeleting(false);
    }
  }

  function handleEditRow(item) {
    setSelectedItem(item);
    setModalState({ mode: "edit", item });
  }

  function handleShowHistory(item) {
    setHistoryTarget(item);
  }

  function handleToggleCheck(itemId) {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  }

  function handleToggleCheckAll(currentItems) {
    const allChecked = currentItems.length > 0 && currentItems.every((item) => checkedIds.has(item.id));
    if (allChecked) {
      setCheckedIds(new Set());
    } else {
      setCheckedIds(new Set(currentItems.map((item) => item.id)));
    }
  }

  async function handleBatchDelete() {
    if (checkedIds.size === 0) {
      return;
    }
    const count = checkedIds.size;
    if (!window.confirm(`确定要批量删除选中的 ${count} 条${resourceDefinition.itemLabel}吗？此操作不可撤销。`)) {
      return;
    }

    setIsBatchDeleting(true);
    showToast(`正在批量删除 ${count} 条记录...`, { variant: "info" });
    try {
      await apiRequest(`${resourceDefinition.endpoint}/batch-delete`, {
        method: "POST",
        token,
        body: { ids: [...checkedIds] },
      });
      await reloadCurrentResource(null, 1, pageSize, queryApplied);
      showToast(`成功删除 ${count} 条${resourceDefinition.itemLabel}。`, { variant: "success" });
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "批量删除失败，请稍后再试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsBatchDeleting(false);
    }
  }

  function handleQueryFieldChange(fieldKey, value) {
    setQueryDraft((current) => ({
      ...current,
      [fieldKey]: value,
    }));
  }

  async function handleSearch() {
    setIsLoading(true);
    setQueryApplied(queryDraft);
    try {
      await reloadCurrentResource(null, 1, pageSize, queryDraft);
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "查询失败，请稍后重试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleResetQuery() {
    const emptyQuery = createEmptyQuery(resourceDefinition);
    setQueryDraft(emptyQuery);
    setQueryApplied(emptyQuery);
    setIsLoading(true);
    try {
      await reloadCurrentResource(null, 1, pageSize, emptyQuery);
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "重置查询失败，请稍后重试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleOpenResourceItem(resourceKey, itemId) {
    if (!resourceKey || !itemId) {
      return;
    }
    const definition = resourceDefinitions[resourceKey];
    if (!definition) {
      return;
    }
    try {
      const response = await apiRequest(`${definition.endpoint}/${itemId}`, { token });
      if (resourceKey === "devices") {
        setDeviceDetail(response.data);
      }
    } catch (error) {
      if (error.status === 401) {
        onUnauthorized();
        return;
      }
      showToast(error.message || "详情加载失败，请稍后重试。", { variant: httpErrorToastVariant(error.status) });
    }
  }

  return (
    <section className={`resource-shell${useModalForm ? " resource-shell--single" : ""}`}>
      {toast ? (
        <div aria-live="polite" className={`admin-toast admin-toast--${toast.variant}`} role="status">
          <span className="admin-toast-text">{toast.text}</span>
          <button aria-label="关闭提示" className="admin-toast-close" onClick={dismissToast} type="button">
            ×
          </button>
        </div>
      ) : null}
      <div className="resource-header">
        <div className="resource-header-left">
          <h2>{resourceDefinition.label}</h2>
          {checkedIds.size > 0 && !resourceDefinition.readOnly ? (
            <span className="batch-selection-info">
              已选 {checkedIds.size} 条
              <button
                className="batch-delete-button"
                disabled={isBatchDeleting}
                onClick={handleBatchDelete}
                type="button"
              >
                {isBatchDeleting ? "删除中..." : "批量删除"}
              </button>
            </span>
          ) : null}
        </div>
        {!resourceDefinition.readOnly ? (
          <button onClick={handleCreateNew} type="button">
            新建{resourceDefinition.itemLabel}
          </button>
        ) : null}
      </div>

      <div className={`resource-body${useModalForm ? " resource-body--single" : ""}`}>
        <section className="resource-section">
          <div className="table-panel">
            <ResourceQueryBar
              disabled={isLoading}
              onChange={handleQueryFieldChange}
              onReset={handleResetQuery}
              onSearch={handleSearch}
              queryFields={resourceDefinition.queryFields ?? []}
              queryState={queryDraft}
              relatedOptions={relatedOptions}
            />
            <div className="table-panel-scroll">
              <ResourceTable
                checkedIds={checkedIds}
                isTestingConnection={isTestingConnection}
                items={items}
                onDeleteRow={handleDeleteRow}
                onEditRow={handleEditRow}
                onSelect={handleSelectItem}
                onShowHistory={handleShowHistory}
                onTestRowConnection={handleTestConnectionByItem}
                onToggleCheck={handleToggleCheck}
                onToggleCheckAll={handleToggleCheckAll}
                onOpenResourceItem={handleOpenResourceItem}
                resourceDefinition={resourceDefinition}
                selectedId={selectedItem?.id ?? null}
              />
            </div>
            <ResourcePagination
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              page={page}
              pageSize={pageSize}
              total={total}
            />
          </div>
        </section>

        {!useModalForm ? (
          <section className="resource-section resource-section--editor">
            {resourceDefinition.readOnly ? (
              <div className="resource-panel-scroll">
                <div className="readonly-detail">
                  <h3>日志详情</h3>
                  <pre>{selectedItem ? stringifyJson(selectedItem) : "点击左侧日志查看详情"}</pre>
                </div>
              </div>
            ) : (
              <div className="resource-panel-scroll resource-panel-scroll--has-footer">
                <form className="editor-form" onSubmit={handleSubmit}>
                  <div className="editor-form-scroll">
                    <h3>{selectedItem ? `编辑${resourceDefinition.itemLabel}` : `新建${resourceDefinition.itemLabel}`}</h3>
                    <div className="editor-grid">
                      {resourceDefinition.fields
                        .filter((field) => !field.hideInForm)
                        .map((field) => (
                          <ResourceField
                            field={field}
                            formState={formState}
                            key={field.key}
                            relatedOptions={relatedOptions}
                            setFormState={setFormState}
                          />
                        ))}
                    </div>
                  </div>
                  <div className="actions">
                    <button disabled={isLoading || isSaving} type="submit">
                      {isSaving ? "保存中..." : "保存"}
                    </button>
                    {selectedItem ? (
                      <button className="danger-button" disabled={isDeleting} onClick={handleDelete} type="button">
                        {isDeleting ? "删除中..." : "删除"}
                      </button>
                    ) : null}
                  </div>
                </form>
              </div>
            )}
          </section>
        ) : null}
      </div>

      {modalState && useModalForm ? (
        <ResourceModalForm
          initialItem={modalState.item}
          isSaving={isSaving}
          isTesting={isTestingConnection}
          onCancel={() => {
            if (!isSaving && !isTestingConnection) setModalState(null);
          }}
          onSubmit={handleModalSubmit}
          onTestConnection={handleTestConnection}
          relatedOptions={relatedOptions}
          resourceDefinition={resourceDefinition}
        />
      ) : null}

      {historyTarget ? (
        <HistoryDialog
          item={historyTarget}
          onClose={() => setHistoryTarget(null)}
          onUnauthorized={onUnauthorized}
          resourceDefinition={resourceDefinition}
          showToast={showToast}
          token={token}
        />
      ) : null}
      {deviceDetail ? (
        <DeviceDetailDialog
          device={deviceDetail}
          onClose={() => setDeviceDetail(null)}
        />
      ) : null}
    </section>
  );
}

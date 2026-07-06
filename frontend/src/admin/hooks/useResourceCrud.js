import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { apiRequest } from "../../adminApi.js";
import { humanizeAdminApiError, humanizeJsonFieldSyntaxError } from "../../adminUserFacingMessages.js";
import {
  createEmptyForm,
  createEmptyQuery,
  createCopyFormFromItem,
  createFormFromItem,
  RESERVED_FIELD_KEYS,
  resourceDefinitions,
} from "../../adminResources.js";
import { httpErrorToastVariant } from "../adminUtils.js";
import { buildPayloadFromForm } from "../resourcePayload.js";

function buildListFilterQueryString(queryState, resourceDefinition) {
  const params = new URLSearchParams();
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
  return params.toString();
}

function buildResourceListPath(resourceDefinition, targetPage, targetPageSize, queryState) {
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
}

async function fetchAllItems(endpoint, token) {
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
}

export function useResourceCrud({ notify, onUnauthorized, resourceKey, token }) {
  const resourceDefinition = resourceDefinitions[resourceKey];
  const useModalForm = Boolean(resourceDefinition?.useModalForm);

  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formState, setFormState] = useState(() => createEmptyForm(resourceDefinition));
  const [relatedOptions, setRelatedOptions] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isBatchDeleting, setIsBatchDeleting] = useState(false);
  const [isCopying, setIsCopying] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [queryDraft, setQueryDraft] = useState(() => createEmptyQuery(resourceDefinition));
  const [queryApplied, setQueryApplied] = useState(() => createEmptyQuery(resourceDefinition));
  const [bulkToolbarInput, setBulkToolbarInput] = useState("");
  const [bulkToolbarMulti, setBulkToolbarMulti] = useState({});
  const [isBulkRefreshing, setIsBulkRefreshing] = useState(false);
  const [checkedIds, setCheckedIds] = useState(() => new Set());
  const [modalState, setModalState] = useState(null);
  const [inlinePatchKeys, setInlinePatchKeys] = useState(() => new Set());
  const [historyTarget, setHistoryTarget] = useState(null);
  const [deviceDetail, setDeviceDetail] = useState(null);
  const loadVersionRef = useRef(0);

  const showToast = useCallback(
    (text, { variant = "info" } = {}) => {
      const trimmed = typeof text === "string" ? text.trim() : "";
      if (!trimmed) {
        return;
      }
      notify({ variant, text: trimmed });
    },
    [notify],
  );

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

  const reloadCurrentResource = useCallback(
    async (nextSelectedId = null, targetPage = page, targetPageSize = pageSize, queryState = queryApplied) => {
      const payload = await apiRequest(
        buildResourceListPath(resourceDefinition, targetPage, targetPageSize, queryState),
        { token },
      );
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
      } else if (!resourceDefinition.readOnly && !useModalForm) {
        setSelectedItem(null);
        setFormState(createEmptyForm(resourceDefinition));
      }
    },
    [page, pageSize, queryApplied, resourceDefinition, token, useModalForm],
  );

  useEffect(() => {
    const loadVersion = loadVersionRef.current + 1;
    loadVersionRef.current = loadVersion;
    let cancelled = false;

    async function loadData() {
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
      const btInit = resourceDefinition.bulkApplyToolbar;
      if (btInit?.fields?.length) {
        const initialMulti = {};
        for (const field of btInit.fields) {
          initialMulti[field.key] = field.defaultInput ?? "";
        }
        setBulkToolbarMulti(initialMulti);
        setBulkToolbarInput("");
      } else {
        setBulkToolbarMulti({});
        setBulkToolbarInput(
          btInit?.inputKind === "booleanSelect" ? btInit?.defaultInput ?? "true" : btInit?.defaultInput ?? "",
        );
      }

      try {
        const listPromise = apiRequest(buildResourceListPath(resourceDefinition, 1, pageSize, initialQuery), { token });
        const dependencyPromises = resourceDependencies.map((dependencyKey) =>
          fetchAllItems(resourceDefinitions[dependencyKey].endpoint, token),
        );
        const [listResponse, ...dependencyItemsGroup] = await Promise.all([listPromise, ...dependencyPromises]);

        if (cancelled || loadVersionRef.current !== loadVersion) {
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
        if (cancelled || loadVersionRef.current !== loadVersion) {
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
        if (!cancelled && loadVersionRef.current === loadVersion) {
          setIsLoading(false);
        }
      }
    }

    loadData();

    return () => {
      cancelled = true;
    };
  }, [onUnauthorized, pageSize, resourceDefinition, resourceDependencies, resourceKey, showToast, token]);

  useEffect(() => {
    const bt = resourceDefinition.bulkApplyToolbar;
    if (!bt || items.length === 0) {
      return;
    }
    if (bt.fields?.length) {
      const firstRow = items[0];
      const keys = bt.fields.map((f) => f.key);
      const allSame = keys.every((key) => items.every((item) => item[key] === firstRow[key]));
      if (!allSame) {
        return;
      }
      const nextMulti = {};
      for (const field of bt.fields) {
        const v = firstRow[field.key];
        nextMulti[field.key] = v === undefined || v === null ? field.defaultInput ?? "" : String(v);
      }
      setBulkToolbarMulti(nextMulti);
      return;
    }
    if (bt.inputKind === "booleanSelect" && bt.valueKey) {
      const key = bt.valueKey;
      const first = items[0][key];
      const norm = first === true || first === "true" || first === 1;
      const allSame = items.every((item) => {
        const v = item[key];
        const n = v === true || v === "true" || v === 1;
        return n === norm;
      });
      if (allSame) {
        setBulkToolbarInput(norm ? "true" : "false");
      }
      return;
    }
    if (!bt.valueKey) {
      return;
    }
    const key = bt.valueKey;
    const first = items[0][key];
    if (first === undefined || first === null) {
      return;
    }
    const allSame = items.every((item) => item[key] === first);
    if (allSame) {
      setBulkToolbarInput(String(first));
    }
  }, [items, resourceDefinition.bulkApplyToolbar]);

  const handleUnauthorized = useCallback(
    (error) => {
      if (error?.status === 401) {
        onUnauthorized();
        return true;
      }
      return false;
    },
    [onUnauthorized],
  );

  const handlePageChange = useCallback(
    async (nextPage, nextPageSize) => {
      const effectivePageSize = nextPageSize ?? pageSize;
      const totalPages = Math.max(1, Math.ceil(total / effectivePageSize));
      const bounded = Math.min(Math.max(nextPage, 1), totalPages);
      if ((bounded === page && effectivePageSize === pageSize) || isLoading) {
        return;
      }
      setIsLoading(true);
      try {
        await reloadCurrentResource(null, bounded, effectivePageSize, queryApplied);
      } catch (error) {
        if (handleUnauthorized(error)) {
          return;
        }
        showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "分页加载失败，请稍后重试。" }), {
          variant: httpErrorToastVariant(error.status),
        });
      } finally {
        setIsLoading(false);
      }
    },
    [
      handleUnauthorized,
      isLoading,
      page,
      pageSize,
      queryApplied,
      reloadCurrentResource,
      resourceDefinition.fields,
      showToast,
      total,
    ],
  );

  const persistFormState = useCallback(
    async (values, { editingItem }) => {
      setIsSaving(true);
      showToast("正在保存...", { variant: "info" });

      try {
        let payload;
        try {
          payload = buildPayloadFromForm(resourceDefinition, values);
        } catch (formErr) {
          if (formErr?.kind === "json") {
            showToast(humanizeJsonFieldSyntaxError(formErr.field, formErr.error), { variant: "error" });
            return false;
          }
          if (formErr?.kind === "integer") {
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
        if (handleUnauthorized(error)) {
          return false;
        }
        showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "保存失败，请检查表单后重试。" }), {
          variant: httpErrorToastVariant(error.status),
        });
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [
      handleUnauthorized,
      page,
      pageSize,
      queryApplied,
      reloadCurrentResource,
      resourceDefinition,
      showToast,
      token,
    ],
  );

  const handleCreateNew = useCallback(() => {
    setSelectedItem(null);
    setFormState(createEmptyForm(resourceDefinition));
    if (useModalForm) {
      setModalState({ mode: "create", item: null });
    } else {
      showToast(`正在创建新的${resourceDefinition.itemLabel}。`, { variant: "info" });
    }
  }, [resourceDefinition, showToast, useModalForm]);

  const handleEditRow = useCallback((item) => {
    setSelectedItem(item);
    setModalState({ mode: "edit", item });
  }, []);

  const handleModalSubmit = useCallback(
    async (values) => {
      const editingItem = modalState?.item ?? null;
      const success = await persistFormState(values, { editingItem });
      if (success) {
        setModalState(null);
      }
    },
    [modalState, persistFormState],
  );

  const isInlineBooleanPatching = useCallback(
    (recordId, fieldKey) => inlinePatchKeys.has(`${recordId}:${fieldKey}`),
    [inlinePatchKeys],
  );

  const handleInlineBooleanToggle = useCallback(
    async (record, fieldKey, nextValue) => {
      if (!record?.id || resourceDefinition.readOnly) {
        return;
      }

      const patchKey = `${record.id}:${fieldKey}`;
      const previousValue = record[fieldKey];

      setInlinePatchKeys((current) => new Set(current).add(patchKey));
      setItems((current) =>
        current.map((item) => (item.id === record.id ? { ...item, [fieldKey]: nextValue } : item)),
      );

      try {
        await apiRequest(`${resourceDefinition.endpoint}/${record.id}`, {
          method: "PATCH",
          token,
          body: { [fieldKey]: nextValue },
        });
      } catch (error) {
        setItems((current) =>
          current.map((item) => (item.id === record.id ? { ...item, [fieldKey]: previousValue } : item)),
        );
        if (handleUnauthorized(error)) {
          return;
        }
        showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "更新失败，请稍后重试。" }), {
          variant: httpErrorToastVariant(error.status),
        });
      } finally {
        setInlinePatchKeys((current) => {
          const next = new Set(current);
          next.delete(patchKey);
          return next;
        });
      }
    },
    [handleUnauthorized, resourceDefinition, showToast, token],
  );

  const handleTestConnection = useCallback(
    async (values) => {
      setIsTestingConnection(true);
      try {
        let payload;
        try {
          payload = buildPayloadFromForm(resourceDefinition, values);
        } catch (formErr) {
          if (formErr?.kind === "json") {
            showToast(humanizeJsonFieldSyntaxError(formErr.field, formErr.error), { variant: "error" });
            return;
          }
          if (formErr?.kind === "integer") {
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
        if (handleUnauthorized(error)) {
          return;
        }
        showToast(error.message || "连接测试失败。", { variant: httpErrorToastVariant(error.status) });
      } finally {
        setIsTestingConnection(false);
      }
    },
    [handleUnauthorized, resourceDefinition, showToast, token],
  );

  const handleDeleteRow = useCallback(
    async (item) => {
      if (!item?.id) {
        return;
      }
      setIsDeleting(true);
      showToast("正在删除...", { variant: "info" });
      try {
        await apiRequest(`${resourceDefinition.endpoint}/${item.id}`, { method: "DELETE", token });
        await reloadCurrentResource(null, page, pageSize, queryApplied);
        showToast("删除成功。", { variant: "success" });
      } catch (error) {
        if (handleUnauthorized(error)) {
          return;
        }
        showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "删除失败，请稍后再试。" }), {
          variant: httpErrorToastVariant(error.status),
        });
      } finally {
        setIsDeleting(false);
      }
    },
    [
      handleUnauthorized,
      page,
      pageSize,
      queryApplied,
      reloadCurrentResource,
      resourceDefinition,
      showToast,
      token,
    ],
  );

  const buildExistingCodeSet = useCallback(
    (extraItems = items) => new Set(extraItems.map((row) => String(row.code ?? "").trim()).filter(Boolean)),
    [items],
  );

  const handleCopyRow = useCallback(
    (item) => {
      if (!item) {
        return;
      }
      const existingCodes = buildExistingCodeSet();
      const copyForm = createCopyFormFromItem(resourceDefinition, item, { existingCodes });
      setSelectedItem(null);
      setModalState({ mode: "create", item: null, initialForm: copyForm });
    },
    [buildExistingCodeSet, resourceDefinition],
  );

  const handleBatchCopyAsNew = useCallback(async () => {
    if (checkedIds.size === 0 || !resourceDefinition.supportsCopyAsNew) {
      return;
    }
    const selected = items.filter((item) => checkedIds.has(item.id));
    if (selected.length === 0) {
      return;
    }
    if (selected.length === 1) {
      handleCopyRow(selected[0]);
      return;
    }

    setIsCopying(true);
    showToast(`正在复制新增 ${selected.length} 条记录...`, { variant: "info" });
    const existingCodes = buildExistingCodeSet();
    let successCount = 0;
    try {
      for (let i = 0; i < selected.length; i += 1) {
        const item = selected[i];
        const copyForm = createCopyFormFromItem(resourceDefinition, item, {
          copyIndex: i,
          existingCodes,
        });
        let payload;
        try {
          payload = buildPayloadFromForm(resourceDefinition, copyForm);
        } catch (formErr) {
          if (formErr?.kind === "json") {
            showToast(humanizeJsonFieldSyntaxError(formErr.field, formErr.error), { variant: "error" });
            return;
          }
          if (formErr?.kind === "integer") {
            showToast(`「${formErr.field.label}」须填写有效整数。`, { variant: "error" });
            return;
          }
          throw formErr;
        }
        for (const key of RESERVED_FIELD_KEYS) {
          payload[key] = "";
        }
        await apiRequest(resourceDefinition.endpoint, { method: "POST", token, body: payload });
        successCount += 1;
      }
      await reloadCurrentResource(null, page, pageSize, queryApplied);
      showToast(`已成功复制新增 ${successCount} 条${resourceDefinition.itemLabel}。`, { variant: "success" });
    } catch (error) {
      if (handleUnauthorized(error)) {
        return;
      }
      const partial = successCount > 0 ? `（已成功 ${successCount} 条）` : "";
      showToast(
        humanizeAdminApiError(error, resourceDefinition.fields, {
          fallback: `复制新增失败${partial}，请检查编码是否重复后重试。`,
        }),
        { variant: httpErrorToastVariant(error.status) },
      );
      if (successCount > 0) {
        await reloadCurrentResource(null, page, pageSize, queryApplied);
      }
    } finally {
      setIsCopying(false);
    }
  }, [
    buildExistingCodeSet,
    checkedIds,
    handleCopyRow,
    handleUnauthorized,
    items,
    page,
    pageSize,
    queryApplied,
    reloadCurrentResource,
    resourceDefinition,
    showToast,
    token,
  ]);

  const handleBatchDelete = useCallback(async () => {
    if (checkedIds.size === 0) {
      return;
    }
    const count = checkedIds.size;
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
      if (handleUnauthorized(error)) {
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "批量删除失败，请稍后再试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsBatchDeleting(false);
    }
  }, [
    checkedIds,
    handleUnauthorized,
    pageSize,
    queryApplied,
    reloadCurrentResource,
    resourceDefinition,
    showToast,
    token,
  ]);

  const handleSearch = useCallback(async () => {
    setIsLoading(true);
    setQueryApplied(queryDraft);
    try {
      await reloadCurrentResource(null, 1, pageSize, queryDraft);
    } catch (error) {
      if (handleUnauthorized(error)) {
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "查询失败，请稍后重试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsLoading(false);
    }
  }, [
    handleUnauthorized,
    pageSize,
    queryDraft,
    reloadCurrentResource,
    resourceDefinition.fields,
    showToast,
  ]);

  const handleResetQuery = useCallback(async () => {
    const emptyQuery = createEmptyQuery(resourceDefinition);
    setQueryDraft(emptyQuery);
    setQueryApplied(emptyQuery);
    setIsLoading(true);
    try {
      await reloadCurrentResource(null, 1, pageSize, emptyQuery);
    } catch (error) {
      if (handleUnauthorized(error)) {
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: "重置查询失败，请稍后重试。" }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsLoading(false);
    }
  }, [handleUnauthorized, pageSize, reloadCurrentResource, resourceDefinition, showToast]);

  const handleBulkToolbarApply = useCallback(async () => {
    const bt = resourceDefinition.bulkApplyToolbar;
    if (!bt || checkedIds.size === 0) {
      return;
    }

    const qs = buildListFilterQueryString(queryApplied, resourceDefinition);
    const path = `${resourceDefinition.endpoint}/${bt.apiPath}${qs ? `?${qs}` : ""}`;

    let body;
    let singleFieldPayload = null;

    if (bt.fields?.length) {
      body = { ids: [...checkedIds] };
      for (const field of bt.fields) {
        const raw = bulkToolbarMulti[field.key] ?? "";
        const trimmed = String(raw).trim();
        if (field.kind === "decimal") {
          const n = Number.parseFloat(trimmed);
          if (Number.isNaN(n) || n < field.min || n > field.max) {
            showToast(`${field.label}须为 ${field.min}～${field.max} 之间的数值。`, { variant: "error" });
            return;
          }
          body[field.key] = n;
        } else {
          const n = Number.parseInt(trimmed, 10);
          if (Number.isNaN(n) || n < field.min || n > field.max) {
            showToast(`${field.label}须为 ${field.min}～${field.max} 之间的整数。`, { variant: "error" });
            return;
          }
          body[field.key] = n;
        }
      }
    } else if (bt.inputKind === "booleanSelect") {
      const raw = String(bulkToolbarInput).trim();
      let boolVal;
      if (raw === "true") {
        boolVal = true;
      } else if (raw === "false") {
        boolVal = false;
      } else {
        showToast("请选择启用状态。", { variant: "error" });
        return;
      }
      body = { ids: [...checkedIds], [bt.valueKey]: boolVal };
      singleFieldPayload = boolVal;
    } else {
      const parsed = Number.parseInt(String(bulkToolbarInput).trim(), 10);
      if (Number.isNaN(parsed) || parsed < bt.min || parsed > bt.max) {
        showToast(`${bt.label}须为 ${bt.min}～${bt.max} 之间的整数。`, { variant: "error" });
        return;
      }
      body = { ids: [...checkedIds], [bt.valueKey]: parsed };
      singleFieldPayload = parsed;
    }

    setIsBulkRefreshing(true);
    try {
      const response = await apiRequest(path, {
        method: "POST",
        token,
        body,
      });
      const updatedCount = response.data?.updatedCount ?? 0;
      await reloadCurrentResource(null, page, pageSize, queryApplied);
      if (bt.fields?.length) {
        showToast(bt.successMessage(updatedCount), { variant: "success" });
      } else {
        showToast(bt.successMessage(updatedCount, singleFieldPayload), { variant: "success" });
      }
    } catch (error) {
      if (handleUnauthorized(error)) {
        return;
      }
      showToast(humanizeAdminApiError(error, resourceDefinition.fields, { fallback: bt.errorFallback }), {
        variant: httpErrorToastVariant(error.status),
      });
    } finally {
      setIsBulkRefreshing(false);
    }
  }, [
    bulkToolbarInput,
    bulkToolbarMulti,
    checkedIds,
    handleUnauthorized,
    page,
    pageSize,
    queryApplied,
    reloadCurrentResource,
    resourceDefinition,
    showToast,
    token,
  ]);

  const handleOpenResourceItem = useCallback(
    async (resourceTypeKey, itemId) => {
      if (!resourceTypeKey || !itemId) {
        return;
      }
      const definition = resourceDefinitions[resourceTypeKey];
      if (!definition) {
        return;
      }
      try {
        const response = await apiRequest(`${definition.endpoint}/${itemId}`, { token });
        if (resourceTypeKey === "devices") {
          setDeviceDetail(response.data);
        }
      } catch (error) {
        if (handleUnauthorized(error)) {
          return;
        }
        showToast(error.message || "详情加载失败，请稍后重试。", { variant: httpErrorToastVariant(error.status) });
      }
    },
    [handleUnauthorized, showToast, token],
  );

  const handleSelectItem = useCallback(
    (item) => {
      if (!item) {
        setSelectedItem(null);
        return;
      }
      setSelectedItem(item);
      if (!resourceDefinition.readOnly && !useModalForm) {
        setFormState(createFormFromItem(resourceDefinition, item));
      }
    },
    [resourceDefinition, useModalForm],
  );

  const setCheckedRowKeys = useCallback((keys) => {
    setCheckedIds(new Set(keys));
  }, []);

  return {
    resourceDefinition,
    useModalForm,
    items,
    selectedItem,
    relatedOptions,
    isLoading,
    isSaving,
    isDeleting,
    isBatchDeleting,
    isCopying,
    isTestingConnection,
    isBulkRefreshing,
    page,
    pageSize,
    total,
    queryDraft,
    checkedIds,
    checkedRowKeys: [...checkedIds],
    modalState,
    historyTarget,
    deviceDetail,
    bulkToolbarInput,
    bulkToolbarMulti,
    setQueryDraft,
    setBulkToolbarInput,
    setBulkToolbarMulti,
    setModalState,
    setHistoryTarget,
    setDeviceDetail,
    handleCreateNew,
    handleEditRow,
    handleDeleteRow,
    handleCopyRow,
    handleBatchCopyAsNew,
    handleBatchDelete,
    handleSearch,
    handleResetQuery,
    handleBulkToolbarApply,
    handlePageChange,
    handleModalSubmit,
    handleInlineBooleanToggle,
    isInlineBooleanPatching,
    handleTestConnection,
    handleTestConnectionByItem: (item) => {
      if (!item) {
        return;
      }
      handleTestConnection(createFormFromItem(resourceDefinition, item));
    },
    handleShowHistory: setHistoryTarget,
    handleOpenResourceItem,
    handleSelectItem,
    setCheckedRowKeys,
    handleQueryFieldChange: (fieldKey, value) => {
      setQueryDraft((current) => ({
        ...current,
        [fieldKey]: value,
      }));
    },
  };
}

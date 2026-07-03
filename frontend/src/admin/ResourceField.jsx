import { useEffect, useState } from "react";

import { ADMIN_TOKEN_STORAGE_KEY, apiRequest } from "../adminApi.js";
import { fieldVisibleForForm } from "../adminResources.js";
import { ScreenPageTransferField } from "./screen/ScreenPageTransferField.jsx";

function matchesVisibleWhen(field, formState) {
  return fieldVisibleForForm(field, formState);
}

export function ResourceField({ field, formState, setFormState, relatedOptions }) {
  const value = formState[field.key];

  if (!matchesVisibleWhen(field, formState)) {
    return null;
  }

  if (field.type === "staticHint") {
    return (
      <div className="field field--static-hint">
        {field.label ? <span className="field-label-static">{field.label}</span> : null}
        <p className="field-hint field-hint--admin">{field.text ?? ""}</p>
      </div>
    );
  }

  function updateValue(nextValue) {
    setFormState((current) => ({
      ...current,
      [field.key]: nextValue,
    }));
  }

  if (field.type === "screenPageTransfer") {
    return <ScreenPageTransferField field={field} formState={formState} setFormState={setFormState} relatedOptions={relatedOptions} />;
  }

  if (field.type === "checkbox") {
    return (
      <label className="checkbox-field">
        <input checked={Boolean(value)} onChange={(event) => updateValue(event.target.checked)} type="checkbox" />
        <span>{field.label}</span>
      </label>
    );
  }

  if (field.type === "textarea" || field.type === "json") {
    return (
      <label className="field">
        <span>{field.label}</span>
        <textarea
          onChange={(event) => updateValue(event.target.value)}
          placeholder={field.placeholder ?? ""}
          rows={field.type === "json" ? 6 : 4}
          value={value ?? ""}
        />
      </label>
    );
  }

  if (field.type === "select") {
    return (
      <label className="field">
        <span>{field.label}</span>
        <select onChange={(event) => updateValue(event.target.value)} value={value ?? ""}>
          {field.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field.type === "resourceSelect") {
    const options = relatedOptions[field.resource] ?? [];
    return (
      <label className="field">
        <span>{field.label}</span>
        <select onChange={(event) => updateValue(event.target.value)} value={value ?? ""}>
          <option value="">{field.allowBlank ? "不设置" : "请选择"}</option>
          {options.map((option) => (
            <option key={option.id} value={option.id}>
              {option.code ? `${option.code} - ${option.name}` : option.name}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field.type === "energyDatabaseEquipmentMulti") {
    return <EnergyDatabaseEquipmentMultiField field={field} formState={formState} setFormState={setFormState} />;
  }

  if (field.type === "resourceMultiSelectFiltered") {
    const rawOptions = relatedOptions[field.resource] ?? [];
    const filterKey = field.filterOptionKey ?? "sourceType";
    const ft = String(formState[field.filterByField] ?? "").trim();
    const options = ft ? rawOptions.filter((opt) => String(opt[filterKey] ?? "") === ft) : [];
    const selectedSet = new Set(Array.isArray(value) ? value.map((item) => String(item)) : []);

    function toggleOption(optionId, checked) {
      const next = new Set(selectedSet);
      const key = String(optionId);
      if (checked) {
        next.add(key);
      } else {
        next.delete(key);
      }
      updateValue(
        [...next]
          .map((id) => Number(id))
          .filter((id) => Number.isInteger(id) && id > 0),
      );
    }

    const emptyHint = ft ? "该类型下暂无数据源，请先在「数据源配置」中新建。" : "请先在上方的「数据源类型」中选择 OPC UA、数据库等。";

    return (
      <div className="field field--multi-select">
        <span>{field.label}</span>
        <p className="field-hint resource-multi-select-hint">仅列出与所选类型一致的数据源；可多选。</p>
        <div className="resource-multi-select-scroll" role="group" aria-label={field.label}>
          {!ft ? (
            <div className="resource-multi-select-empty">{emptyHint}</div>
          ) : options.length === 0 ? (
            <div className="resource-multi-select-empty">{emptyHint}</div>
          ) : (
            options.map((option) => {
              const idStr = String(option.id);
              const labelText = option.code ? `${option.code} - ${option.name}` : option.name;
              return (
                <label className="resource-multi-select-row" key={option.id}>
                  <input
                    checked={selectedSet.has(idStr)}
                    onChange={(event) => toggleOption(option.id, event.target.checked)}
                    type="checkbox"
                  />
                  <span>{labelText}</span>
                </label>
              );
            })
          )}
        </div>
      </div>
    );
  }

  if (field.type === "resourceMultiSelect") {
    const options = relatedOptions[field.resource] ?? [];
    const selectedSet = new Set(Array.isArray(value) ? value.map((item) => String(item)) : []);

    function toggleOption(optionId, checked) {
      const next = new Set(selectedSet);
      const key = String(optionId);
      if (checked) {
        next.add(key);
      } else {
        next.delete(key);
      }
      updateValue([...next]);
    }

    return (
      <div className="field field--multi-select">
        <span>{field.label}</span>
        <p className="field-hint resource-multi-select-hint">可多选；列表过长时可滚动。</p>
        <div className="resource-multi-select-scroll" role="group" aria-label={field.label}>
          {options.length === 0 ? (
            <div className="resource-multi-select-empty">暂无可选设备（请先维护设备台账）</div>
          ) : (
            options.map((option) => {
              const idStr = String(option.id);
              const labelText = option.code ? `${option.code} - ${option.name}` : option.name;
              return (
                <label className="resource-multi-select-row" key={option.id}>
                  <input
                    checked={selectedSet.has(idStr)}
                    onChange={(event) => toggleOption(option.id, event.target.checked)}
                    type="checkbox"
                  />
                  <span>{labelText}</span>
                </label>
              );
            })
          )}
        </div>
      </div>
    );
  }

  return (
    <label className="field">
      <span>{field.label}</span>
      <input
        onChange={(event) => updateValue(event.target.value)}
        placeholder={field.placeholder ?? ""}
        type={field.key === "password" ? "password" : "text"}
        value={value ?? ""}
      />
    </label>
  );
}

function EnergyDatabaseEquipmentMultiField({ field, formState, setFormState }) {
  const value = formState[field.key];
  const dsField = field.dataSourceField ?? "dataSourceIds";
  const dsRaw = formState[dsField];
  const bindingType = String(formState.bindingSourceType ?? "");
  const firstDs =
    Array.isArray(dsRaw) && dsRaw.length > 0 ? dsRaw.map((x) => Number(x)).find((n) => Number.isInteger(n) && n > 0) : null;

  const [options, setOptions] = useState([]);
  const [loadErr, setLoadErr] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (bindingType !== "database" || !firstDs) {
      setOptions([]);
      return;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);
      setLoadErr("");
      try {
        const token =
          window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ??
          window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ??
          "";
        const res = await apiRequest(`/api/admin/energy-equipment-options?data_source_id=${firstDs}`, { token });
        const opts = res?.data?.options ?? [];
        if (!cancelled) {
          setOptions(Array.isArray(opts) ? opts : []);
        }
      } catch (e) {
        if (!cancelled) {
          setLoadErr(e.message || String(e));
          setOptions([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [bindingType, firstDs]);

  const selectedSet = new Set(Array.isArray(value) ? value.map(String) : []);

  function toggleOption(optionId, checked) {
    const next = new Set(selectedSet);
    const key = String(optionId);
    if (checked) {
      next.add(key);
    } else {
      next.delete(key);
    }
    setFormState((current) => ({
      ...current,
      [field.key]: [...next],
    }));
  }

  if (bindingType !== "database") {
    return (
      <div className="field field--static-hint">
        <span className="field-label-static">{field.label}</span>
        <p className="field-hint field-hint--admin">请先将「数据源类型」设为数据库，再勾选 platform_equipment 表计。</p>
      </div>
    );
  }

  if (!firstDs) {
    return (
      <div className="field field--static-hint">
        <span className="field-label-static">{field.label}</span>
        <p className="field-hint field-hint--admin">请先在上方选择至少一个能耗数据库数据源。</p>
      </div>
    );
  }

  return (
    <div className="field field--multi-select">
      <span>{field.label}</span>
      <p className="field-hint resource-multi-select-hint">
        选项来自本地库 EnergyEquipmentCatalog（定时任务 sync_energy_dashboard_snapshots 从能耗库同步）；可多选。
      </p>
      {loadErr ? <p className="field-hint resource-multi-select-hint">{loadErr}</p> : null}
      {loading ? <p className="field-hint resource-multi-select-hint">加载设备列表…</p> : null}
      <div className="resource-multi-select-scroll" role="group" aria-label={field.label}>
        {loading ? (
          <div className="resource-multi-select-empty">加载中…</div>
        ) : options.length === 0 ? (
          <div className="resource-multi-select-empty">
            暂无同步数据。请先运行后端定时任务 sync_energy_dashboard_snapshots（或等待下一轮同步）。
          </div>
        ) : (
          options.map((option) => (
            <label className="resource-multi-select-row" key={option.id}>
              <input
                checked={selectedSet.has(String(option.id))}
                onChange={(event) => toggleOption(option.id, event.target.checked)}
                type="checkbox"
              />
              <span>{option.label}</span>
            </label>
          ))
        )}
      </div>
    </div>
  );
}

import { Alert, Checkbox, Form, Input, InputNumber, Select, Spin, Typography } from "antd";
import { useEffect, useState } from "react";

import { ADMIN_TOKEN_STORAGE_KEY, apiRequest } from "../adminApi.js";
import { fieldVisibleForForm } from "../adminResources.js";
import { ScreenPageTransferField } from "./screen/ScreenPageTransferField.jsx";

function matchesVisibleWhen(field, formState) {
  return fieldVisibleForForm(field, formState);
}

function MultiSelectOptions({ emptyText, field, onChange, options, value }) {
  const selectedSet = new Set(Array.isArray(value) ? value.map(String) : []);

  return (
    <div className="resource-field-multi-select">
      {options.length === 0 ? (
        <Typography.Text type="secondary">{emptyText}</Typography.Text>
      ) : (
        <Checkbox.Group
          onChange={(checkedValues) => onChange(checkedValues)}
          value={[...selectedSet]}
        >
          {options.map((option) => {
            const idStr = String(option.id);
            const labelText = option.code ? `${option.code} - ${option.name}` : option.name;
            return (
              <div className="resource-field-multi-select-row" key={option.id}>
                <Checkbox value={idStr}>{labelText}</Checkbox>
              </div>
            );
          })}
        </Checkbox.Group>
      )}
    </div>
  );
}

export function ResourceField({ field, formState, setFormState, relatedOptions }) {
  const value = formState[field.key];

  if (!matchesVisibleWhen(field, formState)) {
    return null;
  }

  function updateValue(nextValue) {
    setFormState((current) => ({
      ...current,
      [field.key]: nextValue,
    }));
  }

  if (field.type === "staticHint") {
    return (
      <Form.Item label={field.label || undefined}>
        <Typography.Paragraph style={{ marginBottom: 0 }} type="secondary">
          {field.text ?? ""}
        </Typography.Paragraph>
      </Form.Item>
    );
  }

  if (field.type === "screenPageTransfer") {
    return <ScreenPageTransferField field={field} formState={formState} setFormState={setFormState} relatedOptions={relatedOptions} />;
  }

  if (field.type === "checkbox") {
    return (
      <Form.Item valuePropName="checked">
        <Checkbox checked={Boolean(value)} onChange={(event) => updateValue(event.target.checked)}>
          {field.label}
        </Checkbox>
      </Form.Item>
    );
  }

  if (field.type === "textarea" || field.type === "json") {
    return (
      <Form.Item label={field.label}>
        <Input.TextArea
          onChange={(event) => updateValue(event.target.value)}
          placeholder={field.placeholder ?? ""}
          rows={field.type === "json" ? 6 : 4}
          value={value ?? ""}
        />
      </Form.Item>
    );
  }

  if (field.type === "select") {
    return (
      <Form.Item label={field.label}>
        <Select
          onChange={(nextValue) => updateValue(nextValue ?? "")}
          options={field.options ?? []}
          value={value ?? ""}
        />
      </Form.Item>
    );
  }

  if (field.type === "resourceSelect") {
    const options = relatedOptions[field.resource] ?? [];
    return (
      <Form.Item label={field.label}>
        <Select
          allowClear={field.allowBlank}
          onChange={(nextValue) => updateValue(nextValue ?? "")}
          options={[
            ...(field.allowBlank ? [{ value: "", label: "不设置" }] : [{ value: "", label: "请选择", disabled: true }]),
            ...options.map((option) => ({
              value: String(option.id),
              label: option.code ? `${option.code} - ${option.name}` : option.name,
            })),
          ]}
          showSearch
          value={value ?? ""}
        />
      </Form.Item>
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
    const emptyHint = ft
      ? "该类型下暂无数据源，请先在「数据源配置」中新建。"
      : "请先在上方的「数据源类型」中选择 OPC UA、数据库等。";

    return (
      <Form.Item
        extra="仅列出与所选类型一致的数据源；可多选。"
        label={field.label}
      >
        <MultiSelectOptions
          emptyText={emptyHint}
          field={field}
          onChange={(checkedValues) =>
            updateValue(
              checkedValues
                .map((id) => Number(id))
                .filter((id) => Number.isInteger(id) && id > 0),
            )
          }
          options={options}
          value={value}
        />
      </Form.Item>
    );
  }

  if (field.type === "resourceMultiSelect") {
    const options = relatedOptions[field.resource] ?? [];

    return (
      <Form.Item extra="可多选；列表过长时可滚动。" label={field.label}>
        <MultiSelectOptions
          emptyText="暂无可选设备（请先维护设备台账）"
          field={field}
          onChange={(checkedValues) => updateValue([...checkedValues])}
          options={options}
          value={value}
        />
      </Form.Item>
    );
  }

  if (field.type === "integer") {
    return (
      <Form.Item label={field.label}>
        <InputNumber
          onChange={(nextValue) => updateValue(nextValue == null ? "" : String(nextValue))}
          placeholder={field.placeholder ?? ""}
          style={{ width: "100%" }}
          value={value === "" || value == null ? null : Number(value)}
        />
      </Form.Item>
    );
  }

  if (field.key === "password") {
    return (
      <Form.Item label={field.label}>
        <Input.Password
          onChange={(event) => updateValue(event.target.value)}
          placeholder={field.placeholder ?? ""}
          value={value ?? ""}
        />
      </Form.Item>
    );
  }

  return (
    <Form.Item label={field.label}>
      <Input
        onChange={(event) => updateValue(event.target.value)}
        placeholder={field.placeholder ?? ""}
        value={value ?? ""}
      />
    </Form.Item>
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
      } catch (error) {
        if (!cancelled) {
          setLoadErr(error.message || String(error));
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

  function toggleValues(checkedValues) {
    setFormState((current) => ({
      ...current,
      [field.key]: [...checkedValues],
    }));
  }

  if (bindingType !== "database") {
    return (
      <Form.Item label={field.label}>
        <Alert showIcon type="info" message="请先将「数据源类型」设为数据库，再勾选 platform_equipment 表计。" />
      </Form.Item>
    );
  }

  if (!firstDs) {
    return (
      <Form.Item label={field.label}>
        <Alert showIcon type="info" message="请先在上方选择至少一个能耗数据库数据源。" />
      </Form.Item>
    );
  }

  return (
    <Form.Item
      extra="选项来自本地库 EnergyEquipmentCatalog（定时任务 sync_energy_dashboard_snapshots 从能耗库同步）；可多选。"
      label={field.label}
    >
      {loadErr ? <Alert showIcon style={{ marginBottom: 12 }} type="error" message={loadErr} /> : null}
      <Spin spinning={loading}>
        <div className="resource-field-multi-select">
          {!loading && options.length === 0 ? (
            <Typography.Text type="secondary">
              暂无同步数据。请先运行后端定时任务 sync_energy_dashboard_snapshots（或等待下一轮同步）。
            </Typography.Text>
          ) : (
            <Checkbox.Group onChange={toggleValues} value={[...selectedSet]}>
              {options.map((option) => (
                <div className="resource-field-multi-select-row" key={option.id}>
                  <Checkbox value={String(option.id)}>{option.label}</Checkbox>
                </div>
              ))}
            </Checkbox.Group>
          )}
        </div>
      </Spin>
    </Form.Item>
  );
}

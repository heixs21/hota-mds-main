import { Alert, Checkbox, Collapse, Form, Input, InputNumber, Select, Spin, Switch, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";

import { ADMIN_TOKEN_STORAGE_KEY, apiRequest } from "../adminApi.js";
import { fieldVisibleForForm } from "../adminResources.js";
import { buildSelectPlaceholder } from "./adminUtils.js";
import { ScreenPageTransferField } from "./screen/ScreenPageTransferField.jsx";

function matchesVisibleWhen(field, formState) {
  return fieldVisibleForForm(field, formState);
}

function toResourceSelectOptions(options) {
  return options.map((option) => ({
    value: String(option.id),
    label: option.code ? `${option.code} - ${option.name}` : option.name,
  }));
}

function ResourceMultiSelectField({ emptyHint, extra, label, onChange, options, value }) {
  const selectOptions = useMemo(() => toResourceSelectOptions(options), [options]);
  const selectedValues = Array.isArray(value) ? value.map(String) : [];

  return (
    <Form.Item extra={extra} label={label}>
      <Select
        allowClear
        maxTagCount="responsive"
        mode="multiple"
        onChange={(nextValues) => onChange(nextValues ?? [])}
        optionFilterProp="label"
        options={selectOptions}
        placeholder={options.length === 0 ? emptyHint : label ? `请选择${label}` : "请选择"}
        showSearch
        style={{ width: "100%" }}
        value={selectedValues}
      />
    </Form.Item>
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

  if (field.type === "switch") {
    return (
      <Form.Item label={field.label} valuePropName="checked">
        <Switch checked={Boolean(value)} onChange={updateValue} />
      </Form.Item>
    );
  }

  if (field.type === "textarea" || field.type === "json") {
    const rows = field.type === "json" ? 6 : 4;
    const textArea = (
      <Input.TextArea
        onChange={(event) => updateValue(event.target.value)}
        placeholder={field.placeholder ?? ""}
        rows={rows}
        value={value ?? ""}
      />
    );

    if (field.collapseByDefault) {
      return (
        <Collapse
          bordered={false}
          className="resource-field-collapse"
          items={[
            {
              key: field.key,
              label: field.label,
              children: (
                <>
                  {field.collapseHint ? (
                    <Typography.Paragraph style={{ marginBottom: 8 }} type="secondary">
                      {field.collapseHint}
                    </Typography.Paragraph>
                  ) : null}
                  <Form.Item extra={field.extra} style={{ marginBottom: 0 }}>
                    {textArea}
                  </Form.Item>
                </>
              ),
            },
          ]}
        />
      );
    }

    return (
      <Form.Item extra={field.extra} label={field.label}>
        {textArea}
      </Form.Item>
    );
  }

  if (field.type === "select") {
    return (
      <Form.Item label={field.label}>
        <Select
          allowClear={Boolean(field.allowBlank)}
          onChange={(nextValue) => updateValue(nextValue ?? "")}
          options={field.options ?? []}
          placeholder={buildSelectPlaceholder(field)}
          value={value === "" || value == null ? undefined : value}
        />
      </Form.Item>
    );
  }

  if (field.type === "resourceSelect") {
    const options = relatedOptions[field.resource] ?? [];
    const selectedValue = value == null || value === "" ? undefined : String(value);
    return (
      <Form.Item label={field.label}>
        <Select
          allowClear={field.allowBlank}
          onChange={(nextValue) => updateValue(nextValue ?? "")}
          optionFilterProp="label"
          options={toResourceSelectOptions(options)}
          placeholder={buildSelectPlaceholder(field)}
          showSearch
          value={selectedValue}
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
      <ResourceMultiSelectField
        emptyHint={emptyHint}
        extra="仅列出与所选类型一致的数据源；可多选。"
        label={field.label}
        onChange={(nextValues) =>
          updateValue(
            nextValues
              .map((id) => Number(id))
              .filter((id) => Number.isInteger(id) && id > 0),
          )
        }
        options={options}
        value={value}
      />
    );
  }

  if (field.type === "resourceMultiSelect") {
    const options = relatedOptions[field.resource] ?? [];

    return (
      <ResourceMultiSelectField
        emptyHint="暂无可选设备（请先维护设备台账）"
        extra="可多选。"
        label={field.label}
        onChange={(nextValues) => updateValue([...nextValues])}
        options={options}
        value={value}
      />
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

  if (field.type === "decimal") {
    return (
      <Form.Item label={field.label}>
        <InputNumber
          onChange={(nextValue) => updateValue(nextValue == null ? "" : String(nextValue))}
          placeholder={field.placeholder ?? ""}
          step={0.01}
          stringMode
          style={{ width: "100%" }}
          value={value === "" || value == null ? null : value}
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

  const selectOptions = useMemo(
    () =>
      options.map((option) => ({
        value: String(option.id),
        label: option.label,
      })),
    [options],
  );

  if (bindingType !== "database") {
    return (
      <Form.Item label={field.label}>
        <Alert showIcon type="info" message="请先将「数据源类型」设为数据库，再选择 platform_equipment 表计。" />
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
        <Select
          allowClear
          disabled={loading}
          maxTagCount="responsive"
          mode="multiple"
          notFoundContent={
            loading ? null : "暂无同步数据。请先运行后端定时任务 sync_energy_dashboard_snapshots（或等待下一轮同步）。"
          }
          onChange={(nextValues) =>
            setFormState((current) => ({
              ...current,
              [field.key]: [...(nextValues ?? [])],
            }))
          }
          optionFilterProp="label"
          options={selectOptions}
          placeholder="请选择表计"
          showSearch
          style={{ width: "100%" }}
          value={Array.isArray(value) ? value.map(String) : []}
        />
      </Spin>
    </Form.Item>
  );
}

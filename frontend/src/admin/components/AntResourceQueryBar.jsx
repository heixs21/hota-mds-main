import { Button, DatePicker, Form, Input, Select, Space } from "antd";
import dayjs from "dayjs";

export function AntResourceQueryBar({
  bulkToolbarExtra,
  disabled,
  onChange,
  onReset,
  onSearch,
  queryFields,
  queryState,
  relatedOptions,
  trailingActions,
}) {
  if (!queryFields?.length && !bulkToolbarExtra && !trailingActions) {
    return null;
  }

  function renderQueryField(field) {
    const value = queryState[field.key] ?? "";

    if (field.type === "date") {
      return (
        <Form.Item key={field.key} label={field.label}>
          <DatePicker
            allowClear
            disabled={disabled}
            format="YYYY-MM-DD"
            onChange={(date) => onChange(field.key, date ? date.format("YYYY-MM-DD") : "")}
            style={{ width: 180 }}
            value={value ? dayjs(value) : null}
          />
        </Form.Item>
      );
    }

    if (field.type === "select") {
      return (
        <Form.Item key={field.key} label={field.label}>
          <Select
            allowClear
            disabled={disabled}
            onChange={(nextValue) => onChange(field.key, nextValue ?? "")}
            options={[{ value: "", label: "全部" }, ...(field.options ?? [])]}
            style={{ minWidth: 140 }}
            value={value || undefined}
          />
        </Form.Item>
      );
    }

    if (field.type === "resourceSelect") {
      const options = relatedOptions[field.resource] ?? [];
      return (
        <Form.Item key={field.key} label={field.label}>
          <Select
            allowClear
            disabled={disabled}
            onChange={(nextValue) => onChange(field.key, nextValue ?? "")}
            options={[
              { value: "", label: "全部" },
              ...options.map((option) => ({
                value: String(option.id),
                label: option.code ? `${option.code} - ${option.name}` : option.name,
              })),
            ]}
            showSearch
            style={{ minWidth: 180 }}
            value={value || undefined}
          />
        </Form.Item>
      );
    }

    return (
      <Form.Item key={field.key} label={field.label}>
        <Input
          disabled={disabled}
          onChange={(event) => onChange(field.key, event.target.value)}
          onPressEnter={onSearch}
          placeholder={field.placeholder ?? ""}
          style={{ width: 180 }}
          value={value}
        />
      </Form.Item>
    );
  }

  return (
    <div className="resource-crud-query">
      <Form layout="inline" colon={false}>
        {(queryFields ?? []).map(renderQueryField)}
        {bulkToolbarExtra}
        <Form.Item>
          <Space wrap>
            {queryFields?.length ? (
              <>
                <Button disabled={disabled} onClick={onSearch} type="primary">
                  查询
                </Button>
                <Button disabled={disabled} onClick={onReset}>
                  重置
                </Button>
              </>
            ) : null}
            {trailingActions}
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
}

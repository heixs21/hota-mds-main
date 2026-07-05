import { useState } from "react";
import { Button, Form, Modal, Space } from "antd";
import { createEmptyForm, createFormFromItem, fieldVisibleForForm } from "../../adminResources.js";
import { ResourceField } from "../ResourceField.jsx";

function chunkFieldKeys(keys, columns) {
  const rows = [];
  for (let index = 0; index < keys.length; index += columns) {
    rows.push(keys.slice(index, index + columns));
  }
  return rows;
}

function renderResourceField(field, { formState, relatedOptions, setFormState }) {
  return (
    <ResourceField
      field={field}
      formState={formState}
      key={field.key}
      relatedOptions={relatedOptions}
      setFormState={setFormState}
    />
  );
}

function renderModalFormFields(resourceDefinition, formState, relatedOptions, setFormState) {
  const visibleFields = resourceDefinition.fields.filter((field) => !field.hideInForm);
  const fieldByKey = new Map(visibleFields.map((field) => [field.key, field]));
  const sections = resourceDefinition.modalFormSections;
  const sharedProps = { formState, relatedOptions, setFormState };

  if (!sections?.length) {
    return visibleFields.map((field) => renderResourceField(field, sharedProps));
  }

  const sectionedKeys = new Set(sections.flatMap((section) => section.fieldKeys ?? []));
  const output = [];

  for (const section of sections) {
    const columns = section.columns ?? 2;
    const rows = chunkFieldKeys(section.fieldKeys ?? [], columns);

    for (const rowKeys of rows) {
      const rowFields = rowKeys
        .map((key) => fieldByKey.get(key))
        .filter((field) => field && fieldVisibleForForm(field, formState));

      if (rowFields.length === 0) {
        continue;
      }

      output.push(
        <div className="resource-modal-form-row" key={`section-row-${rowKeys.join("-")}`}>
          {rowFields.map((field) => (
            <div className="resource-modal-form-col" key={field.key}>
              {renderResourceField(field, sharedProps)}
            </div>
          ))}
        </div>,
      );
    }
  }

  for (const field of visibleFields) {
    if (!sectionedKeys.has(field.key)) {
      output.push(renderResourceField(field, sharedProps));
    }
  }

  return output;
}

function resolveModalWidth(resourceDefinition) {
  if (typeof resourceDefinition.modalWidth === "number") {
    return resourceDefinition.modalWidth;
  }
  return resourceDefinition.wideModal ? 840 : 720;
}

export function AntResourceModalForm({
  initialFormState,
  initialItem,
  isSaving,
  isTesting,
  onCancel,
  onSubmit,
  onTestConnection,
  open,
  relatedOptions,
  resourceDefinition,
}) {
  const [formState, setFormState] = useState(() => {
    if (initialFormState) {
      return initialFormState;
    }
    return initialItem ? createFormFromItem(resourceDefinition, initialItem) : createEmptyForm(resourceDefinition);
  });

  const isEdit = Boolean(initialItem?.id);
  const isCopy = Boolean(initialFormState && !isEdit);
  const supportsTest = Boolean(resourceDefinition.supportsTestConnection);

  function handleSubmit() {
    onSubmit(formState);
  }

  return (
    <Modal
      destroyOnClose
      footer={
        <Space>
          <Button disabled={isSaving || isTesting} onClick={onCancel}>
            取消
          </Button>
          {supportsTest ? (
            <Button disabled={isSaving || isTesting} loading={isTesting} onClick={() => onTestConnection(formState)}>
              测试连接
            </Button>
          ) : null}
          <Button disabled={isSaving || isTesting} loading={isSaving} onClick={handleSubmit} type="primary">
            {isSaving ? "保存中..." : "保存"}
          </Button>
        </Space>
      }
      onCancel={() => {
        if (!isSaving && !isTesting) {
          onCancel();
        }
      }}
      open={open}
      title={
        isEdit
          ? `编辑${resourceDefinition.itemLabel}`
          : isCopy
            ? `复制新增${resourceDefinition.itemLabel}`
            : `新建${resourceDefinition.itemLabel}`
      }
      width={resolveModalWidth(resourceDefinition)}
      styles={{
        body: { overflowX: "hidden" },
      }}
      style={{ maxWidth: "calc(100vw - 48px)" }}
    >      <Form className="resource-modal-form" layout="vertical" requiredMark={false}>
        {renderModalFormFields(resourceDefinition, formState, relatedOptions, setFormState)}
      </Form>
    </Modal>
  );
}

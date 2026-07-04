import { useState } from "react";
import { Button, Form, Modal, Space } from "antd";

import { createEmptyForm, createFormFromItem } from "../../adminResources.js";
import { ResourceField } from "../ResourceField.jsx";

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
      width={resourceDefinition.wideModal ? 960 : 720}
    >
      <Form className="resource-modal-form" layout="vertical" requiredMark={false}>
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
      </Form>
    </Modal>
  );
}

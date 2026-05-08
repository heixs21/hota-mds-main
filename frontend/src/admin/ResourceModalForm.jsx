import { useState } from "react";

import { createEmptyForm, createFormFromItem } from "../adminResources.js";
import { ResourceField } from "./ResourceField.jsx";

export function ResourceModalForm({
  resourceDefinition,
  initialItem,
  relatedOptions,
  onCancel,
  onSubmit,
  onTestConnection,
  isSaving,
  isTesting,
}) {
  const [formState, setFormState] = useState(() =>
    initialItem ? createFormFromItem(resourceDefinition, initialItem) : createEmptyForm(resourceDefinition),
  );

  const isEdit = Boolean(initialItem?.id);
  const supportsTest = Boolean(resourceDefinition.supportsTestConnection);

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit(formState);
  }

  function handleTest() {
    onTestConnection(formState);
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget && !isSaving && !isTesting) {
      onCancel();
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={handleBackdropClick}>
      <div
        className={`modal-dialog${resourceDefinition.wideModal ? " modal-dialog--wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={`${isEdit ? "编辑" : "新建"}${resourceDefinition.itemLabel}`}
      >
        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="modal-header">
            <h3>{isEdit ? `编辑${resourceDefinition.itemLabel}` : `新建${resourceDefinition.itemLabel}`}</h3>
            <button aria-label="关闭" className="modal-close" disabled={isSaving || isTesting} onClick={onCancel} type="button">
              ×
            </button>
          </div>

          <div className="modal-body">
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

          <div className="modal-footer">
            <button className="ghost-button" disabled={isSaving || isTesting} onClick={onCancel} type="button">
              取消
            </button>
            <button disabled={isSaving || isTesting} type="submit">
              {isSaving ? "保存中..." : "保存"}
            </button>
            {supportsTest ? (
              <button className="secondary-button" disabled={isSaving || isTesting} onClick={handleTest} type="button">
                {isTesting ? "测试中..." : "测试连接"}
              </button>
            ) : null}
          </div>
        </form>
      </div>
    </div>
  );
}

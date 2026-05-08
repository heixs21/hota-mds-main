import { ScreenPageTransferField } from "./screen/ScreenPageTransferField.jsx";

export function ResourceField({ field, formState, setFormState, relatedOptions }) {
  const value = formState[field.key];

  function updateValue(nextValue) {
    setFormState((current) => ({
      ...current,
      [field.key]: nextValue,
    }));
  }

  if (field.type === "screenPageTransfer") {
    return <ScreenPageTransferField field={field} formState={formState} setFormState={setFormState} />;
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

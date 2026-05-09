export function ResourceQueryBar({ queryFields, queryState, relatedOptions, onChange, onSearch, onReset, disabled, queryActionsPrefix }) {
  if (!queryFields || !queryFields.length) {
    return null;
  }

  function handleKeyDown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      onSearch();
    }
  }

  function renderQueryField(field) {
    const value = queryState[field.key] ?? "";
    const updateValue = (nextValue) => onChange(field.key, nextValue);

    if (field.type === "select") {
      return (
        <label className="query-field" key={field.key}>
          <span>{field.label}</span>
          <select disabled={disabled} onChange={(event) => updateValue(event.target.value)} value={value}>
            <option value="">全部</option>
            {(field.options ?? []).map((option) => (
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
        <label className="query-field" key={field.key}>
          <span>{field.label}</span>
          <select disabled={disabled} onChange={(event) => updateValue(event.target.value)} value={value}>
            <option value="">全部</option>
            {options.map((option) => (
              <option key={option.id} value={option.id}>
                {option.code ? `${option.code} - ${option.name}` : option.name}
              </option>
            ))}
          </select>
        </label>
      );
    }

    return (
      <label className="query-field" key={field.key}>
        <span>{field.label}</span>
        <input
          disabled={disabled}
          onChange={(event) => updateValue(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={field.placeholder ?? ""}
          type={field.type === "date" ? "date" : "text"}
          value={value}
        />
      </label>
    );
  }

  return (
    <div className="resource-query-bar">
      <div className="resource-query-grid">{queryFields.map(renderQueryField)}</div>
      <div className="resource-query-actions">
        {queryActionsPrefix}
        <button disabled={disabled} onClick={onSearch} type="button">
          查询
        </button>
        <button className="ghost-button" disabled={disabled} onClick={onReset} type="button">
          重置
        </button>
      </div>
    </div>
  );
}

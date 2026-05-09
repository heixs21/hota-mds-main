import { useEffect, useState } from "react";

import { ALL_PAGE_KEY_OPTIONS, SCREEN_PAGE_KEY_OPTIONS, stringifyJson } from "../../adminResources.js";
import { parseScreenPageTargetKeys } from "./screenPageTransfer.js";

/**
 * 「大屏配置」模块专用：屏幕轮播子页面穿梭框。
 * 若 relatedOptions.screenPageBindings 已加载，则只展示该屏已配置的子页面作为备选；
 * 否则回落到静态 SCREEN_PAGE_KEY_OPTIONS。
 */
export function ScreenPageTransferField({ field, formState, setFormState, relatedOptions }) {
  const screenKeyField = field.screenKeyField ?? "screenKey";
  const screenKey = formState[screenKeyField] || "left";

  // 优先从绑定数据动态计算该屏的可用页面
  const bindings = relatedOptions?.screenPageBindings;
  let options, validKeys;
  if (Array.isArray(bindings) && bindings.length > 0) {
    const forScreen = bindings.filter((b) => b.screenKey === screenKey);
    options = Object.fromEntries(
      forScreen.map((b) => [b.pageKey, b.pageKeyLabel || ALL_PAGE_KEY_OPTIONS[b.pageKey] || b.pageKey]),
    );
    validKeys = forScreen.map((b) => b.pageKey);
  } else {
    options = SCREEN_PAGE_KEY_OPTIONS[screenKey] || {};
    validKeys = Object.keys(options);
  }

  const targetKeys = parseScreenPageTargetKeys(formState[field.key], validKeys, screenKey);
  const sourceKeys = validKeys.filter((k) => !targetKeys.includes(k));

  const [pickedSource, setPickedSource] = useState(() => new Set());
  const [pickedTarget, setPickedTarget] = useState(() => new Set());

  useEffect(() => {
    const normalized = parseScreenPageTargetKeys(formState[field.key], validKeys, screenKey);
    let currentParsed = [];
    try {
      const p = JSON.parse(formState[field.key] || "[]");
      currentParsed = Array.isArray(p) ? p.filter((x) => typeof x === "string") : [];
    } catch {
      currentParsed = [];
    }
    if (JSON.stringify(normalized) !== JSON.stringify(currentParsed)) {
      setFormState((current) => ({
        ...current,
        [field.key]: stringifyJson(normalized),
      }));
    }
  }, [screenKey, validKeys.join(","), field.key, formState[field.key], setFormState]);

  useEffect(() => {
    setPickedSource(new Set());
    setPickedTarget(new Set());
  }, [screenKey]);

  function commitTargetKeys(nextKeys) {
    setFormState((current) => ({
      ...current,
      [field.key]: stringifyJson(nextKeys),
    }));
    setPickedSource(new Set());
    setPickedTarget(new Set());
  }

  function moveToTarget() {
    if (pickedSource.size === 0) {
      return;
    }
    const toAdd = validKeys.filter((k) => pickedSource.has(k));
    commitTargetKeys([...targetKeys, ...toAdd]);
  }

  function moveToSource() {
    if (pickedTarget.size === 0) {
      return;
    }
    const remove = new Set([...pickedTarget]);
    const next = targetKeys.filter((k) => !remove.has(k));
    const defaults = screenKey === "right" ? ["schedule"] : ["overview"];
    commitTargetKeys(next.length > 0 ? next : defaults);
  }

  function toggleSource(key) {
    setPickedSource((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  function toggleTarget(key) {
    setPickedTarget((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  const allSourcePicked = sourceKeys.length > 0 && sourceKeys.every((k) => pickedSource.has(k));
  const allTargetPicked = targetKeys.length > 0 && targetKeys.every((k) => pickedTarget.has(k));

  function toggleAllSource(checked) {
    if (checked) {
      setPickedSource(new Set(sourceKeys));
    } else {
      setPickedSource(new Set());
    }
  }

  function toggleAllTarget(checked) {
    if (checked) {
      setPickedTarget(new Set(targetKeys));
    } else {
      setPickedTarget(new Set());
    }
  }

  return (
    <div className="field field--screen-transfer">
      <span>{field.label}</span>
      <p className="field-hint screen-transfer-hint">右侧顺序即为大屏轮播子页面的先后顺序；选项随「屏幕」左/右切换。</p>
      <div className="admin-transfer" role="group" aria-label={field.label}>
        <div className="admin-transfer-panel">
          <div className="admin-transfer-panel-head">
            <label className="admin-transfer-select-all">
              <input
                checked={allSourcePicked}
                disabled={sourceKeys.length === 0}
                onChange={(event) => toggleAllSource(event.target.checked)}
                type="checkbox"
              />
              <span className="admin-transfer-count">{sourceKeys.length} 项</span>
              <span className="admin-transfer-title">备选项</span>
            </label>
          </div>
          <div className="admin-transfer-body">
            {sourceKeys.length === 0 ? (
              <div className="admin-transfer-empty">暂无备选项</div>
            ) : (
              <ul className="admin-transfer-list">
                {sourceKeys.map((key) => (
                  <li key={key}>
                    <label className="admin-transfer-row">
                      <input checked={pickedSource.has(key)} onChange={() => toggleSource(key)} type="checkbox" />
                      <span>{options[key] ?? key}</span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="admin-transfer-actions">
          <button
            className="admin-transfer-btn"
            disabled={pickedSource.size === 0}
            onClick={moveToTarget}
            title="加入已选"
            type="button"
          >
            ›
          </button>
          <button
            className="admin-transfer-btn"
            disabled={pickedTarget.size === 0}
            onClick={moveToSource}
            title="移回备选"
            type="button"
          >
            ‹
          </button>
        </div>

        <div className="admin-transfer-panel">
          <div className="admin-transfer-panel-head">
            <label className="admin-transfer-select-all">
              <input
                checked={allTargetPicked}
                disabled={targetKeys.length === 0}
                onChange={(event) => toggleAllTarget(event.target.checked)}
                type="checkbox"
              />
              <span className="admin-transfer-count">{targetKeys.length} 项</span>
              <span className="admin-transfer-title">已选项</span>
            </label>
          </div>
          <div className="admin-transfer-body">
            {targetKeys.length === 0 ? (
              <div className="admin-transfer-empty">请从左侧添加</div>
            ) : (
              <ol className="admin-transfer-list admin-transfer-list--ordered">
                {targetKeys.map((key) => (
                  <li key={key}>
                    <label className="admin-transfer-row">
                      <input checked={pickedTarget.has(key)} onChange={() => toggleTarget(key)} type="checkbox" />
                      <span>{options[key] ?? key}</span>
                    </label>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

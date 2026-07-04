import { Form, Transfer, Typography } from "antd";
import { useEffect } from "react";

import { ALL_PAGE_KEY_OPTIONS, SCREEN_PAGE_KEY_OPTIONS, stringifyJson } from "../../adminResources.js";
import { filterBindingsForScreenArea, parseScreenPageTargetKeys } from "./screenPageTransfer.js";

/**
 * 「大屏配置」模块专用：屏幕轮播子页面穿梭框。
 * 备选项来自「屏幕子页面」绑定：须匹配当前表单的区域 + 左/右屏（与后端 pageBindings 解析一致）。
 * 若该区域尚无绑定，回落到静态 SCREEN_PAGE_KEY_OPTIONS。
 */
export function ScreenPageTransferField({ field, formState, setFormState, relatedOptions }) {
  const screenKeyField = field.screenKeyField ?? "screenKey";
  const areaIdField = field.areaIdField ?? "areaId";
  const screenKey = formState[screenKeyField] || "left";
  const areaId = formState[areaIdField];

  const bindings = relatedOptions?.screenPageBindings;
  const forScreenAndArea = filterBindingsForScreenArea(bindings, screenKey, areaId);

  let options;
  let validKeys;
  if (forScreenAndArea.length > 0) {
    options = Object.fromEntries(
      forScreenAndArea.map((b) => [b.pageKey, b.pageKeyLabel || ALL_PAGE_KEY_OPTIONS[b.pageKey] || b.pageKey]),
    );
    validKeys = forScreenAndArea.map((b) => b.pageKey);
  } else if (!areaId) {
    options = SCREEN_PAGE_KEY_OPTIONS[screenKey] || {};
    validKeys = Object.keys(options);
  } else {
    options = {};
    validKeys = [];
  }

  const targetKeys = parseScreenPageTargetKeys(formState[field.key], validKeys, screenKey);
  const dataSource = validKeys.map((key) => ({
    key,
    title: options[key] ?? key,
  }));

  useEffect(() => {
    const normalized = parseScreenPageTargetKeys(formState[field.key], validKeys, screenKey);
    let currentParsed = [];
    try {
      const parsed = JSON.parse(formState[field.key] || "[]");
      currentParsed = Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string") : [];
    } catch {
      currentParsed = [];
    }
    if (JSON.stringify(normalized) !== JSON.stringify(currentParsed)) {
      setFormState((current) => ({
        ...current,
        [field.key]: stringifyJson(normalized),
      }));
    }
  }, [screenKey, areaId, validKeys.join(","), field.key, formState[field.key], setFormState]);

  function commitTargetKeys(nextKeys) {
    setFormState((current) => ({
      ...current,
      [field.key]: stringifyJson(nextKeys),
    }));
  }

  function handleChange(nextTargetKeys) {
    const defaults = screenKey === "right" ? ["schedule"] : ["overview"];
    const filtered = nextTargetKeys.filter((key) => validKeys.includes(key));
    commitTargetKeys(filtered.length > 0 ? filtered : defaults);
  }

  const emptyDescription = areaId
    ? "当前区域暂无子页面绑定，请先在「屏幕子页面」中创建"
    : "请先选择区域";

  return (
    <Form.Item
      className="screen-page-transfer"
      extra={
        <Typography.Text type="secondary">
          右侧为轮播顺序。备选项仅来自「屏幕子页面」中同一区域的绑定；01 与 05 需分别新建，互不影响。
        </Typography.Text>
      }
      label={field.label}
    >
      <Transfer
        dataSource={dataSource}
        disabled={validKeys.length === 0}
        listStyle={{ flex: 1, height: 240, minWidth: 0 }}
        locale={{
          itemUnit: "项",
          itemsUnit: "项",
          notFoundContent: emptyDescription,
          searchPlaceholder: "搜索子页面",
        }}
        onChange={handleChange}
        oneWay={false}
        render={(item) => item.title}
        showSearch
        targetKeys={targetKeys}
        titles={["备选项", "已选项（轮播顺序）"]}
      />
    </Form.Item>
  );
}

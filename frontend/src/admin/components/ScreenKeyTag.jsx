import { Tag } from "antd";

import { SCREEN_KEY_TAG_MAP } from "../../adminResources.js";

export function ScreenKeyTag({ value }) {
  const config = SCREEN_KEY_TAG_MAP[value];
  if (!config) {
    return value ? String(value) : "-";
  }
  return <Tag color={config.color}>{config.label}</Tag>;
}

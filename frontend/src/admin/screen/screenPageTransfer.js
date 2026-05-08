/**
 * 侧栏分组「大屏配置」相关：轮播子页面键解析。
 */
export function parseScreenPageTargetKeys(rawJson, validKeys, screenKey) {
  let parsed = [];
  try {
    const p = JSON.parse(rawJson || "[]");
    parsed = Array.isArray(p) ? p.filter((k) => typeof k === "string") : [];
  } catch {
    parsed = [];
  }
  const filtered = parsed.filter((k) => validKeys.includes(k));
  if (filtered.length > 0) {
    return filtered;
  }
  return screenKey === "right" ? ["schedule"] : ["overview"];
}

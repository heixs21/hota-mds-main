/**
 * 侧栏分组「大屏配置」相关：轮播子页面键解析。
 */

/** 大屏配置穿梭框：仅展示当前区域的绑定（不含其他区域、不含全局兜底）。 */
export function filterBindingsForScreenArea(bindings, screenKey, areaId) {
  if (!Array.isArray(bindings)) {
    return [];
  }
  const normalizedAreaId =
    areaId === "" || areaId === null || areaId === undefined ? null : Number(areaId);

  return bindings.filter((binding) => {
    if (binding.screenKey !== screenKey) {
      return false;
    }
    const bindingAreaId = binding.areaId ?? null;
    if (normalizedAreaId == null) {
      return bindingAreaId == null;
    }
    return bindingAreaId === normalizedAreaId;
  });
}

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

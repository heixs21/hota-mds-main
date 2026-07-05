export const REALTIME_GRID_GAP_PX = 14;
export const REALTIME_MIN_COL_WIDTH_PX = 280;
export const REALTIME_MAX_COLS_WIDE = 4;
export const REALTIME_WIDE_BREAKPOINT_PX = 1600;

/** 与 industrial-realtime-grid 列宽策略一致：宽屏最多 4 列，其余按 280px 估算。 */
export function countRealtimeGridColumns(containerWidth) {
  const width = Number(containerWidth) || 0;
  if (width >= REALTIME_WIDE_BREAKPOINT_PX) {
    return REALTIME_MAX_COLS_WIDE;
  }
  return Math.max(
    1,
    Math.floor((width + REALTIME_GRID_GAP_PX) / (REALTIME_MIN_COL_WIDTH_PX + REALTIME_GRID_GAP_PX)),
  );
}

export function buildDeviceCardsSignature(cards) {
  if (!Array.isArray(cards) || cards.length === 0) {
    return "";
  }
  return cards.map((card) => card.sourceCode).join("\0");
}

export function resolveDeviceRealtimePageCount(cardCount, columns) {
  const safeColumns = Math.max(1, Number(columns) || 1);
  const safeCount = Math.max(0, Number(cardCount) || 0);
  if (safeCount === 0) {
    return 0;
  }
  return Math.ceil(safeCount / safeColumns);
}

/** 子页面轮播总时长均分到各 card 分页。 */
export function resolveDeviceRealtimePageIntervalSeconds(rotationIntervalSeconds, pageCount) {
  const safePages = Number(pageCount) || 0;
  const safeRotation = Number(rotationIntervalSeconds) || 0;
  if (safePages <= 1 || safeRotation <= 0) {
    return 0;
  }
  return safeRotation / safePages;
}

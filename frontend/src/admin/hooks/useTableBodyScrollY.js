import { useEffect, useState } from "react";

const DEFAULT_SCROLL_Y = 320;
const MIN_SCROLL_Y = 160;
/** 分页区默认占位（含 margin），测量不到 DOM 时使用 */
const PAGINATION_BLOCK_FALLBACK = 80;
/** 表格边框、横向滚动条等额外留白 */
const TABLE_LAYOUT_BUFFER = 24;

function measurePaginationBlock(paginationEl) {
  if (!paginationEl) {
    return PAGINATION_BLOCK_FALLBACK;
  }
  const style = window.getComputedStyle(paginationEl);
  return (
    paginationEl.offsetHeight +
    (parseFloat(style.marginTop) || 0) +
    (parseFloat(style.marginBottom) || 0)
  );
}

function measureTableHeaderHeight(wrap) {
  const header = wrap.querySelector(".ant-table-header");
  if (header) {
    return header.offsetHeight;
  }
  const thead = wrap.querySelector(".ant-table-thead");
  return thead?.offsetHeight ?? 0;
}

function measureScrollY(wrap) {
  const pagination = wrap.querySelector(".ant-table-pagination");
  const headerHeight = measureTableHeaderHeight(wrap);
  const paginationBlock = measurePaginationBlock(pagination);
  const next = Math.floor(wrap.clientHeight - headerHeight - paginationBlock - TABLE_LAYOUT_BUFFER);
  return Math.max(MIN_SCROLL_Y, next);
}

/**
 * Measure the table wrapper and return a scroll.y that leaves room for thead + pagination.
 */
export function useTableBodyScrollY(containerRef, deps = []) {
  const [scrollY, setScrollY] = useState(DEFAULT_SCROLL_Y);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return undefined;
    }

    function measure() {
      const wrap = containerRef.current;
      if (!wrap) {
        return;
      }
      setScrollY(measureScrollY(wrap));
    }

    function scheduleMeasure() {
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(measure);
      });
    }

    scheduleMeasure();

    const resizeObserver = new ResizeObserver(scheduleMeasure);
    resizeObserver.observe(container);

    const pagination = container.querySelector(".ant-table-pagination");
    if (pagination) {
      resizeObserver.observe(pagination);
    }

    const mutationObserver = new MutationObserver(scheduleMeasure);
    mutationObserver.observe(container, { childList: true, subtree: true, attributes: true });

    window.addEventListener("resize", scheduleMeasure);

    return () => {
      resizeObserver.disconnect();
      mutationObserver.disconnect();
      window.removeEventListener("resize", scheduleMeasure);
    };
  }, [containerRef, ...deps]);

  return scrollY;
}

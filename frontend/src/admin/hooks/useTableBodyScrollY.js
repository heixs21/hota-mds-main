import { useEffect, useState } from "react";

const DEFAULT_SCROLL_Y = 320;
const MIN_SCROLL_Y = 160;
const PAGINATION_HEIGHT_FALLBACK = 56;

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

      const thead = wrap.querySelector(".ant-table-thead");
      const pagination = wrap.querySelector(".ant-table-pagination");
      const headerHeight = thead?.getBoundingClientRect().height ?? 0;
      const paginationHeight =
        pagination?.getBoundingClientRect().height ?? PAGINATION_HEIGHT_FALLBACK;
      const next = Math.floor(wrap.clientHeight - headerHeight - paginationHeight - 12);
      setScrollY(Math.max(MIN_SCROLL_Y, next));
    }

    measure();
    const rafId = window.requestAnimationFrame(measure);

    const resizeObserver = new ResizeObserver(measure);
    resizeObserver.observe(container);

    const mutationObserver = new MutationObserver(measure);
    mutationObserver.observe(container, { childList: true, subtree: true });

    return () => {
      window.cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      mutationObserver.disconnect();
    };
  }, [containerRef, ...deps]);

  return scrollY;
}

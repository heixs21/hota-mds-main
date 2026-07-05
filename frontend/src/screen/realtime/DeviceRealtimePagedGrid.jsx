import { useEffect, useMemo, useRef, useState } from "react";

import { useScreenCarouselPageActive } from "../../screenCarouselContext.jsx";
import { RealtimeDeviceCard } from "./RealtimeCards.jsx";
import {
  buildDeviceCardsSignature,
  countRealtimeGridColumns,
  resolveDeviceRealtimePageCount,
  resolveDeviceRealtimePageIntervalSeconds,
} from "./deviceRealtimeLayout.js";

function useRealtimeGridColumns(containerRef) {
  const [columns, setColumns] = useState(1);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return undefined;
    }

    function updateColumns() {
      setColumns(countRealtimeGridColumns(element.clientWidth));
    }

    updateColumns();

    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", updateColumns);
      return () => window.removeEventListener("resize", updateColumns);
    }

    const observer = new ResizeObserver(updateColumns);
    observer.observe(element);
    return () => observer.disconnect();
  }, [containerRef]);

  return columns;
}

function SectionEmpty({ description, title = "当前模块暂无数据" }) {
  return (
    <div className="section-empty">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}

export function DeviceRealtimePagedGrid({
  cards,
  rotationIntervalSeconds,
  alarmPulseDismissed,
  setAlarmPulseDismissed,
  formatDateTime,
}) {
  const bodyRef = useRef(null);
  const columns = useRealtimeGridColumns(bodyRef);
  const carouselPageActive = useScreenCarouselPageActive();
  const [activePageIndex, setActivePageIndex] = useState(0);
  const [rotationEpoch, setRotationEpoch] = useState(0);

  const safeCards = Array.isArray(cards) ? cards : [];
  const cardsSignature = useMemo(() => buildDeviceCardsSignature(safeCards), [safeCards]);
  const pageCount = resolveDeviceRealtimePageCount(safeCards.length, columns);
  const pageIntervalSeconds = resolveDeviceRealtimePageIntervalSeconds(rotationIntervalSeconds, pageCount);

  const visibleCards = useMemo(() => {
    if (pageCount === 0) {
      return [];
    }
    const start = activePageIndex * columns;
    return safeCards.slice(start, start + columns);
  }, [activePageIndex, columns, pageCount, safeCards]);

  useEffect(() => {
    setActivePageIndex(0);
  }, [cardsSignature, columns]);

  useEffect(() => {
    setActivePageIndex((current) => (current >= pageCount ? 0 : current));
  }, [pageCount]);

  useEffect(() => {
    if (!carouselPageActive || pageCount <= 1 || pageIntervalSeconds <= 0) {
      return undefined;
    }

    const timerId = window.setInterval(() => {
      setActivePageIndex((current) => (current + 1) % pageCount);
    }, pageIntervalSeconds * 1000);

    return () => window.clearInterval(timerId);
  }, [carouselPageActive, pageCount, pageIntervalSeconds, cardsSignature, rotationEpoch]);

  function goToPage(index) {
    if (index === activePageIndex) {
      return;
    }
    setActivePageIndex(index);
    setRotationEpoch((current) => current + 1);
  }

  return (
    <section className="screen-panel panel-span-12 panel-unbounded industrial-realtime-panel industrial-realtime-panel--paged">
      <div className="industrial-realtime-paged-body" ref={bodyRef}>
        {pageCount === 0 ? (
          <SectionEmpty
            title="当前暂无可监控 OPC UA 设备"
            description="请在数据源配置中绑定设备并配置节点列表（含 TK.MD 数据点）。"
          />
        ) : (
          <div
            className="industrial-realtime-paged-grid"
            style={{ "--realtime-paged-cols": columns }}
          >
            {visibleCards.map((card) => {
              const pulseOn = Boolean(card.machineStatus?.alarmActive) && !alarmPulseDismissed.has(card.sourceCode);
              return (
                <div className="industrial-realtime-paged-slot" key={card.sourceCode}>
                  <RealtimeDeviceCard
                    card={card}
                    pulseOn={pulseOn}
                    formatDateTime={formatDateTime}
                    onDismissAlarm={() => {
                      if (card.machineStatus?.alarmActive) {
                        setAlarmPulseDismissed((prev) => new Set(prev).add(card.sourceCode));
                      }
                    }}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {pageCount > 1 ? (
        <div className="industrial-realtime-page-dots" role="tablist" aria-label="设备监控分页">
          {Array.from({ length: pageCount }, (_, index) => (
            <button
              aria-label={`第 ${index + 1} 页`}
              aria-selected={index === activePageIndex}
              className={index === activePageIndex ? "industrial-realtime-page-dot active" : "industrial-realtime-page-dot"}
              key={index}
              onClick={() => goToPage(index)}
              role="tab"
              type="button"
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

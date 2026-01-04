"use client";

import { useRef, useMemo, useCallback, useEffect, useState } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { SelectableMediaCard } from "./SelectableMediaCard";
import { ContentDrawer } from "@/components/twelvelabs/ContentDrawer";

const GAP = 16;
const CARD_ASPECT = 9 / 16;

function useResponsiveLayout(containerRef: React.RefObject<any>) {
    const [layout, setLayout] = useState({ columns: 4, width: 0 });

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        const observer = new ResizeObserver((entries) => {
            const width = entries[0].contentRect.width;
            let columns = 1;
            // Breakpoints adjusted for container width
            if (width >= 1800) columns = 6;
            else if (width >= 1500) columns = 5;
            else if (width >= 1200) columns = 4;
            else if (width >= 900) columns = 3;
            else if (width >= 600) columns = 2;

            setLayout({ columns, width });
        });

        observer.observe(el);
        return () => observer.disconnect();
    }, [containerRef]);

    return layout;
}

export function VirtualizedResultsGrid({ results, analysisDisabled = false, itemsById }: any) {
    // console.log("[VirtualGrid] Render results:", results.length);

    // ✅ make our OWN scroll container
    const scrollRef = useRef<HTMLDivElement>(null);
    const parentRef = useRef<HTMLDivElement>(null);
    const [selectedItem, setSelectedItem] = useState<any | null>(null);
    const [selectedResumeTime, setSelectedResumeTime] = useState(0);

    // Use container width for columns
    const { columns, width } = useResponsiveLayout(scrollRef);

    const rows = useMemo(() => {
        const rowArray: any[][] = [];
        for (let i = 0; i < results.length; i += columns) rowArray.push(results.slice(i, i + columns));
        return rowArray;
    }, [results, columns]);

    const getRowHeight = useCallback(() => {
        const el = parentRef.current;
        if (!el) return 400;
        const containerWidth = el.offsetWidth;
        const cardWidth = (containerWidth - GAP * (columns - 1)) / columns;
        const cardHeight = cardWidth / CARD_ASPECT;
        return cardHeight + GAP;
    }, [columns]);

    const virtualizer = useVirtualizer({
        count: rows.length,
        getScrollElement: () => scrollRef.current,
        estimateSize: getRowHeight,
        overscan: 6,
        enabled: true,
    });

    useEffect(() => {
        // console.log("[VirtualGrid] Measuring. Rows:", rows.length, "Columns:", columns);
        virtualizer.measure();
    }, [columns, rows.length, width]);

    const virtualRows = virtualizer.getVirtualItems();

    return (
        <>
            <div ref={scrollRef} className="flex-1 min-h-0 w-full overflow-y-auto">
                <div
                    ref={parentRef}
                    className="w-full"
                    style={{
                        height: `${virtualizer.getTotalSize()}px`,
                        position: "relative",
                    }}
                >
                    {virtualRows.map((virtualRow) => {
                        const rowItems = rows[virtualRow.index];
                        return (
                            <div
                                key={virtualRow.key}
                                style={{
                                    position: "absolute",
                                    top: 0,
                                    left: 0,
                                    width: "100%",
                                    height: `${virtualRow.size - GAP}px`,
                                    transform: `translateY(${virtualRow.start}px)`,
                                }}
                            >
                                <div
                                    className="grid gap-4"
                                    style={{
                                        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
                                        height: "100%",
                                    }}
                                >
                                    {rowItems.map((item: any, colIndex: number) => (
                                        <div key={item.id || `${virtualRow.index}-${colIndex}`}>
                                            <SelectableMediaCard
                                                item={item}
                                                platform={item.platform || "unknown"}
                                                itemsById={itemsById}
                                                onOpen={(nextItem: any, resumeTime: number) => {
                                                    setSelectedItem(nextItem);
                                                    setSelectedResumeTime(resumeTime);
                                                }}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            <ContentDrawer
                isOpen={!!selectedItem}
                onClose={() => {
                    setSelectedItem(null);
                    setSelectedResumeTime(0);
                }}
                item={selectedItem}
                analysisDisabled={analysisDisabled}
                resumeTime={selectedResumeTime}
            />
        </>
    );
}

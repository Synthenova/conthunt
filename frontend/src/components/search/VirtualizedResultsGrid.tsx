"use client";

import { useRef, useMemo, useCallback, useState, useEffect } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { SelectableMediaCard } from "./SelectableMediaCard";
import { ContentDrawer } from "@/components/twelvelabs/ContentDrawer";

interface VirtualizedResultsGridProps {
    results: any[];
    analysisDisabled?: boolean;
    itemsById: Record<string, any>;
}

// Fixed card dimensions for 9:16 aspect ratio
const GAP = 16;
const CARD_ASPECT = 9 / 16;

function useResponsiveColumns() {
    const [columns, setColumns] = useState(4);

    useEffect(() => {
        const updateColumns = () => {
            const width = window.innerWidth;
            if (width >= 1280) setColumns(4);       // xl
            else if (width >= 1024) setColumns(3);  // lg
            else if (width >= 640) setColumns(2);   // sm
            else setColumns(1);
        };

        updateColumns();
        window.addEventListener("resize", updateColumns);
        return () => window.removeEventListener("resize", updateColumns);
    }, []);

    return columns;
}

export function VirtualizedResultsGrid({
    results,
    analysisDisabled = false,
    itemsById,
}: VirtualizedResultsGridProps) {
    const parentRef = useRef<HTMLDivElement>(null);
    const columns = useResponsiveColumns();
    const [selectedItem, setSelectedItem] = useState<any | null>(null);
    const [selectedResumeTime, setSelectedResumeTime] = useState(0);
    const [offsetTop, setOffsetTop] = useState(0);
    const [scroller, setScroller] = useState<HTMLElement | null>(null);

    // Group results into rows
    const rows = useMemo(() => {
        const rowArray: any[][] = [];
        for (let i = 0; i < results.length; i += columns) {
            rowArray.push(results.slice(i, i + columns));
        }
        return rowArray;
    }, [results, columns]);

    // Find scroll container and measure offset
    useEffect(() => {
        if (!parentRef.current) return;

        // Find the scrolling parent (should be the <main> tag in AppShell)
        const scrollParent = parentRef.current.closest('main');
        setScroller(scrollParent as HTMLElement);

        const updateOffset = () => {
            if (parentRef.current) {
                setOffsetTop(parentRef.current.offsetTop);
            }
        };

        // Initial measurement
        updateOffset();

        // Also measure after a short delay to account for layout shifts
        const timeout = setTimeout(updateOffset, 100);

        window.addEventListener("resize", updateOffset);
        return () => {
            window.removeEventListener("resize", updateOffset);
            clearTimeout(timeout);
        }
    }, []);

    // Calculate row height based on container width
    const getRowHeight = useCallback(() => {
        if (!parentRef.current) return 400; // Fallback
        const containerWidth = parentRef.current.offsetWidth;
        const cardWidth = (containerWidth - GAP * (columns - 1)) / columns;
        const cardHeight = cardWidth / CARD_ASPECT;
        return cardHeight + GAP;
    }, [columns]);

    // Use Element Virtualizer (scrolling 'main' not 'window')
    const virtualizer = useVirtualizer({
        count: rows.length,
        getScrollElement: () => scroller,
        estimateSize: getRowHeight,
        overscan: 2,
        scrollMargin: offsetTop,
    });

    const virtualRows = virtualizer.getVirtualItems();

    return (
        <>
            {/* Debug Overlay */}
            <div className="fixed bottom-4 left-4 z-50 bg-black/80 text-white p-2 rounded text-xs font-mono pointer-events-none">
                <div>Scroller Found: {scroller ? 'YES (MAIN)' : 'NO'}</div>
                <div>Offset via State: {offsetTop}px</div>
                <div>ScrollTop: {scroller?.scrollTop.toFixed(0) || 0}px</div>
                <div>Total Size: {virtualizer.getTotalSize()}px</div>
                <div>Rows: {virtualRows.length} ({virtualRows[0]?.index} - {virtualRows[virtualRows.length - 1]?.index})</div>
            </div>

            <div
                ref={parentRef}
                className="w-full"
                style={{
                    height: `${virtualizer.getTotalSize()}px`,
                    position: "relative",
                    contain: "strict",
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
                                {rowItems.map((item, colIndex) => (
                                    <div key={item.id || `${virtualRow.index}-${colIndex}`}>
                                        <SelectableMediaCard
                                            item={item}
                                            platform={item.platform || "unknown"}
                                            itemsById={itemsById}
                                            onOpen={(nextItem, resumeTime) => {
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

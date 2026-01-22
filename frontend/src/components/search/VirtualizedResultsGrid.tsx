"use client";

import { useRef, useMemo, useCallback, useEffect, useLayoutEffect, useState } from "react";
import { useVirtualizer, Virtualizer } from "@tanstack/react-virtual";
import { motion } from "framer-motion";
import { SelectableMediaCard } from "./SelectableMediaCard";
import { ContentDrawer } from "@/components/twelvelabs/ContentDrawer";
import { getResponsiveColumns } from "./gridUtils";
import { useChatStore } from "@/lib/chatStore";
import { scrollToAndHighlight } from "@/hooks/useScrollToMedia";

const GAP = 16;
const CARD_ASPECT = 9 / 16;

// ✅ Only track columns in state. Track width in a ref to avoid rerenders on every resize tick.
function useResponsiveColumns(
    containerRef: React.RefObject<any>,
    opts: {
        onResizeTick?: (width: number) => void;
        onColumnsChange?: (prev: number, next: number, width: number) => void;
    } = {}
) {
    const [columns, setColumns] = useState(4);

    useLayoutEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const width = el.getBoundingClientRect().width;
        if (!width) return;
        // Use queueMicrotask to defer state update and avoid flushSync conflicts
        queueMicrotask(() => {
            setColumns((prev) => {
                const nextCols = getResponsiveColumns(width, prev);
                opts.onResizeTick?.(width);
                if (prev !== nextCols) {
                    opts.onColumnsChange?.(prev, nextCols, width);
                    return nextCols;
                }
                return prev;
            });
        });
    }, [containerRef, opts]);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        let rafId: number | null = null;

        const observer = new ResizeObserver((entries) => {
            const width = entries[0]?.contentRect?.width ?? 0;
            if (!width) return;

            if (rafId) cancelAnimationFrame(rafId);
            rafId = requestAnimationFrame(() => {
                // Use queueMicrotask to defer state update and avoid flushSync conflicts
                queueMicrotask(() => {
                    setColumns((prev) => {
                        const nextCols = getResponsiveColumns(width, prev);
                        opts.onResizeTick?.(width);
                        if (prev !== nextCols) {
                            opts.onColumnsChange?.(prev, nextCols, width);
                            return nextCols;
                        }
                        return prev;
                    });
                });
            });
        });

        observer.observe(el);

        return () => {
            if (rafId) cancelAnimationFrame(rafId);
            observer.disconnect();
        };
    }, [containerRef, opts]);

    return columns;
}

export function VirtualizedResultsGrid({
    results,
    analysisDisabled = false,
    itemsByIdRef,
    scrollRef,
    onMediaError,
}: {
    results: any[];
    analysisDisabled?: boolean;
    itemsByIdRef: React.MutableRefObject<Record<string, any>>;
    scrollRef: React.RefObject<HTMLDivElement | null>;
    onMediaError?: (id: string) => void;
}) {
    const parentRef = useRef<HTMLDivElement>(null);

    const [selectedItem, setSelectedItem] = useState<any | null>(null);
    const [selectedResumeTime, setSelectedResumeTime] = useState(0);

    // --- Resize smoothing controls ---
    const widthRef = useRef(0);
    const rafMeasureRef = useRef<number | null>(null);
    const resizeEndTimerRef = useRef<number | null>(null);
    const [isResizing, setIsResizing] = useState(false);

    const scheduleMeasure = useCallback((reason: string) => {
        if (rafMeasureRef.current) cancelAnimationFrame(rafMeasureRef.current);
        rafMeasureRef.current = requestAnimationFrame(() => {
            virtualizerRef.current?.measure();
        });
    }, []);

    const markResizing = useCallback((reason: string) => {
        if (!isResizing) setIsResizing(true);

        if (resizeEndTimerRef.current) window.clearTimeout(resizeEndTimerRef.current);
        resizeEndTimerRef.current = window.setTimeout(() => {
            setIsResizing(false);
            scheduleMeasure("resize-end");
        }, 180);
    }, [isResizing, scheduleMeasure]);

    // We need the virtualizer instance inside scheduleMeasure, so keep a ref
    const virtualizerRef = useRef<Virtualizer<HTMLDivElement, Element> | null>(null);

    const columns = useResponsiveColumns(scrollRef, {
        onResizeTick: (w) => {
            widthRef.current = w;
            // Only trigger resize state, but DON'T re-measure on every tick.
            // Re-measurement happens only when columns change or resize ends.
            markResizing("resize-tick");
        },
        onColumnsChange: (prev, next, width) => {
            console.log("[VirtualizedResultsGrid] cols", prev, "->", next, "width", Math.round(width));
            markResizing("columns-change");
            scheduleMeasure("columns-change");
        },
    });

    // Group results into rows
    const rows = useMemo(() => {
        const rowArray: any[][] = [];
        for (let i = 0; i < results.length; i += columns) {
            rowArray.push(results.slice(i, i + columns));
        }
        return rowArray;
    }, [results, columns]);

    // Estimate row height (fast). Real cards may have extra footer height; ok.
    const estimateRowHeight = useCallback(() => {
        const el = parentRef.current;
        if (!el) return 400;
        const containerWidth = el.offsetWidth;
        const cardWidth = (containerWidth - GAP * (columns - 1)) / columns;
        const mediaHeight = cardWidth / CARD_ASPECT;
        // add some footer space so estimate is closer and reduces jump
        return Math.ceil(mediaHeight + GAP);
    }, [columns]);

    const virtualizer = useVirtualizer({
        count: rows.length,
        getScrollElement: () => scrollRef.current,
        estimateSize: estimateRowHeight,
        overscan: 6,
        enabled: true,
    });

    virtualizerRef.current = virtualizer;

    // One solid measure when data/columns changes
    useEffect(() => {
        virtualizer.measure();
    }, [columns, rows.length]); // intentionally no width

    // Register scroll handler to store
    const { setCanvasScrollToItem } = useChatStore();

    useEffect(() => {
        const handleScrollToItem = async (itemId: string): Promise<boolean> => {
            console.log('[VirtualizedResultsGrid] handleScrollToItem called for:', itemId);

            // 1. Find the item index in the flat results array
            const index = results.findIndex((item) => {
                // Check item ID
                if (item.id === itemId) return true;
                // Check media asset ID
                const videoAsset = item.assets?.find((a: any) => a.asset_type === 'video');
                if (videoAsset?.id === itemId) return true;
                return false;
            });

            if (index === -1) {
                console.log('[VirtualizedResultsGrid] Item not found in results:', itemId);
                return false;
            }

            // 2. Calculate row index
            const rowIndex = Math.floor(index / columns);
            console.log('[VirtualizedResultsGrid] Found item at index:', index, 'rowIndex:', rowIndex);

            // 3. Scroll to that row (smooth animation)
            virtualizer.scrollToIndex(rowIndex, { align: 'center', behavior: 'smooth' });

            // 4. Wait for scroll animation to complete by detecting scroll position stability
            // Note: virtualizer.isScrolling is unreliable for programmatic scrolls, so we detect
            // scroll completion by waiting until scrollTop stops changing for 100ms
            const waitForScrollComplete = async (): Promise<boolean> => {
                const scrollEl = scrollRef.current;
                if (!scrollEl) return false;

                const maxWaitMs = 3000; // Max 3 seconds for very long scrolls
                const stabilityThresholdMs = 100; // Consider scroll "done" after 100ms of no movement
                let lastScrollTop = scrollEl.scrollTop;
                let stableTime = 0;
                let elapsed = 0;
                const pollIntervalMs = 20;

                // Small initial delay to let scroll animation start
                await new Promise(r => setTimeout(r, 50));

                while (elapsed < maxWaitMs) {
                    const currentScrollTop = scrollEl.scrollTop;

                    if (currentScrollTop === lastScrollTop) {
                        stableTime += pollIntervalMs;
                        if (stableTime >= stabilityThresholdMs) {
                            console.log('[VirtualizedResultsGrid] Scroll completed (stable) after', elapsed, 'ms');
                            return true;
                        }
                    } else {
                        stableTime = 0; // Reset stability counter on movement
                        lastScrollTop = currentScrollTop;
                    }

                    await new Promise(r => setTimeout(r, pollIntervalMs));
                    elapsed += pollIntervalMs;
                }
                console.log('[VirtualizedResultsGrid] Scroll timed out after 3s');
                return false;
            };

            await waitForScrollComplete();

            // 5. Small buffer for React to render the new rows after scroll settles
            await new Promise(r => setTimeout(r, 100));

            // 6. Poll for DOM element (now with confidence it should exist)
            let attempts = 0;
            const maxAttempts = 10; // Increased attempts

            while (attempts < maxAttempts) {
                const success = scrollToAndHighlight(itemId);
                if (success) {
                    return true;
                }
                attempts++;
                await new Promise(r => setTimeout(r, 50));
            }

            console.log('[VirtualizedResultsGrid] Failed to find DOM element after scrolling');
            return false;
        };

        setCanvasScrollToItem(handleScrollToItem);

        return () => {
            setCanvasScrollToItem(null);
        };
    }, [results, columns, virtualizer, setCanvasScrollToItem]);

    const virtualRows = virtualizer.getVirtualItems();

    // stable onOpen callback (pairs well with React.memo children)
    const handleOpen = useCallback((nextItem: any, resumeTime: number) => {
        setSelectedItem(nextItem);
        setSelectedResumeTime(resumeTime);
    }, []);

    return (
        <>
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
                                // ✅ Smooth ONLY during resize (keep scrolling snappy)
                                transition: isResizing ? "transform 160ms ease" : "none",
                                willChange: "transform",
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
                                    <motion.div
                                        key={item.id || `${virtualRow.index}-${colIndex}`}
                                        layout={false}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ duration: 0.18, ease: "easeOut" }}
                                        style={{ height: "100%" }}
                                    >
                                        <SelectableMediaCard
                                            item={item}
                                            platform={item.platform || "unknown"}
                                            itemsByIdRef={itemsByIdRef}
                                            onOpen={handleOpen}
                                            onError={onMediaError}
                                        />
                                    </motion.div>
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

"use client";

import { useMemo, useEffect, useRef, useState, ReactNode, useCallback } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { VirtualizedResultsGrid } from "./VirtualizedResultsGrid";
import { getResponsiveColumns } from "./gridUtils";

interface SelectableResultsGridProps {
    results: any[];
    loading: boolean;
    analysisDisabled?: boolean;
    scrollRef?: React.RefObject<HTMLDivElement | null>;
    footer?: ReactNode;
}

export function SelectableResultsGrid({ results, loading, analysisDisabled = false, scrollRef, footer }: SelectableResultsGridProps) {
    const internalScrollRef = useRef<HTMLDivElement>(null);
    const resolvedScrollRef = scrollRef ?? internalScrollRef;
    const [skeletonColumns, setSkeletonColumns] = useState(4);
    const lastSkeletonColsRef = useRef<number | null>(null);

    useEffect(() => {
        const el = resolvedScrollRef.current;
        if (!el) return;

        let rafId: number | null = null;
        const updateWidth = (width: number) => {
            if (!width) return;
            if (rafId) cancelAnimationFrame(rafId);
            rafId = requestAnimationFrame(() => {
                // Use queueMicrotask to defer state update and avoid flushSync conflicts
                queueMicrotask(() => {
                    setSkeletonColumns((prev) => {
                        const nextCols = getResponsiveColumns(width, prev);
                        if (lastSkeletonColsRef.current !== nextCols) {
                            lastSkeletonColsRef.current = nextCols;
                            console.log("[SelectableResultsGrid] skeleton cols", nextCols, "width", Math.round(width));
                        }
                        return nextCols;
                    });
                });
            });
        };

        updateWidth(el.getBoundingClientRect().width);

        const observer = new ResizeObserver((entries) => {
            const width = entries[0]?.contentRect?.width ?? 0;
            updateWidth(width);
        });

        observer.observe(el);
        return () => {
            if (rafId) cancelAnimationFrame(rafId);
            observer.disconnect();
        };
    }, [scrollRef]);

    const [hiddenIds, setHiddenIds] = useState<Set<string>>(new Set());

    const handleMediaError = useCallback((id: string) => {
        setHiddenIds((prev) => {
            const next = new Set(prev);
            next.add(id);
            return next;
        });
    }, []);

    const visibleResults = useMemo(() => {
        if (hiddenIds.size === 0) return results;
        return results.filter(item => !hiddenIds.has(item.id));
    }, [results, hiddenIds]);

    // We use a ref to hold the map so we can pass a stable reference to child components.
    // This prevents them from re-rendering just because the map *content* changed,
    // as long as they don't *need* the new content immediately for rendering (SelectableMediaCard mainly needs it for drag/drop).
    const itemsByIdRef = useRef<Record<string, any>>({});

    useEffect(() => {
        const map: Record<string, any> = {};
        visibleResults.forEach((item) => {
            if (item?.id) {
                map[item.id] = item;
            }
        });
        itemsByIdRef.current = map;
    }, [visibleResults]);

    let content: ReactNode;
    if (loading) {
        const skeletonCount = Math.max(8, skeletonColumns * 2);
        content = (
            <div
                className="grid gap-4 w-full"
                style={{ gridTemplateColumns: `repeat(${skeletonColumns}, minmax(0, 1fr))` }}
            >
                {[...Array(skeletonCount)].map((_, i) => (
                    <div key={i} className="aspect-[9/16] rounded-xl overflow-hidden">
                        <Skeleton className="h-full w-full" />
                    </div>
                ))}
            </div>
        );
    } else if (!results || results.length === 0) {
        content = (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
                <div className="h-24 w-24 rounded-full bg-white/5 flex items-center justify-center mb-4">
                    <span className="text-4xl">🔍</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">Ready to Hunt?</h3>
                <p className="text-muted-foreground max-w-sm">
                    Enter a keyword above to search across Instagram, TikTok, YouTube, and more simultaneously.
                </p>
            </div>
        );
    } else {
        content = (
            <VirtualizedResultsGrid
                results={visibleResults}
                analysisDisabled={analysisDisabled}
                itemsByIdRef={itemsByIdRef} // Pass ref instead of value
                scrollRef={resolvedScrollRef}
                onMediaError={handleMediaError}
            />
        );
    }

    return (
        <div ref={resolvedScrollRef} className="flex-1 min-h-0 w-full overflow-y-auto p-2">
            {content}
            {footer ? <div className="w-full">{footer}</div> : null}
        </div>
    );
}

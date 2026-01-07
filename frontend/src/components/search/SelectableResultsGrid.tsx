"use client";

import { useMemo, useEffect, useRef, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { VirtualizedResultsGrid } from "./VirtualizedResultsGrid";
import { getResponsiveColumns } from "./gridUtils";

interface SelectableResultsGridProps {
    results: any[];
    loading: boolean;
    analysisDisabled?: boolean;
    scrollRef?: React.RefObject<HTMLDivElement | null>;
}

export function SelectableResultsGrid({ results, loading, analysisDisabled = false, scrollRef }: SelectableResultsGridProps) {
    const skeletonRef = useRef<HTMLDivElement>(null);
    const [skeletonColumns, setSkeletonColumns] = useState(4);

    useEffect(() => {
        const el = skeletonRef.current;
        if (!el) return;

        let rafId: number | null = null;
        const observer = new ResizeObserver((entries) => {
            const width = entries[0]?.contentRect?.width ?? 0;
            if (!width) return;
            if (rafId) cancelAnimationFrame(rafId);
            rafId = requestAnimationFrame(() => {
                setSkeletonColumns(getResponsiveColumns(width));
            });
        });

        observer.observe(el);
        return () => {
            if (rafId) cancelAnimationFrame(rafId);
            observer.disconnect();
        };
    }, []);

    const itemsById = useMemo(() => {
        const map: Record<string, any> = {};
        results.forEach((item) => {
            if (item?.id) {
                map[item.id] = item;
            }
        });
        return map;
    }, [results]);

    if (loading) {
        const skeletonCount = Math.max(8, skeletonColumns * 2);
        return (
            <div
                ref={skeletonRef}
                className="grid gap-4 p-2 w-full"
                style={{ gridTemplateColumns: `repeat(${skeletonColumns}, minmax(0, 1fr))` }}
            >
                {[...Array(skeletonCount)].map((_, i) => (
                    <div key={i} className="aspect-[9/16] rounded-xl overflow-hidden">
                        <Skeleton className="h-full w-full" />
                    </div>
                ))}
            </div>
        );
    }

    if (!results || results.length === 0) {
        return (
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
    }

    return (
        <VirtualizedResultsGrid
            results={results}
            analysisDisabled={analysisDisabled}
            itemsById={itemsById}
            scrollRef={scrollRef}
        />
    );
}

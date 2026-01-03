"use client";

import { useMemo } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { VirtualizedResultsGrid } from "./VirtualizedResultsGrid";

interface SelectableResultsGridProps {
    results: any[];
    loading: boolean;
    analysisDisabled?: boolean;
}

export function SelectableResultsGrid({ results, loading, analysisDisabled = false }: SelectableResultsGridProps) {
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
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {[...Array(10)].map((_, i) => (
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
        />
    );
}

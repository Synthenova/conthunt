
import { useState, useCallback, useEffect } from "react";
import { FlatMediaItem } from "@/lib/transformers";
import type { ClientFilters } from "@/lib/clientFilters";
import { useLoadMore } from "@/hooks/useLoadMore";
import { transformSearchResults } from "@/lib/transformers";

export function useChatSearchState(activeSearchId: string | null) {
    const [resultsMap, setResultsMap] = useState<Record<string, FlatMediaItem[]>>({});
    const [streamingSearchIds, setStreamingSearchIds] = useState<Record<string, boolean>>({});
    const [loadingSearchIds, setLoadingSearchIds] = useState<Record<string, boolean>>({});
    const [cursorsMap, setCursorsMap] = useState<Record<string, Record<string, any>>>({});
    const [hasMoreMap, setHasMoreMap] = useState<Record<string, boolean>>({});

    // rawSearchResults aggregation kept for compatibility if needed, though strictly not used for rendering active view
    const [allResults, setAllResults] = useState<FlatMediaItem[]>([]);

    const handleSearchResults = useCallback((id: string, items: FlatMediaItem[]) => {
        setResultsMap(prev => {
            if (JSON.stringify(prev[id]) === JSON.stringify(items)) return prev;
            return { ...prev, [id]: items };
        });
    }, []);

    const handleSearchStreamingChange = useCallback((id: string, isStreaming: boolean) => {
        setStreamingSearchIds(prev => {
            if (prev[id] === isStreaming) return prev;
            return { ...prev, [id]: isStreaming };
        });
    }, []);

    const handleSearchLoadingChange = useCallback((id: string, isLoading: boolean) => {
        setLoadingSearchIds(prev => {
            if (prev[id] === isLoading) return prev;
            return { ...prev, [id]: isLoading };
        });
    }, []);

    const handleSearchCursorsChange = useCallback((id: string, cursors: Record<string, any>, hasMore: boolean) => {
        setCursorsMap(prev => {
            if (JSON.stringify(prev[id]) === JSON.stringify(cursors)) return prev;
            return { ...prev, [id]: cursors };
        });
        setHasMoreMap(prev => {
            if (prev[id] === hasMore) return prev;
            return { ...prev, [id]: hasMore };
        });
    }, []);

    // Load More hook
    const { loadMore, isLoading: isLoadingMore } = useLoadMore(activeSearchId);

    const handleLoadMore = useCallback((filters?: ClientFilters) => {
        if (!activeSearchId) return;

        loadMore(
            // onNewResults - append new items
            (newItems) => {
                const transformed = transformSearchResults(newItems);
                setResultsMap(prev => {
                    const existing = prev[activeSearchId] || [];
                    const existingIds = new Set(existing.map(item => item.id));
                    const uniqueNew = transformed.filter(item => !existingIds.has(item.id));
                    return { ...prev, [activeSearchId]: [...existing, ...uniqueNew] };
                });
            },
            // onNewCursors - update cursors
            (newCursors) => {
                setCursorsMap(prev => ({ ...prev, [activeSearchId]: newCursors }));
                setHasMoreMap(prev => ({ ...prev, [activeSearchId]: Object.keys(newCursors).length > 0 }));
            },
            filters
        );
    }, [activeSearchId, loadMore]);

    // Flatten results for display
    useEffect(() => {
        // Aggregate all values from resultsMap
        const aggregated = Object.values(resultsMap).flat();
        // Remove duplicates by ID
        const unique = new Map();
        aggregated.forEach(item => unique.set(item.id, item));
        const merged = Array.from(unique.values());
        setAllResults(merged);
    }, [resultsMap]);

    return {
        resultsMap,
        setResultsMap,
        streamingSearchIds,
        loadingSearchIds,
        cursorsMap,
        hasMoreMap,
        allResults,
        handleSearchResults,
        handleSearchStreamingChange,
        handleSearchLoadingChange,
        handleSearchCursorsChange,
        handleLoadMore,
        isLoadingMore,
        hasMoreMapValue: activeSearchId ? (hasMoreMap[activeSearchId] ?? false) : false
    };
}

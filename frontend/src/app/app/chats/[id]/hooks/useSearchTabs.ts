
import { useState, useMemo, useEffect, useRef } from "react";
import { useChatTags } from "@/hooks/useChatTags";

export function useSearchTabs(chatId: string, activeSearchId: string | null, setActiveSearchId: (id: string | null) => void) {
    const { tagsQuery, deleteTag } = useChatTags(chatId);
    const [searchTabs, setSearchTabs] = useState<Array<{ id: string; label: string; sort_order?: number | null }>>([]);

    // derive searches from chat tags (search only)
    const searchTags = useMemo(() => {
        const tags = tagsQuery.data || [];
        return tags
            .filter((t) => t.type === 'search')
            .map((t) => ({
                id: t.id,
                label: t.label || t.id,
                sort_order: t.sort_order ?? null,
                created_at: t.created_at || null,
            }));
    }, [tagsQuery.data]);

    // sync searchTabs state with fetched tags, keep new tags at top
    useEffect(() => {
        if (!searchTags.length) {
            setSearchTabs([]);
            return;
        }
        setSearchTabs((prev) => {
            const seen = new Set<string>();
            const mapped = prev.filter((p) => {
                if (seen.has(p.id)) return false;
                seen.add(p.id);
                return searchTags.some((t) => t.id === p.id);
            });

            // Add new tags not in prev
            searchTags.forEach((t) => {
                if (!seen.has(t.id)) {
                    mapped.unshift({ id: t.id, label: t.label, sort_order: t.sort_order });
                    seen.add(t.id);
                }
            });

            // Sort by sort_order ascending (smaller is newer), then created_at desc via searchTags list order
            const tagMap = new Map(searchTags.map((t) => [t.id, t]));
            mapped.sort((a, b) => {
                const ta = tagMap.get(a.id);
                const tb = tagMap.get(b.id);
                const ao = ta?.sort_order ?? 0;
                const bo = tb?.sort_order ?? 0;
                if (ao !== bo) return ao - bo;
                const ac = ta?.created_at ? new Date(ta.created_at).getTime() : 0;
                const bc = tb?.created_at ? new Date(tb.created_at).getTime() : 0;
                return bc - ac;
            });

            return mapped;
        });
    }, [searchTags]);

    // Unified list of searches with labels for display
    const displaySearches = useMemo(() => searchTabs, [searchTabs]);

    // Combine all search IDs (history + live canvas)
    const allSearchIds = useMemo(() => {
        return displaySearches.map(s => s.id);
    }, [displaySearches]);

    // Effect: Auto-select latest search
    useEffect(() => {
        if (allSearchIds.length > 0) {
            const latestId = allSearchIds[0];
            const nextActive = !activeSearchId || (!allSearchIds.includes(activeSearchId) && activeSearchId !== "deep-research")
                ? latestId
                : activeSearchId;
            setActiveSearchId(nextActive);
        }
    }, [allSearchIds, activeSearchId, setActiveSearchId]);

    // Better Auto-switch logic using ref
    const prevSearchCountRef = useRef(0);
    useEffect(() => {
        // If user is on the Deep Research tab, don't auto-switch away when new searches arrive.
        if (activeSearchId === "deep-research") {
            prevSearchCountRef.current = allSearchIds.length;
            return;
        }
        if (allSearchIds.length > prevSearchCountRef.current) {
            // New search added! Switch to it (top of list).
            const latest = allSearchIds[0];
            setActiveSearchId(latest);
        } else if (allSearchIds.length > 0 && !activeSearchId) {
            setActiveSearchId(allSearchIds[0]);
        }
        prevSearchCountRef.current = allSearchIds.length;
    }, [allSearchIds, activeSearchId, setActiveSearchId]);

    const handleTabDelete = (searchId: string) => {
        deleteTag.mutate(searchId);
        if (activeSearchId === searchId) {
            const currentIndex = displaySearches.findIndex(s => s.id === searchId);
            const prevSearch = displaySearches[currentIndex - 1];
            const nextSearch = displaySearches[currentIndex + 1];
            setActiveSearchId(prevSearch?.id || nextSearch?.id || null);
        }
    };

    return {
        displaySearches,
        allSearchIds,
        handleTabDelete
    };
}

import { useState, useMemo } from "react";
import { FlatMediaItem, transformSearchResults } from "@/lib/transformers";
import { ClientSortOption, ClientDateFilter } from "@/components/search/ClientResultControls";

interface UseClientResultSortOptions {
    resultsAreFlat?: boolean;
}

export function useClientResultSort(rawResults: any[], options: UseClientResultSortOptions = {}) {
    const [clientSort, setClientSort] = useState<ClientSortOption>("default");
    const [clientDateFilter, setClientDateFilter] = useState<ClientDateFilter>("all");
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
    const { resultsAreFlat = false } = options;

    const baseResults = useMemo(() => {
        return resultsAreFlat
            ? [...(rawResults || [])]
            : transformSearchResults(rawResults || []);
    }, [rawResults, resultsAreFlat]);

    const platforms = useMemo(() => {
        const set = new Set<string>();
        baseResults.forEach(item => {
            if (item.platform) set.add(item.platform.toLowerCase());
        });
        return Array.from(set).sort();
    }, [baseResults]);

    const flatResults = useMemo(() => {
        let results: FlatMediaItem[] = [...baseResults];

        // 0. Platform Filtering
        if (selectedPlatforms.length > 0) {
            results = results.filter(item => {
                const p = String(item.platform || "").toLowerCase();
                return selectedPlatforms.includes(p);
            });
        }

        // 1. Client-Side Filtering (Date)
        if (clientDateFilter !== "all") {
            const now = new Date();
            const oneDay = 24 * 60 * 60 * 1000;
            const sevenDays = 7 * oneDay;
            const thirtyDays = 30 * oneDay;
            const ninetyDays = 90 * oneDay;
            const sixMonths = 180 * oneDay;
            const oneYear = 365 * oneDay;

            // For "yesterday", "this_week", "this_month" calculations
            const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const yesterdayStart = new Date(todayStart);
            yesterdayStart.setDate(yesterdayStart.getDate() - 1);
            const yesterdayEnd = new Date(todayStart); // Yesterday ends at today 00:00:00

            // Start of this week (assuming Monday start)
            const currentDay = todayStart.getDay(); // 0 is Sunday
            const distanceToMonday = currentDay === 0 ? 6 : currentDay - 1;
            const thisWeekStart = new Date(todayStart);
            thisWeekStart.setDate(todayStart.getDate() - distanceToMonday);

            const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);

            results = results.filter(item => {
                if (!item.published_at) return false;
                const date = new Date(item.published_at);
                const diffTime = now.getTime() - date.getTime();
                // Ensure we don't filter out future dates by accident if any (though usually strictly past)
                // but checking diffTime > 0 is safer, or abs()

                switch (clientDateFilter) {
                    case "today":
                        return date >= todayStart;
                    case "yesterday":
                        return date >= yesterdayStart && date < yesterdayEnd;
                    case "week":
                        // Rolling 7 days
                        return diffTime < sevenDays && diffTime >= 0;
                    case "this_week":
                        return date >= thisWeekStart;
                    case "month":
                        // Rolling 30 days
                        return diffTime < thirtyDays && diffTime >= 0;
                    case "this_month":
                        return date >= thisMonthStart;
                    case "three_months":
                        return diffTime < ninetyDays && diffTime >= 0;
                    case "six_months":
                        return diffTime < sixMonths && diffTime >= 0;
                    case "year":
                        return diffTime < oneYear && diffTime >= 0;
                    default:
                        return true;
                }
            });
        }

        // 2. Client-Side Sorting
        if (clientSort !== "default") {
            results.sort((a, b) => {
                let valA = 0;
                let valB = 0;

                switch (clientSort) {
                    case "views":
                        valA = a.view_count || 0;
                        valB = b.view_count || 0;
                        break;
                    case "likes":
                        valA = a.like_count || 0;
                        valB = b.like_count || 0;
                        break;
                    case "shares":
                        valA = a.share_count || 0;
                        valB = b.share_count || 0;
                        break;
                    case "comments":
                        valA = a.comment_count || 0;
                        valB = b.comment_count || 0;
                        break;
                    case "newest":
                        valA = a.published_at ? new Date(a.published_at).getTime() : 0;
                        valB = b.published_at ? new Date(b.published_at).getTime() : 0;
                        break;
                }

                // Descending order
                return valB - valA;
            });
        }

        // 3. Platform Ordering: push YouTube items to the end while keeping other ordering intact
        const nonYoutube: FlatMediaItem[] = [];
        const youtube: FlatMediaItem[] = [];
        for (const item of results) {
            const platform = String(item.platform || "").toLowerCase();
            if (platform === "youtube") {
                youtube.push(item);
            } else {
                nonYoutube.push(item);
            }
        }
        results = [...nonYoutube, ...youtube];

        return results;
    }, [baseResults, clientSort, clientDateFilter, selectedPlatforms]);

    return {
        baseResults,
        flatResults,
        clientSort,
        setClientSort,
        clientDateFilter,
        setClientDateFilter,
        platforms,
        selectedPlatforms,
        setSelectedPlatforms
    };
}

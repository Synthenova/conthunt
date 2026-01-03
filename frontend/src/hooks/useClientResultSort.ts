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
            const sixMonths = 6 * thirtyDays;
            const oneYear = 365 * oneDay;

            results = results.filter(item => {
                if (!item.published_at) return false;
                const date = new Date(item.published_at);
                const diffTime = Math.abs(now.getTime() - date.getTime());

                switch (clientDateFilter) {
                    case "today":
                        return diffTime < oneDay;
                    case "week":
                        return diffTime < sevenDays;
                    case "month":
                        return diffTime < thirtyDays;
                    case "six_months":
                        return diffTime < sixMonths;
                    case "year":
                        return diffTime < oneYear;
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

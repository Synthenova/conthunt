import { useState, useMemo } from "react";
import { FlatMediaItem, transformSearchResults } from "@/lib/transformers";
import { ClientSortOption, ClientDateFilter } from "@/components/search/ClientResultControls";

interface UseClientResultSortOptions {
    resultsAreFlat?: boolean;
}

export function useClientResultSort(rawResults: any[], options: UseClientResultSortOptions = {}) {
    const [clientSort, setClientSort] = useState<ClientSortOption>("default");
    const [clientDateFilter, setClientDateFilter] = useState<ClientDateFilter>("all");
    const { resultsAreFlat = false } = options;

    const baseResults = useMemo(() => {
        return resultsAreFlat
            ? [...(rawResults || [])]
            : transformSearchResults(rawResults || []);
    }, [rawResults, resultsAreFlat]);

    const flatResults = useMemo(() => {
        let results: FlatMediaItem[] = [...baseResults];

        // 1. Client-Side Filtering (Date)
        if (clientDateFilter !== "all") {
            const now = new Date();
            const oneDay = 24 * 60 * 60 * 1000;

            results = results.filter(item => {
                if (!item.published_at) return false;
                const date = new Date(item.published_at);
                const diffTime = Math.abs(now.getTime() - date.getTime());

                if (clientDateFilter === "today") return diffTime < oneDay;
                if (clientDateFilter === "week") return diffTime < (7 * oneDay);
                if (clientDateFilter === "month") return diffTime < (30 * oneDay);
                return true;
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

        return results;
    }, [baseResults, clientSort, clientDateFilter]);

    return {
        baseResults,
        flatResults,
        clientSort,
        setClientSort,
        clientDateFilter,
        setClientDateFilter
    };
}

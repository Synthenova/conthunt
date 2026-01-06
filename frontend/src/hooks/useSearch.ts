import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchStore } from "@/lib/store";
import { auth } from "@/lib/firebaseClient";
import { useState, useMemo } from "react";

import { BACKEND_URL, authFetch } from '@/lib/api';

// Define response types
export interface SearchResponse {
    search_id: string;
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const res = await authFetch(url, options);
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || "API request failed");
    }
    return res.json();
}

export function useSearch() {
    const store = useSearchStore();
    const queryClient = useQueryClient();
    const { setActiveSearchId } = store;

    // State for pagination and results (used by detail page now)
    const [cursors, setCursors] = useState<Record<string, any>>({});

    const getParams = (platform: string, cursor?: any) => {
        const platformFilters = store.filters[platform] || {};
        const sortValue = store.sortBy[platform];

        const params: any = { ...platformFilters };

        // Add Sort
        if (sortValue) {
            if (platform === 'youtube') params.sortBy = sortValue;
            else if (platform === 'tiktok_keyword') params.sort_type = sortValue;
            else params.sort_by = sortValue;
        }

        // Add Cursor if loading more
        if (cursor) {
            Object.assign(params, cursor);
        }

        return params;
    };

    // 1. Search Mutation (POST /v1/search) - Now returns search_id and redirects
    const searchMutation = useMutation({
        onMutate: () => {
            setActiveSearchId(null);
        },
        mutationFn: async () => {
            const body = {
                query: store.query,
                inputs: {} as any
            };

            // Transform store inputs to API format
            const inputs: Record<string, any> = {};
            const platformKeys = Object.keys(store.platformInputs) as Array<keyof typeof store.platformInputs>;
            const activeKeys = platformKeys.filter(k => store.platformInputs[k]);

            activeKeys.forEach(key => {
                inputs[key] = getParams(key);
            });

            body.inputs = inputs;

            // Get Token
            const user = auth.currentUser;
            if (!user) throw new Error("User not authenticated");
            const token = await user.getIdToken();

            const res = await fetch(`${BACKEND_URL}/v1/search`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const error = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(error.detail || "Search failed");
            }

            return res.json() as Promise<SearchResponse>;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["searchHistory"] });
            setActiveSearchId(data.search_id);
        },
    });

    const hasMore = useMemo(() => {
        // We have more if any active platform (except Instagram) has a cursor
        const activeNonInsta = (Object.keys(store.platformInputs) as Array<keyof typeof store.platformInputs>)
            .filter(k => store.platformInputs[k] && k !== 'instagram_reels');

        return activeNonInsta.some(k => !!cursors[k]);
    }, [cursors, store.platformInputs]);

    // 2. History Query (GET /v1/searches)
    const historyQuery = useQuery({
        queryKey: ["searchHistory"],
        queryFn: () => fetchWithAuth(`${BACKEND_URL}/v1/searches`),
    });

    // 3. Get Single Search (GET /v1/searches/:id)
    const getSearch = (id: string) => useQuery({
        queryKey: ["search", id],
        queryFn: () => fetchWithAuth(`${BACKEND_URL}/v1/searches/${id}`),
        enabled: !!id,
    });

    return {
        ...store,
        search: () => {
            searchMutation.mutate();
        },
        isSearching: searchMutation.isPending,
        searchError: searchMutation.error,
        history: historyQuery.data?.searches || [],
        isLoadingHistory: historyQuery.isLoading,
        getSearch,
        hasMore,
        setCursors,
    };
}

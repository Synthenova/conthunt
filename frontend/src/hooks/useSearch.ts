import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchStore } from "@/lib/store";
import { auth } from "@/lib/firebaseClient";
import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";

// Define response types
export interface SearchResponse {
    search_id: string;
    platforms: Record<string, any>;
    results: any[];
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const user = auth.currentUser;
    if (!user) throw new Error("User not authenticated");

    const token = await user.getIdToken();
    const headers = {
        ...options.headers,
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
    };

    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || "API request failed");
    }
    return res.json();
}

export function useSearch() {
    const store = useSearchStore();
    const router = useRouter();
    const queryClient = useQueryClient();

    // State for pagination and results
    const [results, setResults] = useState<any[]>([]);
    const [cursors, setCursors] = useState<Record<string, any>>({});

    const getParams = (platform: string, cursor?: any) => {
        const platformFilters = store.filters[platform] || {};
        const sortValue = store.sortBy[platform];

        // Base params: filters + default amount (backend handles default)
        // We only send amount for Instagram really, but store.limit is legacy now effectively
        // unless we want to keep using it for initial request? User said remove it. 
        // We'll just pass filters.
        const params: any = { ...platformFilters };

        // Add Sort
        if (sortValue) {
            if (platform === 'youtube') params.sortBy = sortValue;
            else if (platform === 'tiktok_keyword') params.sort_type = sortValue;
            else params.sort_by = sortValue;
        }

        // Add Cursor if loading more
        if (cursor) {
            // different platforms have different cursor keys in request?
            // Base adapter usually expects just passed params.
            // Let's check schemas... next_cursor is a dict like {cursor: "..."} or {continuationToken: "..."}
            // So we can just spread it.
            Object.assign(params, cursor);
        }

        return params;
    };

    // 1. Search Mutation (POST /v1/search)
    const searchMutation = useMutation({
        mutationFn: async ({ isLoadMore = false }: { isLoadMore?: boolean } = {}) => {
            const body = {
                query: store.query,
                inputs: {} as any
            };

            // Transform store inputs to API format
            const inputs: Record<string, any> = {};

            // Determine which platforms to include
            const platformKeys = Object.keys(store.platformInputs) as Array<keyof typeof store.platformInputs>;
            const activeKeys = platformKeys.filter(k => store.platformInputs[k]);

            let platformsToFetch = activeKeys;

            if (isLoadMore) {
                // If loading more, only include platforms that have a next cursor
                // AND are NOT instagram (per user request)
                platformsToFetch = activeKeys.filter(key => {
                    if (key === 'instagram_reels') return false; // Explicitly exclude Instagram
                    return !!cursors[key]; // Must have a cursor
                });

                if (platformsToFetch.length === 0) {
                    return null; // Nothing to fetch
                }
            }

            platformsToFetch.forEach(key => {
                const cursor = isLoadMore ? cursors[key] : undefined;
                inputs[key] = getParams(key, cursor);
            });

            body.inputs = inputs;

            return fetchWithAuth("http://localhost:8000/v1/search", {
                method: "POST",
                body: JSON.stringify(body),
            });
        },
        onSuccess: (data: SearchResponse, variables) => {
            if (!data) return; // Case where loadMore had nothing to do

            if (variables.isLoadMore) {
                // Append results (filter duplicates)
                setResults(prev => {
                    const existingIds = new Set(prev.map(item => item.content_item?.id));
                    const uniqueNew = data.results.filter(item => !existingIds.has(item.content_item?.id));
                    return [...prev, ...uniqueNew];
                });

                // Update cursors
                setCursors(prev => {
                    const next = { ...prev };
                    Object.entries(data.platforms).forEach(([key, value]: [string, any]) => {
                        if (value.success) {
                            if (value.next_cursor) {
                                next[key] = value.next_cursor;
                            } else {
                                delete next[key]; // No more results for this platform
                            }
                        }
                    });
                    return next;
                });

            } else {
                // New Search
                setResults(data.results);

                // Set initial cursors
                const next: Record<string, any> = {};
                Object.entries(data.platforms).forEach(([key, value]: [string, any]) => {
                    if (value.success && value.next_cursor) {
                        next[key] = value.next_cursor;
                    }
                });
                setCursors(next);
            }

            // Invalidate history query to show new search
            queryClient.invalidateQueries({ queryKey: ["searchHistory"] });
        }
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
        queryFn: () => fetchWithAuth("http://localhost:8000/v1/searches"),
    });

    // 3. Get Single Search (GET /v1/searches/:id)
    const getSearch = (id: string) => useQuery({
        queryKey: ["search", id],
        queryFn: () => fetchWithAuth(`http://localhost:8000/v1/searches/${id}`),
        enabled: !!id,
    });

    // Track load type
    const [isLoadMoreRequest, setIsLoadMoreRequest] = useState(false);

    return {
        ...store,
        search: () => {
            setIsLoadMoreRequest(false);
            searchMutation.mutate({ isLoadMore: false });
        },
        loadMore: () => {
            setIsLoadMoreRequest(true);
            searchMutation.mutate({ isLoadMore: true });
        },
        isSearching: searchMutation.isPending, // Global loading state
        isInitialLoading: searchMutation.isPending && !isLoadMoreRequest, // For full page skeleton
        isLoadingMore: searchMutation.isPending && isLoadMoreRequest, // For bottom spinner
        searchResults: { results },
        searchError: searchMutation.error,
        history: historyQuery.data?.searches || [],
        isLoadingHistory: historyQuery.isLoading,
        getSearch,
        hasMore,
    };
}

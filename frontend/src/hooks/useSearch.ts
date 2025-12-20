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
    const [controller, setController] = useState<AbortController | null>(null);

    const searchMutation = useMutation({
        mutationFn: async ({ isLoadMore = false }: { isLoadMore?: boolean } = {}) => {
            const body = {
                query: store.query,
                inputs: {} as any
            };

            // Transform store inputs to API format
            const inputs: Record<string, any> = {};
            const platformKeys = Object.keys(store.platformInputs) as Array<keyof typeof store.platformInputs>;
            const activeKeys = platformKeys.filter(k => store.platformInputs[k]);

            let platformsToFetch = activeKeys;

            if (isLoadMore) {
                platformsToFetch = activeKeys.filter(key => {
                    if (key === 'instagram_reels') return false;
                    return !!cursors[key];
                });

                if (platformsToFetch.length === 0) return null;
            }

            platformsToFetch.forEach(key => {
                const cursor = isLoadMore ? cursors[key] : undefined;
                inputs[key] = getParams(key, cursor);
            });

            body.inputs = inputs;

            // Get Token
            const user = auth.currentUser;
            if (!user) throw new Error("User not authenticated");
            const token = await user.getIdToken();

            // Abort previous request if any
            if (controller) controller.abort();
            const newController = new AbortController();
            setController(newController);

            // If new search, clear results immediately
            if (!isLoadMore) {
                setResults([]);
                setCursors({});
            }

            await import("@microsoft/fetch-event-source").then(({ fetchEventSource }) => {
                return fetchEventSource("http://localhost:8000/v1/search", {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(body),
                    signal: newController.signal,
                    onmessage(msg) {
                        try {
                            const data = JSON.parse(msg.data);

                            if (msg.event === "start") {
                                // console.log("Search started:", data);
                            } else if (msg.event === "platform_result") {
                                const result = data;
                                if (result.success && result.items) {
                                    setResults(prev => {
                                        // Deduplicate based on content_item.id
                                        const existingIds = new Set(prev.map(p => p.content_item?.id));
                                        const uniqueNew = result.items.filter((item: any) => !existingIds.has(item.content_item?.id));
                                        return [...prev, ...uniqueNew];
                                    });

                                    // Update Cursor
                                    if (result.next_cursor) {
                                        setCursors(prev => ({ ...prev, [result.platform]: result.next_cursor }));
                                    } else {
                                        setCursors(prev => {
                                            const next = { ...prev };
                                            delete next[result.platform];
                                            return next;
                                        });
                                    }
                                }
                            } else if (msg.event === "done") {
                                // console.log("Search done");
                                queryClient.invalidateQueries({ queryKey: ["searchHistory"] });
                            }
                        } catch (e) {
                            console.error("Error parsing SSE message", e);
                        }
                    },
                    onerror(err) {
                        console.error("SSE Error", err);
                        throw err; // Rethrow to trigger mutation error
                    }
                });
            });
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

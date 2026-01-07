import { useCallback, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { auth } from "@/lib/firebaseClient";
import { fetchEventSource } from "@microsoft/fetch-event-source";

import { BACKEND_URL } from '@/lib/api';

export function useSearchStream(searchId?: string | null) {
    const queryClient = useQueryClient();
    const [search, setSearch] = useState<any>(null);
    const [results, setResults] = useState<any[]>([]);
    const [platformCalls, setPlatformCalls] = useState<any[]>([]);
    const [cursors, setCursors] = useState<Record<string, any>>({});
    const [isLoading, setIsLoading] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchSearchDetails = useCallback(async (token: string, id: string) => {
        try {
            const res = await fetch(`${BACKEND_URL}/v1/searches/${id}`, {
                headers: { "Authorization": `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setSearch(data);
                setPlatformCalls(data.platform_calls || []);
                if (data.results) {
                    setResults(data.results);
                }
                // Extract cursors from platform_calls (skip instagram - no cursor pagination)
                const newCursors: Record<string, any> = {};
                for (const call of (data.platform_calls || [])) {
                    if (call.next_cursor && !call.platform?.toLowerCase().includes('instagram')) {
                        newCursors[call.platform] = call.next_cursor;
                    }
                }
                console.log("[useSearchStream] fetchSearchDetails cursors:", newCursors, "from platform_calls:", data.platform_calls?.length);
                setCursors(prev => {
                    // Merge with existing cursors from SSE
                    const merged = { ...prev, ...newCursors };
                    return Object.keys(merged).length > 0 ? merged : prev;
                });

                if (data?.status === "completed") {
                    queryClient.setQueryData(["search", id], data);
                }
            }
        } catch (err) {
            console.error("Failed to fetch search details", err);
        }
    }, [queryClient]);

    const waitForAuth = () => {
        return new Promise<any>((resolve) => {
            const unsubscribe = auth.onAuthStateChanged((user) => {
                unsubscribe();
                resolve(user);
            });
        });
    };

    const loadSearch = useCallback(async (abortController: AbortController, id: string) => {
        // Check react-query cache first - skip fetch for completed searches we've already loaded
        const cachedSearch = queryClient.getQueryData<any>(["search", id]);
        if (cachedSearch?.status === "completed" && cachedSearch.results) {
            setSearch(cachedSearch);
            setPlatformCalls(cachedSearch.platform_calls || []);
            setResults(cachedSearch.results);
            // Extract cursors from cached platform_calls
            const cachedCursors: Record<string, any> = {};
            for (const call of (cachedSearch.platform_calls || [])) {
                if (call.next_cursor && !call.platform?.toLowerCase().includes('instagram')) {
                    cachedCursors[call.platform] = call.next_cursor;
                }
            }
            setCursors(cachedCursors);
            setIsStreaming(false);
            setIsLoading(false);
            return; // Skip network request!
        }

        // Wait for auth to initialize first
        await waitForAuth();

        const user = auth.currentUser;
        if (!user) {
            setError("User not authenticated");
            setIsLoading(false);
            return;
        }

        const token = await user.getIdToken();

        try {
            const statusRes = await fetch(`${BACKEND_URL}/v1/searches/${id}`, {
                headers: { "Authorization": `Bearer ${token}` },
                signal: abortController.signal,
            });

            if (!statusRes.ok && statusRes.status !== 404) {
                throw new Error("Failed to fetch search");
            }

            const searchData = statusRes.ok ? await statusRes.json() : null;

            if (searchData?.status === "completed") {
                setSearch(searchData);
                setPlatformCalls(searchData.platform_calls || []);
                setResults(searchData.results || []);
                // Extract cursors from platform_calls
                const newCursors: Record<string, any> = {};
                for (const call of (searchData.platform_calls || [])) {
                    if (call.next_cursor && !call.platform?.toLowerCase().includes('instagram')) {
                        newCursors[call.platform] = call.next_cursor;
                    }
                }
                console.log("[useSearchStream] completed search cursors:", newCursors);
                setCursors(newCursors);
                setIsStreaming(false);
                setIsLoading(false);
                queryClient.setQueryData(["search", id], searchData);
                return;
            }

            if (searchData?.status === "failed") {
                setError("Search failed");
                setIsLoading(false);
                return;
            }

            setIsStreaming(true);
            setIsLoading(false);
            if (searchData) {
                setSearch(searchData);
            }

            await fetchEventSource(`${BACKEND_URL}/v1/search/${id}/stream`, {
                headers: { "Authorization": `Bearer ${token}` },
                signal: abortController.signal,
                onmessage(msg) {
                    try {
                        if (!msg.data) return;
                        const data = JSON.parse(msg.data);

                        if (data.type === "platform_result") {
                            if (data.success && data.items) {
                                setResults(prev => {
                                    const existingIds = new Set(prev.map((p: any) => p.content_item?.id));
                                    const uniqueNew = data.items.filter((item: any) => !existingIds.has(item.content_item?.id));
                                    return [...prev, ...uniqueNew];
                                });
                            }
                            // Track cursor for pagination (skip instagram)
                            if (data.next_cursor && !data.platform?.toLowerCase().includes('instagram')) {
                                console.log("[useSearchStream] SSE cursor:", data.platform, data.next_cursor);
                                setCursors(prev => ({ ...prev, [data.platform]: data.next_cursor }));
                            }
                        } else if (data.type === "done") {
                            setIsStreaming(false);
                            fetchSearchDetails(token, id);
                        } else if (data.type === "error") {
                            setError(data.error || "Search failed");
                            setIsStreaming(false);
                        }
                    } catch (err) {
                        console.error("Error parsing SSE message", err);
                    }
                },
                onerror(err) {
                    if (!abortController.signal.aborted) {
                        console.error("SSE Error", err);
                        setIsStreaming(false);
                    }
                },
            });
        } catch (err: any) {
            if (err.name === "AbortError") return;
            console.error("Failed to load search", err);
            setError(err.message || "Failed to load search");
            setIsLoading(false);
        }
    }, [fetchSearchDetails, queryClient]);

    useEffect(() => {
        if (!searchId) {
            setSearch(null);
            setResults([]);
            setPlatformCalls([]);
            setCursors({});
            setIsLoading(false);
            setIsStreaming(false);
            setError(null);
            return;
        }

        const abortController = new AbortController();
        setSearch(null);
        setResults([]);
        setPlatformCalls([]);
        setCursors({});
        setIsLoading(true);
        setIsStreaming(false);
        setError(null);
        loadSearch(abortController, searchId);
        return () => abortController.abort();
    }, [searchId, loadSearch]);

    const hasMore = Object.keys(cursors).length > 0;

    return {
        search,
        results,
        platformCalls,
        cursors,
        hasMore,
        isLoading,
        isStreaming,
        error,
    };
}

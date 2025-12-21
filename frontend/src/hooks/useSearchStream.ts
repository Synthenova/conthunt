import { useCallback, useEffect, useState } from "react";
import { auth } from "@/lib/firebaseClient";
import { fetchEventSource } from "@microsoft/fetch-event-source";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export function useSearchStream(searchId?: string | null) {
    const [search, setSearch] = useState<any>(null);
    const [results, setResults] = useState<any[]>([]);
    const [platformCalls, setPlatformCalls] = useState<any[]>([]);
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
            }
        } catch (err) {
            console.error("Failed to fetch search details", err);
        }
    }, []);

    const loadSearch = useCallback(async (abortController: AbortController, id: string) => {
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
                setIsStreaming(false);
                setIsLoading(false);
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
    }, [fetchSearchDetails]);

    useEffect(() => {
        if (!searchId) {
            setSearch(null);
            setResults([]);
            setPlatformCalls([]);
            setIsLoading(false);
            setIsStreaming(false);
            setError(null);
            return;
        }

        const abortController = new AbortController();
        setSearch(null);
        setResults([]);
        setPlatformCalls([]);
        setIsLoading(true);
        setIsStreaming(false);
        setError(null);
        loadSearch(abortController, searchId);
        return () => abortController.abort();
    }, [searchId, loadSearch]);

    return {
        search,
        results,
        platformCalls,
        isLoading,
        isStreaming,
        error,
    };
}

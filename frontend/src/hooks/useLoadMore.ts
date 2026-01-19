import { useCallback, useState } from "react";
import { auth } from "@/lib/firebaseClient";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { BACKEND_URL } from "@/lib/api";
import { mapClientFiltersToPlatformInputs } from "@/lib/clientFilters";
import type { ClientFilters } from "@/lib/clientFilters";

interface LoadMoreResult {
    items: any[];
    cursors: Record<string, any>;
}

export function useLoadMore(searchId: string | null) {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadMore = useCallback(async (
        onNewResults: (items: any[]) => void,
        onNewCursors: (cursors: Record<string, any>) => void,
        filters?: ClientFilters
    ): Promise<void> => {
        if (!searchId) return;

        const user = auth.currentUser;
        if (!user) {
            setError("User not authenticated");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const token = await user.getIdToken();

            // POST to trigger the load_more worker
            const payload = filters
                ? {
                    inputs: mapClientFiltersToPlatformInputs(filters),
                }
                : null;
            const res = await fetch(`${BACKEND_URL}/v1/search/${searchId}/more`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: payload ? JSON.stringify(payload) : undefined,
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(err.detail || "Failed to load more");
            }

            const newCursors: Record<string, any> = {};

            // Connect to SSE stream
            const abortController = new AbortController();

            await fetchEventSource(`${BACKEND_URL}/v1/search/${searchId}/more/stream`, {
                headers: { "Authorization": `Bearer ${token}` },
                signal: abortController.signal,
                onmessage(msg) {
                    try {
                        if (!msg.data) return;
                        const data = JSON.parse(msg.data);

                        if (data.type === "platform_result") {
                            if (data.success && data.items) {
                                onNewResults(data.items);
                            }
                            // Track new cursor
                            if (data.next_cursor && data.platform !== "instagram_reels") {
                                newCursors[data.platform] = data.next_cursor;
                            }
                        } else if (data.type === "done") {
                            onNewCursors(newCursors);
                            setIsLoading(false);
                        } else if (data.type === "error") {
                            setError(data.error || "Load more failed");
                            setIsLoading(false);
                        }
                    } catch (err) {
                        console.error("Error parsing SSE message", err);
                    }
                },
                onerror(err) {
                    if (!abortController.signal.aborted) {
                        console.error("SSE Error", err);
                        setError("Connection error");
                        setIsLoading(false);
                    }
                },
            });
        } catch (err: any) {
            console.error("Load more failed", err);
            setError(err.message || "Failed to load more");
            setIsLoading(false);
        }
    }, [searchId]);

    return {
        loadMore,
        isLoading,
        error,
    };
}

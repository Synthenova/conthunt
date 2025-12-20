"use client";

import { useEffect, useState, useCallback } from "react";
import { SelectableResultsGrid } from "@/components/search/SelectableResultsGrid";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Calendar, Search, Loader2 } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { useParams } from "next/navigation";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { transformSearchResults, transformToMediaItem } from "@/lib/transformers";
import { auth } from "@/lib/firebaseClient";
import { fetchEventSource } from "@microsoft/fetch-event-source";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function SearchDetailPage() {
    const params = useParams();
    const id = params.id as string;

    const [search, setSearch] = useState<any>(null);
    const [results, setResults] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [platformCalls, setPlatformCalls] = useState<any[]>([]);

    // Fetch search data or stream
    const loadSearch = useCallback(async (abortController: AbortController) => {
        if (!id) return;

        const user = auth.currentUser;
        if (!user) {
            setError("User not authenticated");
            setIsLoading(false);
            return;
        }

        const token = await user.getIdToken();

        try {
            // First check search status from the main endpoint
            const statusRes = await fetch(`${BACKEND_URL}/v1/searches/${id}`, {
                headers: { "Authorization": `Bearer ${token}` },
                signal: abortController.signal,
            });

            if (!statusRes.ok) {
                if (statusRes.status === 404) {
                    // Search might still be initializing, try stream
                } else {
                    throw new Error("Failed to fetch search");
                }
            }

            const searchData = statusRes.ok ? await statusRes.json() : null;

            if (searchData?.status === "completed") {
                // Already completed - use data from DB
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

            // Status is 'running' - stream from Redis
            setIsStreaming(true);
            setIsLoading(false);
            if (searchData) {
                setSearch(searchData);
            }

            // Use fetchEventSource for streaming
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
                            // Fetch full search details from DB
                            fetchSearchDetails(token);
                        } else if (data.type === "error") {
                            setError(data.error || "Search failed");
                            setIsStreaming(false);
                        }
                    } catch (e) {
                        console.error("Error parsing SSE message", e);
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
            if (err.name === 'AbortError') return; // Ignore abort errors
            console.error("Failed to load search", err);
            setError(err.message || "Failed to load search");
            setIsLoading(false);
        }
    }, [id]);

    const fetchSearchDetails = async (token: string) => {
        try {
            const res = await fetch(`${BACKEND_URL}/v1/searches/${id}`, {
                headers: { "Authorization": `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setSearch(data);
                setPlatformCalls(data.platform_calls || []);
                // Update results from DB for consistency (has DB IDs now)
                if (data.results) {
                    setResults(data.results);
                }
            }
        } catch (e) {
            console.error("Failed to fetch search details", e);
        }
    };

    useEffect(() => {
        const abortController = new AbortController();
        loadSearch(abortController);
        return () => abortController.abort();
    }, [loadSearch]);

    // Transform results for grid
    const flattenedResults = transformSearchResults(results);


    if (isLoading) {
        return (
            <div className="container mx-auto max-w-6xl py-12 px-4 space-y-8">
                <Skeleton className="h-12 w-1/3" />
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Skeleton className="h-40 w-full" />
                    <Skeleton className="h-40 w-full" />
                    <Skeleton className="h-40 w-full" />
                    <Skeleton className="h-40 w-full" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto max-w-4xl py-12 px-4 flex flex-col items-center justify-center text-center">
                <h2 className="text-2xl font-bold mb-4">Error: {error}</h2>
                <Button asChild>
                    <Link href="/app/history">Back to History</Link>
                </Button>
            </div>
        );
    }

    return (
        <div className="container mx-auto max-w-7xl py-8 px-4 space-y-8">
            {/* Header */}
            <div className="flex flex-col gap-4">
                <div className="flex items-center gap-2 text-muted-foreground hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    <Link href="/app/history">Back to History</Link>
                </div>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <span className="bg-primary/20 p-2 rounded-lg"><Search className="h-6 w-6 text-primary" /></span>
                            {search?.query || "Searching..."}
                        </h1>
                        <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                            {search?.created_at && (
                                <span className="flex items-center gap-1">
                                    <Calendar className="h-3 w-3" />
                                    {formatDistanceToNow(new Date(search.created_at), { addSuffix: true })}
                                </span>
                            )}
                            {isStreaming && (
                                <Badge variant="secondary" className="flex items-center gap-1">
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                    Searching...
                                </Badge>
                            )}
                            {!isStreaming && search?.status === "completed" && (
                                <Badge variant="default" className="uppercase text-[10px]">
                                    Completed
                                </Badge>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Platform Stats */}
            {platformCalls.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {platformCalls.map((call: any) => (
                        <GlassCard key={call.id} className="p-4 flex flex-col gap-2">
                            <div className="flex justify-between items-center">
                                <span className="font-semibold capitalize text-white">{call.platform.replace('_', ' ')}</span>
                                <Badge variant={call.success ? "default" : "destructive"} className="text-[10px]">
                                    {call.success ? "Success" : "Failed"}
                                </Badge>
                            </div>
                            <div className="flex justify-between text-xs text-muted-foreground mt-2">
                                <span>{(call.duration_ms / 1000).toFixed(2)}s</span>
                                <span>{call.response_meta?.items_count || 0} items</span>
                            </div>
                        </GlassCard>
                    ))}
                </div>
            )}

            {/* Results */}
            <div className="space-y-4">
                <h2 className="text-xl font-semibold border-b border-white/10 pb-2">
                    Results ({flattenedResults.length})
                    {isStreaming && <Loader2 className="inline-block h-4 w-4 animate-spin ml-2" />}
                </h2>
                <SelectableResultsGrid
                    results={flattenedResults}
                    loading={isStreaming && flattenedResults.length === 0}
                    analysisDisabled={isStreaming}
                />
            </div>

            {/* Selection Bar */}
            <SelectionBar />
        </div>
    );
}

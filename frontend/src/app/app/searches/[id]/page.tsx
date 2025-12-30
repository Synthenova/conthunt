"use client";

import { useMemo, useState } from "react";
import { ClientFilteredResults } from "@/components/search/ClientFilteredResults";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Calendar, Search, Loader2 } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { useParams } from "next/navigation";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { FlatMediaItem } from "@/lib/transformers";
import { useSearchStream } from "@/hooks/useSearchStream";

export default function SearchDetailPage() {
    const params = useParams();
    const id = params.id as string;

    const { search, results, platformCalls, isLoading, isStreaming, error } = useSearchStream(id);
    const [flatResults, setFlatResults] = useState<FlatMediaItem[]>([]);
    const [allFlatResults, setAllFlatResults] = useState<FlatMediaItem[]>([]);

    const itemsById = useMemo(() => {
        const map: Record<string, FlatMediaItem> = {};
        for (const item of allFlatResults) {
            if (item?.id) {
                map[item.id] = item;
            }
        }
        return map;
    }, [allFlatResults]);

    const mergedPlatformCalls = useMemo(() => {
        if (!platformCalls || platformCalls.length === 0) return [];

        const merged = new Map<string, any>();

        for (const call of platformCalls) {
            const platform = String(call.platform || "").toLowerCase();
            const key = platform || "unknown";
            const existing = merged.get(key);

            if (!existing) {
                merged.set(key, {
                    ...call,
                    platform: platform || call.platform,
                    response_meta: {
                        ...(call.response_meta || {}),
                        items_count: call.response_meta?.items_count || 0,
                    },
                });
                continue;
            }

            existing.success = existing.success || call.success;
            existing.duration_ms = Math.max(existing.duration_ms || 0, call.duration_ms || 0);
            existing.response_meta = {
                ...(existing.response_meta || {}),
                ...(call.response_meta || {}),
                items_count: (existing.response_meta?.items_count || 0) + (call.response_meta?.items_count || 0),
            };
        }

        return Array.from(merged.values());
    }, [platformCalls]);

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
            {mergedPlatformCalls.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {mergedPlatformCalls.map((call: any) => (
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
                    Results ({flatResults.length})
                    {isStreaming && <Loader2 className="inline-block h-4 w-4 animate-spin ml-2" />}
                </h2>
                <ClientFilteredResults
                    results={results}
                    loading={isStreaming && results.length === 0}
                    analysisDisabled={isStreaming}
                    onFlatResultsChange={setFlatResults}
                    onAllResultsChange={setAllFlatResults}
                />
            </div>

            {/* Selection Bar */}
            <SelectionBar itemsById={itemsById} downloadDisabled={isStreaming} />
        </div>
    );
}

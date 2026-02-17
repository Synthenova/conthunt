"use client";

import { useEffect, useMemo, useRef, useState } from "react";
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
import { useUser } from "@/hooks/useUser";
import {
    trackSearchNoResults,
    trackSearchResultsPageViewed,
    trackUserFirstSearch,
} from "@/lib/telemetry/tracking";

export default function SearchDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const { profile } = useUser();

    const { search, results, platformCalls, isLoading, isStreaming, error } = useSearchStream(id);
    const [flatResults, setFlatResults] = useState<FlatMediaItem[]>([]);
    const [allFlatResults, setAllFlatResults] = useState<FlatMediaItem[]>([]);
    const noResultsTrackedRef = useRef(false);

    const itemsById = useMemo(() => {
        const map: Record<string, FlatMediaItem> = {};
        for (const item of allFlatResults) {
            if (item?.id) {
                map[item.id] = item;
            }
        }
        return map;
    }, [allFlatResults]);

    useEffect(() => {
        noResultsTrackedRef.current = false;
    }, [id]);

    useEffect(() => {
        if (!id) return;
        trackSearchResultsPageViewed(id);
    }, [id]);

    useEffect(() => {
        if (!id || isLoading || isStreaming || error) return;
        if (results.length !== 0) return;
        if (noResultsTrackedRef.current) return;
        trackSearchNoResults(id);
        noResultsTrackedRef.current = true;
    }, [id, isLoading, isStreaming, error, results.length]);

    useEffect(() => {
        if (!profile?.id || !id || isLoading || isStreaming || error) return;
        const firstSearchKey = `ph:first_search:${profile.id}`;
        try {
            if (window.localStorage.getItem(firstSearchKey)) {
                return;
            }
            trackUserFirstSearch(profile.id);
            window.localStorage.setItem(firstSearchKey, "1");
        } catch {
            // Fail open if storage is unavailable.
        }
    }, [profile?.id, id, isLoading, isStreaming, error]);


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
        <div className="container mx-auto max-w-7xl py-8 px-4 space-y-8 relative">
            {/* Deep Space Background Gradients */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[120px]" />
            </div>

            {/* Header */}
            <div className="flex flex-col gap-4">
                <div className="flex items-center gap-2 text-muted-foreground hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    <Link href="/app/history" className="text-sm font-medium">Back to History</Link>
                </div>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <span className="glass p-2.5 rounded-xl block shadow-xl shadow-primary/10"><Search className="h-6 w-6 text-primary" /></span>
                            {search?.query || "Searching..."}
                        </h1>
                        <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                            {search?.created_at && (
                                <span className="flex items-center gap-2 glass px-3 py-1 rounded-full border-white/10">
                                    <Calendar className="h-3.5 w-3.5" />
                                    {formatDistanceToNow(new Date(search.created_at), { addSuffix: true })}
                                </span>
                            )}
                            {isStreaming && (
                                <Badge variant="secondary" className="flex items-center gap-2 glass border-primary/20 text-primary">
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                    Searching...
                                </Badge>
                            )}
                            {!isStreaming && search?.status === "completed" && (
                                <Badge variant="default" className="uppercase text-[10px] glass border-white/20">
                                    Completed
                                </Badge>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Results */}
            <div className="space-y-4">
                {/* <h2 className="text-xl font-semibold border-b border-white/10 pb-2">
                    Results ({flatResults.length})
                    {isStreaming && <Loader2 className="inline-block h-4 w-4 animate-spin ml-2" />}
                </h2> */}
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
